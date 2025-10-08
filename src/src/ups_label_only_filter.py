#!/usr/bin/env python3
"""
UPS Label-Only Tracking Filter
==============================

WORKFLOW: Extract tracking numbers from DLT pipeline and filter for label-only status

This script is part of the data processing workflow:
1. Run dlt_pipeline_examples.py to extract data from ClickHouse
2. Run this script to filter for tracking numbers with ONLY label-created status

Date Range: 85-89 days ago (configurable via environment variables)

Filtering Criteria:
- The tracking number should have only ONE activity record
- That single activity record must have the exact status description:
  "Shipper created a label, UPS has not received the package yet. "
- Exclude any tracking numbers that have additional activity records or different status descriptions

Usage:
    poetry run python src/src/ups_label_only_filter.py

Configuration:
    Set in .env file:
    - DLT_TRANSACTION_START_CUTOFF_DAYS=89 (default: 89 days ago = start)
    - DLT_TRANSACTION_END_CUTOFF_DAYS=85 (default: 85 days ago = end)
    - This creates a 5-day window: 85-89 days ago

Output:
    - CSV: ups_label_only_tracking_range_YYYYMMDD_to_YYYYMMDD_timestamp.csv
    - JSON: ups_label_only_filter_range_YYYYMMDD_to_YYYYMMDD_timestamp.json
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import duckdb
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "carrier_invoice_extraction.duckdb")
TABLE_NAME = "carrier_invoice_extraction.carrier_invoice_data"
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data/output")

# UPS API Configuration - Load from environment variables
UPS_TOKEN_URL = os.getenv("UPS_TOKEN_URL")
UPS_TRACKING_URL = os.getenv("UPS_TRACKING_URL")
UPS_USERNAME = os.getenv("UPS_USERNAME")
UPS_PASSWORD = os.getenv("UPS_PASSWORD")

# Validate required UPS API environment variables
if not UPS_TOKEN_URL:
    raise ValueError("UPS_TOKEN_URL environment variable is required")
if not UPS_TRACKING_URL:
    raise ValueError("UPS_TRACKING_URL environment variable is required")
if not UPS_USERNAME:
    raise ValueError("UPS_USERNAME environment variable is required")
if not UPS_PASSWORD:
    raise ValueError("UPS_PASSWORD environment variable is required")

# Target status description to filter for
TARGET_STATUS_DESCRIPTION = (
    "Shipper created a label, UPS has not received the package yet. "
)
TARGET_STATUS_CODE = "MP"
TARGET_STATUS_TYPE = "M"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def connect_to_duckdb() -> Optional[duckdb.DuckDBPyConnection]:
    """Connect to the DuckDB file and return connection"""
    if not os.path.exists(DUCKDB_PATH):
        logger.error(f"❌ DuckDB file not found: {DUCKDB_PATH}")
        logger.info("💡 Run the pipeline first to create the database")
        return None

    try:
        conn = duckdb.connect(DUCKDB_PATH)
        logger.info(f"✅ Connected to DuckDB: {DUCKDB_PATH}")
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to connect to DuckDB: {e}")
        return None


def extract_tracking_numbers_from_duckdb(limit: int = 0) -> List[Dict[str, str]]:
    """
    Extract unique tracking numbers with account_number from DuckDB database with transaction_date filtering

    Filters for tracking numbers where transaction_date is 85-89 days ago from today,
    matching the same logic used in the DLT pipeline.

    Args:
        limit: Maximum number of tracking numbers to return (0 = no limit, process all)

    Returns:
        List of dictionaries containing tracking_number and account_number
    """
    conn = connect_to_duckdb()
    if not conn:
        return []

    try:
        # Calculate dynamic date range (same logic as DLT pipeline) - 85-89 days ago
        start_cutoff_days = int(os.getenv("DLT_TRANSACTION_START_CUTOFF_DAYS", "89"))
        end_cutoff_days = int(os.getenv("DLT_TRANSACTION_END_CUTOFF_DAYS", "85"))
        start_target_date = (
            datetime.utcnow() - timedelta(days=start_cutoff_days)
        ).date()
        end_target_date = (datetime.utcnow() - timedelta(days=end_cutoff_days)).date()

        logger.info(
            f"🔍 Extracting tracking numbers from {TABLE_NAME} with transaction_date filtering..."
        )
        logger.info(
            f"🎯 Target transaction_date range: {start_target_date} to {end_target_date} ({start_cutoff_days}-{end_cutoff_days} days ago)"
        )

        # Base query with transaction_date filtering - include account_number
        base_where_clause = f"""
            WHERE tracking_number IS NOT NULL
            AND tracking_number != ''
            AND LENGTH(TRIM(tracking_number)) > 0
            AND tracking_number LIKE '1Z%'  -- UPS tracking numbers start with 1Z
            AND transaction_date >= '{start_target_date}'
            AND transaction_date <= '{end_target_date}'
        """

        if limit > 0:
            query = f"""
                SELECT DISTINCT tracking_number, account_number
                FROM {TABLE_NAME}
                {base_where_clause}
                ORDER BY tracking_number
                LIMIT {limit}
            """
        else:
            # No limit - process all tracking numbers
            query = f"""
                SELECT DISTINCT tracking_number, account_number
                FROM {TABLE_NAME}
                {base_where_clause}
                ORDER BY tracking_number
            """

        result = conn.execute(query).fetchall()
        tracking_numbers = [
            {"tracking_number": row[0], "account_number": row[1]} for row in result
        ]

        logger.info(
            f"📊 Found {len(tracking_numbers)} unique UPS tracking numbers in date range"
        )

        if tracking_numbers:
            sample_display = [
                f"{item['tracking_number']} (Account: {item['account_number']})"
                for item in tracking_numbers[:5]
            ]
            logger.info(f"📋 Sample tracking numbers: {sample_display}")
        else:
            logger.warning(
                f"⚠️ No tracking numbers found for transaction_date range {start_target_date} to {end_target_date}"
            )

        return tracking_numbers

    except Exception as e:
        logger.error(f"❌ Failed to extract tracking numbers from DuckDB: {e}")
        return []
    finally:
        if conn:
            conn.close()


def get_ups_access_token() -> Optional[str]:
    """Get UPS API access token"""
    try:
        payload = {"grant_type": "client_credentials"}
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "x-merchant-id": "string",
        }

        response = requests.post(
            UPS_TOKEN_URL,
            data=payload,
            headers=headers,
            auth=(UPS_USERNAME, UPS_PASSWORD),
        )
        response.raise_for_status()

        data = response.json()
        access_token = data["access_token"]
        logger.info("✅ Successfully obtained UPS access token")
        return access_token

    except Exception as e:
        logger.error(f"❌ Failed to get UPS access token: {e}")
        return None


def query_ups_tracking(tracking_number: str, access_token: str) -> Optional[Dict]:
    """
    Query UPS API for tracking information

    Args:
        tracking_number: UPS tracking number
        access_token: UPS API access token

    Returns:
        UPS API response data or None if failed
    """
    try:
        url = UPS_TRACKING_URL + tracking_number
        epoch_time = int(time.time())

        headers = {
            "transId": str(epoch_time),
            "transactionSrc": "label_filter",
            "Authorization": f"Bearer {access_token}",
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        return data

    except requests.RequestException as e:
        logger.warning(f"❌ UPS API request failed for {tracking_number}: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Unexpected error querying {tracking_number}: {e}")
        return None


def check_label_only_status(ups_response: Dict) -> Tuple[bool, str]:
    """
    Check if tracking number has exclusively the label-only status

    Args:
        ups_response: UPS API response data

    Returns:
        Tuple of (is_label_only, reason)
    """
    try:
        # Navigate to the activity array
        shipment = ups_response.get("trackResponse", {}).get("shipment", [])
        if not shipment:
            return False, "No shipment data found"

        package = shipment[0].get("package", [])
        if not package:
            return False, "No package data found"

        activity = package[0].get("activity", [])
        if not activity:
            return False, "No activity data found"

        # Check if there's exactly one activity record
        if len(activity) != 1:
            return False, f"Has {len(activity)} activity records (expected exactly 1)"

        # Check the single activity record
        single_activity = activity[0]
        status = single_activity.get("status", {})

        description = status.get("description", "").strip()
        code = status.get("code", "")
        status_type = status.get("type", "")

        # Check if it matches our target criteria
        if description == TARGET_STATUS_DESCRIPTION.strip():
            if code == TARGET_STATUS_CODE and status_type == TARGET_STATUS_TYPE:
                return True, "Matches label-only criteria exactly"
            else:
                return (
                    False,
                    f"Description matches but code/type differs: {code}/{status_type}",
                )
        else:
            return False, f"Different status description: '{description}'"

    except Exception as e:
        return False, f"Error parsing response: {e}"


def process_tracking_numbers(
    tracking_numbers: List[Dict[str, str]], access_token: str
) -> Dict:
    """
    Process tracking numbers and filter for label-only status

    Args:
        tracking_numbers: List of dictionaries containing tracking_number and account_number
        access_token: UPS API access token

    Returns:
        Dictionary with results and statistics
    """
    results = {
        "label_only_tracking_numbers": [],
        "excluded_tracking_numbers": [],
        "api_errors": [],
        "total_processed": 0,
        "total_label_only": 0,
        "total_excluded": 0,
        "total_errors": 0,
    }

    logger.info(f"🔄 Processing {len(tracking_numbers)} tracking numbers...")

    for i, tracking_item in enumerate(tracking_numbers, 1):
        tracking_number = tracking_item["tracking_number"]
        account_number = tracking_item["account_number"]
        logger.info(
            f"📦 Processing {i}/{len(tracking_numbers)}: {tracking_number} (Account: {account_number})"
        )

        # Query UPS API
        ups_response = query_ups_tracking(tracking_number, access_token)
        results["total_processed"] += 1

        if ups_response is None:
            results["api_errors"].append(
                {
                    "tracking_number": tracking_number,
                    "account_number": account_number,
                    "error": "API request failed",
                }
            )
            results["total_errors"] += 1
            continue

        # Check if it matches label-only criteria
        is_label_only, reason = check_label_only_status(ups_response)

        if is_label_only:
            results["label_only_tracking_numbers"].append(
                {
                    "tracking_number": tracking_number,
                    "account_number": account_number,
                    "reason": reason,
                    "ups_response": ups_response,
                }
            )
            results["total_label_only"] += 1
            logger.info(f"   ✅ MATCH: {reason}")
        else:
            results["excluded_tracking_numbers"].append(
                {
                    "tracking_number": tracking_number,
                    "account_number": account_number,
                    "reason": reason,
                    "ups_response": ups_response,
                }
            )
            results["total_excluded"] += 1
            logger.info(f"   ❌ EXCLUDED: {reason}")

        # Add small delay to avoid rate limiting
        time.sleep(0.5)

    return results


def save_results(results: Dict, timestamp: str) -> Tuple[str, str]:
    """
    Save results to JSON and CSV files with date range in filename

    Args:
        results: Processing results dictionary
        timestamp: Timestamp string for filenames

    Returns:
        Tuple of (json_filepath, csv_filepath)
    """
    # Calculate date range for filename (same logic as DLT pipeline) - 85-89 days ago
    start_cutoff_days = int(os.getenv("DLT_TRANSACTION_START_CUTOFF_DAYS", "89"))
    end_cutoff_days = int(os.getenv("DLT_TRANSACTION_END_CUTOFF_DAYS", "85"))
    start_date = (datetime.utcnow() - timedelta(days=start_cutoff_days)).strftime(
        "%Y%m%d"
    )
    end_date = (datetime.utcnow() - timedelta(days=end_cutoff_days)).strftime("%Y%m%d")

    # Save complete results to JSON
    json_filename = (
        f"ups_label_only_filter_range_{start_date}_to_{end_date}_{timestamp}.json"
    )
    json_filepath = os.path.join(OUTPUT_DIR, json_filename)

    with open(json_filepath, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Save filtered tracking numbers to CSV with status information
    csv_filename = (
        f"ups_label_only_tracking_range_{start_date}_to_{end_date}_{timestamp}.csv"
    )
    csv_filepath = os.path.join(OUTPUT_DIR, csv_filename)

    with open(csv_filepath, "w", encoding="utf-8") as f:
        f.write(
            "tracking_number,account_number,status_description,status_code,status_type,date_processed\n"
        )
        for item in results["label_only_tracking_numbers"]:
            # Extract status information from the UPS response
            try:
                ups_response = item.get("ups_response", {})
                activity = (
                    ups_response.get("trackResponse", {})
                    .get("shipment", [{}])[0]
                    .get("package", [{}])[0]
                    .get("activity", [{}])
                )
                if activity:
                    status = activity[0].get("status", {})
                    status_description = status.get("description", "").strip()
                    status_code = status.get("code", "")
                    status_type = status.get("type", "")
                else:
                    status_description = "Unknown"
                    status_code = "Unknown"
                    status_type = "Unknown"
            except (KeyError, IndexError, AttributeError):
                status_description = "Unknown"
                status_code = "Unknown"
                status_type = "Unknown"

            # Escape commas in status description for CSV
            status_description_escaped = status_description.replace(",", ";")

            f.write(
                f"{item['tracking_number']},{item['account_number']},{status_description_escaped},{status_code},{status_type},{timestamp}\n"
            )

    return json_filepath, csv_filepath


def print_summary(results: Dict):
    """Print summary of processing results"""
    logger.info("\n" + "=" * 60)
    logger.info("🎯 UPS LABEL-ONLY FILTER SUMMARY")
    logger.info("=" * 60)
    logger.info(f"📊 Total Processed: {results['total_processed']}")
    logger.info(f"✅ Label-Only Found: {results['total_label_only']}")
    logger.info(f"❌ Excluded: {results['total_excluded']}")
    logger.info(f"🚫 API Errors: {results['total_errors']}")

    if results["total_processed"] > 0:
        success_rate = (results["total_label_only"] / results["total_processed"]) * 100
        logger.info(f"📈 Label-Only Rate: {success_rate:.1f}%")

    if results["label_only_tracking_numbers"]:
        logger.info("\n🎯 LABEL-ONLY TRACKING NUMBERS:")
        for item in results["label_only_tracking_numbers"]:
            logger.info(
                f"   📦 {item['tracking_number']} (Account: {item['account_number']})"
            )

    if results["api_errors"]:
        logger.info("\n🚫 API ERRORS:")
        for error in results["api_errors"]:
            logger.info(f"   ❌ {error['tracking_number']}: {error['error']}")


def main():
    """Main function to run the label-only filter"""
    logger.info("🚀 Starting UPS Label-Only Tracking Filter")
    logger.info("=" * 60)

    # Show the exact target date range being used (same as DLT pipeline) - 85-89 days ago
    start_cutoff_days = int(os.getenv("DLT_TRANSACTION_START_CUTOFF_DAYS", "89"))
    end_cutoff_days = int(os.getenv("DLT_TRANSACTION_END_CUTOFF_DAYS", "85"))
    start_target_date = (datetime.utcnow() - timedelta(days=start_cutoff_days)).date()
    end_target_date = (datetime.utcnow() - timedelta(days=end_cutoff_days)).date()
    logger.info(
        f"🎯 Target transaction_date range: {start_target_date} to {end_target_date} ({start_cutoff_days}-{end_cutoff_days} days ago)"
    )

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Extract tracking numbers from DuckDB
    logger.info("📊 Step 1: Extracting tracking numbers from DuckDB...")
    tracking_numbers = extract_tracking_numbers_from_duckdb(
        limit=0
    )  # Process ALL tracking numbers in the date range (limit=0 means no limit)

    if not tracking_numbers:
        logger.error("❌ No tracking numbers found. Exiting.")
        return

    # Get UPS access token
    logger.info("🔑 Step 2: Getting UPS API access token...")
    access_token = get_ups_access_token()

    if not access_token:
        logger.error("❌ Failed to get UPS access token. Exiting.")
        return

    # Process tracking numbers
    logger.info("🔄 Step 3: Processing tracking numbers...")
    results = process_tracking_numbers(tracking_numbers, access_token)

    # Save results
    logger.info("💾 Step 4: Saving results...")
    json_filepath, csv_filepath = save_results(results, timestamp)

    # Print summary
    print_summary(results)

    logger.info(f"\n📁 Results saved to:")
    logger.info(f"   JSON: {json_filepath}")
    logger.info(f"   CSV:  {csv_filepath}")
    logger.info("\n✅ UPS Label-Only Filter completed successfully!")


if __name__ == "__main__":
    main()
