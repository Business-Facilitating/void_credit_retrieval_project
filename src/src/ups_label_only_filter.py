#!/usr/bin/env python3
"""
UPS Label-Only Tracking Filter
==============================

WORKFLOW: Extract tracking numbers from DLT pipeline and filter for label-only status

This script is part of the data processing workflow:
1. Run dlt_pipeline_examples.py to extract data from ClickHouse
2. Run this script to filter for tracking numbers with ONLY label-created status

Date Range: 88-89 days ago (configurable via environment variables)

Filtering Criteria:
- The tracking number should have only ONE activity record
- That single activity record must have the exact status description:
  "Shipper created a label, UPS has not received the package yet. "
- Exclude any tracking numbers that have additional activity records or different status descriptions

Usage:
    poetry run python src/src/ups_label_only_filter.py

Configuration:
    Set in .env file:
    - UPS_FILTER_START_DAYS=89 (default: 89 days ago)
    - UPS_FILTER_END_DAYS=88 (default: 88 days ago)
    - This creates a 2-day window: 88-89 days ago

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

    Filters for tracking numbers where transaction_date is 88-89 days ago from today,
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
        # Calculate dynamic date range (same logic as DLT pipeline) - 88-89 days ago
        start_cutoff_days = int(os.getenv("UPS_FILTER_START_DAYS", "89"))
        end_cutoff_days = int(os.getenv("UPS_FILTER_END_DAYS", "88"))
        start_target_date = (
            datetime.utcnow() - timedelta(days=start_cutoff_days)
        ).date()
        end_target_date = (datetime.utcnow() - timedelta(days=end_cutoff_days)).date()

        logger.info(
            f"🔍 Extracting tracking numbers from {TABLE_NAME} with transaction_date filtering..."
        )
        # Show date range - if start and end are the same, show "exactly X days ago"
        if start_cutoff_days == end_cutoff_days:
            logger.info(
                f"🎯 Target transaction_date: {start_target_date} (exactly {start_cutoff_days} days ago)"
            )
        else:
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


def get_ups_access_token(retry_count: int = 3) -> Optional[Tuple[str, datetime]]:
    """
    Get UPS API access token with retry logic

    Args:
        retry_count: Number of retry attempts if token request fails

    Returns:
        Tuple of (access_token, token_timestamp) or None if failed
    """
    for attempt in range(1, retry_count + 1):
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
            token_timestamp = datetime.now()

            logger.info(
                f"✅ Successfully obtained UPS access token at {token_timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            return access_token, token_timestamp

        except Exception as e:
            logger.error(
                f"❌ Failed to get UPS access token (attempt {attempt}/{retry_count}): {e}"
            )
            if attempt < retry_count:
                wait_time = 5 * attempt  # Exponential backoff: 5s, 10s, 15s
                logger.info(f"⏳ Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"❌ All {retry_count} token request attempts failed")
                return None

    return None


def is_token_expired(token_timestamp: datetime, expiry_minutes: int = 55) -> bool:
    """
    Check if the access token is expired or about to expire

    Args:
        token_timestamp: Timestamp when the token was obtained
        expiry_minutes: Minutes before considering token expired (default: 55 minutes,
                       to refresh before the 60-minute expiration)

    Returns:
        True if token should be refreshed, False otherwise
    """
    if token_timestamp is None:
        return True

    elapsed_time = datetime.now() - token_timestamp
    elapsed_minutes = elapsed_time.total_seconds() / 60

    return elapsed_minutes >= expiry_minutes


def refresh_token_if_needed(
    current_token: str, token_timestamp: datetime, expiry_minutes: int = 55
) -> Tuple[str, datetime]:
    """
    Refresh the UPS API access token if it's expired or about to expire

    Args:
        current_token: Current access token
        token_timestamp: Timestamp when current token was obtained
        expiry_minutes: Minutes before considering token expired (default: 55)

    Returns:
        Tuple of (access_token, token_timestamp) - either refreshed or current
    """
    if is_token_expired(token_timestamp, expiry_minutes):
        elapsed_time = datetime.now() - token_timestamp
        elapsed_minutes = elapsed_time.total_seconds() / 60

        logger.info(
            f"🔄 Token has been active for {elapsed_minutes:.1f} minutes - refreshing..."
        )

        result = get_ups_access_token()
        if result:
            new_token, new_timestamp = result
            logger.info("✅ Token successfully refreshed")
            return new_token, new_timestamp
        else:
            logger.warning("⚠️ Token refresh failed - continuing with current token")
            return current_token, token_timestamp

    return current_token, token_timestamp


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
    tracking_numbers: List[Dict[str, str]], access_token: str, token_timestamp: datetime
) -> Dict:
    """
    Process tracking numbers and filter for label-only status with automatic token refresh

    Args:
        tracking_numbers: List of dictionaries containing tracking_number and account_number
        access_token: UPS API access token
        token_timestamp: Timestamp when the token was obtained

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
        "token_refreshes": 0,
    }

    logger.info(f"🔄 Processing {len(tracking_numbers)} tracking numbers...")

    # Track current token and timestamp
    current_token = access_token
    current_token_timestamp = token_timestamp

    for i, tracking_item in enumerate(tracking_numbers, 1):
        tracking_number = tracking_item["tracking_number"]
        account_number = tracking_item["account_number"]

        # Start timing for this tracking number
        tracking_start_time = time.time()

        logger.info(
            f"📦 Processing {i}/{len(tracking_numbers)}: {tracking_number} (Account: {account_number})"
        )

        # Check and refresh token if needed before each API call
        current_token, current_token_timestamp = refresh_token_if_needed(
            current_token, current_token_timestamp
        )

        # Track if token was refreshed
        if current_token != access_token or current_token_timestamp != token_timestamp:
            results["token_refreshes"] += 1

        # Query UPS API with current (possibly refreshed) token
        ups_response = query_ups_tracking(tracking_number, current_token)
        results["total_processed"] += 1

        # Calculate elapsed time for this tracking number
        tracking_elapsed = time.time() - tracking_start_time

        if ups_response is None:
            results["api_errors"].append(
                {
                    "tracking_number": tracking_number,
                    "account_number": account_number,
                    "error": "API request failed",
                    "processing_time_seconds": tracking_elapsed,
                }
            )
            results["total_errors"] += 1
            logger.info(f"   ⏱️  Processing time: {tracking_elapsed:.2f} seconds")
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
                    "processing_time_seconds": tracking_elapsed,
                }
            )
            results["total_label_only"] += 1
            logger.info(f"   ✅ MATCH: {reason}")
            logger.info(f"   ⏱️  Processing time: {tracking_elapsed:.2f} seconds")
        else:
            results["excluded_tracking_numbers"].append(
                {
                    "tracking_number": tracking_number,
                    "account_number": account_number,
                    "reason": reason,
                    "ups_response": ups_response,
                    "processing_time_seconds": tracking_elapsed,
                }
            )
            results["total_excluded"] += 1
            logger.info(f"   ❌ EXCLUDED: {reason}")
            logger.info(f"   ⏱️  Processing time: {tracking_elapsed:.2f} seconds")

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
    # Calculate date range for filename (same logic as DLT pipeline) - exactly 89 days ago
    start_cutoff_days = int(os.getenv("UPS_FILTER_START_DAYS", "89"))
    end_cutoff_days = int(os.getenv("UPS_FILTER_END_DAYS", "88"))
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
    logger.info(f"🔄 Token Refreshes: {results.get('token_refreshes', 0)}")

    if results["total_processed"] > 0:
        success_rate = (results["total_label_only"] / results["total_processed"]) * 100
        logger.info(f"📈 Label-Only Rate: {success_rate:.1f}%")

    # Calculate and display average processing time
    all_processing_times = []

    # Collect processing times from all tracking numbers
    for item in results["label_only_tracking_numbers"]:
        if "processing_time_seconds" in item:
            all_processing_times.append(item["processing_time_seconds"])

    for item in results["excluded_tracking_numbers"]:
        if "processing_time_seconds" in item:
            all_processing_times.append(item["processing_time_seconds"])

    for error in results["api_errors"]:
        if "processing_time_seconds" in error:
            all_processing_times.append(error["processing_time_seconds"])

    if all_processing_times:
        avg_time = sum(all_processing_times) / len(all_processing_times)
        min_time = min(all_processing_times)
        max_time = max(all_processing_times)
        logger.info("\n⏱️  PROCESSING TIME STATISTICS:")
        logger.info(f"   Average: {avg_time:.2f} seconds per tracking number")
        logger.info(f"   Minimum: {min_time:.2f} seconds")
        logger.info(f"   Maximum: {max_time:.2f} seconds")
        logger.info(f"   Total samples: {len(all_processing_times)}")

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
    """Main function to run the label-only filter with automatic token refresh"""
    logger.info("🚀 Starting UPS Label-Only Tracking Filter")
    logger.info("=" * 60)

    # Show the exact target date range being used (same as DLT pipeline) - 88-89 days ago
    start_cutoff_days = int(os.getenv("UPS_FILTER_START_DAYS", "89"))
    end_cutoff_days = int(os.getenv("UPS_FILTER_END_DAYS", "88"))
    start_target_date = (datetime.utcnow() - timedelta(days=start_cutoff_days)).date()
    end_target_date = (datetime.utcnow() - timedelta(days=end_cutoff_days)).date()

    # Show date range - if start and end are the same, show "exactly X days ago"
    if start_cutoff_days == end_cutoff_days:
        logger.info(
            f"🎯 Target transaction_date: {start_target_date} (exactly {start_cutoff_days} days ago)"
        )
    else:
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
        logger.warning("⚠️ No tracking numbers found for the specified date range.")
        logger.info(
            f"ℹ️  This is expected if ClickHouse doesn't have data for {start_target_date} to {end_target_date} yet."
        )
        logger.info(
            "ℹ️  The pipeline will automatically find tracking numbers when data becomes available."
        )
        logger.info("✅ Exiting gracefully - no action needed.")
        return

    # Get UPS access token with timestamp
    logger.info("🔑 Step 2: Getting UPS API access token...")
    token_result = get_ups_access_token()

    if not token_result:
        logger.error("❌ Failed to get UPS access token. Exiting.")
        return

    access_token, token_timestamp = token_result
    logger.info(f"🔑 Token will auto-refresh every 55 minutes to prevent expiration")

    # Process tracking numbers with automatic token refresh
    logger.info("🔄 Step 3: Processing tracking numbers...")
    results = process_tracking_numbers(tracking_numbers, access_token, token_timestamp)

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
