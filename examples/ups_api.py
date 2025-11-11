#!/usr/bin/env python3
"""
UPS Tracking API Integration
============================

WORKFLOW STEP 2 of 2: Query UPS API for tracking numbers

This script is part of a 2-step workflow:
1. Run dlt_pipeline_examples.py to extract tracking numbers from ClickHouse
   - Filters by transaction_date: 85-89 days ago
   - Creates DuckDB file: carrier_invoice_tracking_range_*.duckdb

2. Run this script (ups_api.py) to query UPS Tracking API
   - Reads tracking numbers from the most recent DuckDB file
   - Queries UPS API for current status of each tracking number
   - Saves results to JSON files in data/output/

Example:
    # Step 1: Extract data (85-89 days ago)
    poetry run python src/src/dlt_pipeline_examples.py

    # Step 2: Query UPS API
    poetry run python src/src/ups_api.py

Output:
    - Individual: data/output/ups_tracking_{TRACKING_NUMBER}_{timestamp}.json
    - Batch: data/output/ups_tracking_batch_{timestamp}.json

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import glob
import json
import os
import pprint
import time
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get UPS API configuration from environment variables
UPS_TOKEN_URL = os.getenv("UPS_TOKEN_URL")
UPS_TRACKING_URL = os.getenv("UPS_TRACKING_URL")
UPS_USERNAME = os.getenv("UPS_USERNAME")
UPS_PASSWORD = os.getenv("UPS_PASSWORD")

# Validate required environment variables
if not UPS_TOKEN_URL:
    raise ValueError("UPS_TOKEN_URL environment variable is required")
if not UPS_TRACKING_URL:
    raise ValueError("UPS_TRACKING_URL environment variable is required")
if not UPS_USERNAME:
    raise ValueError("UPS_USERNAME environment variable is required")
if not UPS_PASSWORD:
    raise ValueError("UPS_PASSWORD environment variable is required")


def get_tracking_numbers_from_duckdb():
    """
    Extract tracking numbers from the most recent DuckDB file created by dlt_pipeline_examples.py

    Returns:
        List of unique tracking numbers from the date-filtered dataset
    """
    try:
        import duckdb
    except ImportError:
        print("❌ duckdb library not available. Install with: poetry add duckdb")
        return []

    # Find the most recent DuckDB file in data/output
    output_dir = "data/output"
    duckdb_pattern = os.path.join(output_dir, "carrier_invoice_tracking_range_*.duckdb")
    duckdb_files = glob.glob(duckdb_pattern)

    if not duckdb_files:
        print(f"❌ No DuckDB files found matching pattern: {duckdb_pattern}")
        print("💡 Run dlt_pipeline_examples.py first to extract data from ClickHouse")
        return []

    # Get the most recent file
    latest_duckdb = max(duckdb_files, key=os.path.getmtime)
    print(f"📂 Using DuckDB file: {latest_duckdb}")

    try:
        # Connect to DuckDB and extract tracking numbers
        conn = duckdb.connect(latest_duckdb, read_only=True)

        # Query to get unique tracking numbers
        query = """
            SELECT DISTINCT tracking_number
            FROM carrier_invoice_data
            WHERE tracking_number IS NOT NULL
            AND tracking_number != ''
            AND LENGTH(TRIM(tracking_number)) > 0
            ORDER BY tracking_number
        """

        result = conn.execute(query).fetchall()
        conn.close()

        # Extract tracking numbers from result tuples
        tracking_numbers = [row[0] for row in result if row[0]]

        print(f"✅ Extracted {len(tracking_numbers)} tracking numbers from DuckDB")

        # Show date range info from filename
        filename = os.path.basename(latest_duckdb)
        print(f"📅 Source file: {filename}")

        return tracking_numbers

    except Exception as e:
        print(f"❌ Failed to extract tracking numbers from DuckDB: {e}")
        import traceback

        traceback.print_exc()
        return []


url = UPS_TOKEN_URL

username = UPS_USERNAME
password = UPS_PASSWORD

payload = {"grant_type": "client_credentials"}

headers = {
    "Content-Type": "application/x-www-form-urlencoded",
    "x-merchant-id": "string",
}

print("Making OAuth request to UPS API...")
print(f"URL: {url}")
print(f"Username: {username[:10]}...")

try:
    response = requests.post(
        url, data=payload, headers=headers, auth=(username, password), timeout=10
    )
    print(f"OAuth response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        access_token = data["access_token"]
        print(f"Access token obtained: {access_token[:20]}...")
    else:
        print(f"OAuth failed with status {response.status_code}")
        print(f"Response: {response.text}")
        exit(1)

except requests.exceptions.RequestException as e:
    print(f"OAuth request failed: {e}")
    exit(1)

# Create output directory if it doesn't exist
output_dir = "data/output"
os.makedirs(output_dir, exist_ok=True)

# Generate timestamp for the batch
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

epoch_time = int(time.time())

# Get tracking numbers from the most recent DuckDB file
print("\n📦 Loading tracking numbers from DuckDB...")
tracking_nums = get_tracking_numbers_from_duckdb()

if not tracking_nums:
    print("⚠️ No tracking numbers found. Exiting.")
    exit(0)

print(f"📊 Total tracking numbers to process: {len(tracking_nums)}")

# Show sample tracking numbers
sample_count = min(5, len(tracking_nums))
print(f"📋 Sample tracking numbers: {tracking_nums[:sample_count]}")
print()

# Store all responses
all_responses = []

for i, inquiry_number in enumerate(tracking_nums, 1):
    print(f"Processing tracking number {i}/{len(tracking_nums)}: {inquiry_number}")

    url = UPS_TRACKING_URL + inquiry_number
    epoch_time = int(time.time())

    headers = {
        "transId": str(epoch_time),
        "transactionSrc": "testing",
        "Authorization": f"Bearer {access_token}",
    }

    print(f"  Making tracking request to: {url}")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"  Tracking response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
        else:
            print(f"  Tracking request failed with status {response.status_code}")
            print(f"  Response: {response.text}")
            data = {"error": f"HTTP {response.status_code}", "response": response.text}

    except requests.exceptions.RequestException as e:
        print(f"  Tracking request failed: {e}")
        data = {"error": str(e)}

    # Add metadata to the response
    response_with_metadata = {
        "tracking_number": inquiry_number,
        "request_timestamp": datetime.now().isoformat(),
        "response_status_code": response.status_code,
        "ups_response": data,
    }

    # Store in collection
    all_responses.append(response_with_metadata)

    # Save individual response
    individual_filename = f"ups_tracking_{inquiry_number}_{timestamp}.json"
    individual_filepath = os.path.join(output_dir, individual_filename)

    with open(individual_filepath, "w", encoding="utf-8") as f:
        json.dump(response_with_metadata, f, indent=2, ensure_ascii=False)

    # Print status summary
    if response.status_code == 200 and "trackResponse" in data:
        try:
            status = data["trackResponse"]["shipment"][0]["package"][0]["currentStatus"]
            print(f"  Status: {status['description']} (code: {status['code']})")
        except (KeyError, IndexError):
            print("  Status: Unable to parse status from response")
    else:
        print(f"  Error: HTTP {response.status_code}")

    print(f"  Saved to: {individual_filepath}")
    print()

# Save combined responses
combined_filename = f"ups_tracking_batch_{timestamp}.json"
combined_filepath = os.path.join(output_dir, combined_filename)

combined_data = {
    "batch_timestamp": datetime.now().isoformat(),
    "total_tracking_numbers": len(tracking_nums),
    "responses": all_responses,
}

with open(combined_filepath, "w", encoding="utf-8") as f:
    json.dump(combined_data, f, indent=2, ensure_ascii=False)

print(f"All responses saved to: {combined_filepath}")
print(f"Individual files saved to: {output_dir}")
print(f"Total tracking numbers processed: {len(tracking_nums)}")
