#!/usr/bin/env python3
"""
17Track API Demo Module
=======================

Demo version of 17Track API integration that accepts manually provided tracking numbers
instead of extracting from DuckDB. Perfect for presentations and demonstrations.

Features:
- Manual tracking number input
- Complete 17Track API workflow (register → wait → retrieve)
- 5-minute processing wait as per 17Track documentation
- Batch processing with progress tracking
- Export to JSON and CSV formats
- No database dependencies

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests

# 17Track API Configuration
API_URL = "https://api.17track.net/track/v2.4/gettrackinfo"
REGISTER_API_URL = "https://api.17track.net/track/v2.2/register"
API_TOKEN = "3ED9315FC1B2FC06CB396E95FE72AB66"
DEFAULT_CARRIER_CODE = 100002  # UPS carrier code
BATCH_SIZE = 40  # Maximum tracking numbers per API call
API_DELAY = 1.0  # Delay between API calls in seconds

# Ensure output directory exists
OUTPUT_DIR = "data/output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TrackingClient:
    """
    17Track API client for package tracking
    """

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize 17Track client

        Args:
            api_token: 17Track API token. If None, will use default token
        """
        self.api_token = api_token or API_TOKEN
        self.api_url = API_URL

        # Headers based on 17Track documentation
        self.headers = {
            "content-type": "application/json",
            "17token": self.api_token,
        }

        logger.info("✅ 17Track client initialized successfully")

    def register_tracking_numbers(
        self, tracking_numbers: List[str], carrier_code: int = DEFAULT_CARRIER_CODE
    ) -> Optional[Dict[str, Any]]:
        """
        Register tracking numbers with 17Track API before retrieving tracking info

        Args:
            tracking_numbers: List of tracking numbers to register
            carrier_code: Carrier code (e.g., 100002 for UPS)

        Returns:
            API response dictionary if successful, None otherwise
        """
        try:
            # Prepare payload for registration API
            payload = [
                {"number": number, "carrier": carrier_code}
                for number in tracking_numbers
            ]

            logger.info(
                f"📝 Registering {len(tracking_numbers)} tracking numbers with 17Track API"
            )

            # Make registration API request
            response = requests.request(
                "POST", REGISTER_API_URL, json=payload, headers=self.headers
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"✅ Registration successful")
            return result

        except requests.RequestException as e:
            logger.error(f"❌ 17Track registration API error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected registration error: {e}")
            return None

    def get_tracking_info(
        self, tracking_numbers: List[str], carrier_code: int = DEFAULT_CARRIER_CODE
    ) -> Optional[Dict[str, Any]]:
        """
        Get tracking information for tracking numbers using 17Track API

        Args:
            tracking_numbers: List of tracking numbers to query
            carrier_code: Carrier code (e.g., 100002 for UPS)

        Returns:
            API response dictionary if successful, None otherwise
        """
        try:
            # Prepare payload for 17Track API
            payload = [
                {"number": number, "carrier": carrier_code}
                for number in tracking_numbers
            ]

            logger.info(
                f"🔍 Getting tracking info for {len(tracking_numbers)} tracking numbers"
            )

            # Make API request using the exact pattern from documentation
            response = requests.request(
                "POST", self.api_url, json=payload, headers=self.headers
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"✅ Tracking query successful")
            return result

        except requests.RequestException as e:
            logger.error(f"❌ 17Track API request error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error: {e}")
            return None

    def get_tracking_results_batch(
        self, tracking_numbers: List[str], carrier_code: int = DEFAULT_CARRIER_CODE
    ) -> Optional[Dict[str, Any]]:
        """
        Alias for get_tracking_info for backward compatibility
        """
        return self.get_tracking_info(tracking_numbers, carrier_code)


def load_tracking_numbers_from_json(json_file_path: str) -> List[str]:
    """
    Load tracking numbers from existing JSON summary files

    Args:
        json_file_path: Path to the tracking summary JSON file

    Returns:
        List of unique tracking numbers
    """
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        tracking_numbers = []

        # Handle different JSON structures
        if isinstance(data, list):
            # List of tracking results
            for item in data:
                if isinstance(item, dict) and "tracking_numbers" in item:
                    tracking_numbers.extend(item["tracking_numbers"])
                elif isinstance(item, str):
                    tracking_numbers.append(item)
        elif isinstance(data, dict):
            # Single tracking result
            if "tracking_numbers" in data:
                tracking_numbers.extend(data["tracking_numbers"])

        # Remove duplicates and empty strings
        unique_numbers = list(
            set([num.strip() for num in tracking_numbers if num.strip()])
        )

        logger.info(
            f"📋 Loaded {len(unique_numbers)} unique tracking numbers from {json_file_path}"
        )
        return unique_numbers

    except Exception as e:
        logger.error(f"❌ Error loading tracking numbers from {json_file_path}: {e}")
        return []


def process_tracking_numbers_in_batches(
    tracking_numbers: List[str],
    client: TrackingClient,
    carrier_code: int = DEFAULT_CARRIER_CODE,
    batch_size: int = BATCH_SIZE,
) -> Tuple[List[Dict[str, Any]], int, int]:
    """
    Process tracking numbers in batches with 17Track registration workflow

    This function follows the correct 17Track API workflow:
    1. Register tracking numbers with 17Track API
    2. Wait 5 minutes for processing (as per 17Track documentation)
    3. Retrieve tracking information for registered numbers

    Args:
        tracking_numbers: List of tracking numbers to process
        client: 17Track client instance
        carrier_code: Carrier code to use
        batch_size: Number of tracking numbers per batch (max 40)

    Returns:
        Tuple of (results_list, successful_batches, failed_batches)

    Note:
        Each batch will take approximately 5+ minutes due to the required
        processing wait time between registration and retrieval steps.
    """
    results = []
    successful_batches = 0
    failed_batches = 0

    # Split into batches
    total_batches = (len(tracking_numbers) + batch_size - 1) // batch_size

    logger.info(
        f"🔄 Processing {len(tracking_numbers)} tracking numbers in {total_batches} batches"
    )

    for i in range(0, len(tracking_numbers), batch_size):
        batch_num = (i // batch_size) + 1
        batch = tracking_numbers[i : i + batch_size]

        logger.info(
            f"📦 Processing batch {batch_num}/{total_batches} ({len(batch)} items)"
        )

        # Step 1: Register tracking numbers first
        logger.info(f"📝 Step 1: Registering batch {batch_num} tracking numbers")
        registration_result = client.register_tracking_numbers(batch, carrier_code)

        if not registration_result:
            failed_batches += 1
            logger.error(f"❌ Batch {batch_num} registration failed")
            continue

        # Wait 5 minutes for 17Track to process the registered tracking numbers
        wait_time = 300  # 5 minutes in seconds
        wait_minutes = wait_time / 60
        logger.info(
            f"⏳ Waiting {wait_minutes:.1f} minutes for 17Track to process registered tracking numbers..."
        )

        # Show progress during wait
        remaining_time = wait_time
        while remaining_time > 0:
            if remaining_time >= 60:
                mins = int(remaining_time // 60)
                secs = int(remaining_time % 60)
                logger.info(f"⏰ {mins}m {secs}s remaining for processing...")
                time.sleep(60)  # Wait 1 minute
                remaining_time -= 60
            else:
                logger.info(f"⏰ {int(remaining_time)}s remaining...")
                time.sleep(remaining_time)
                remaining_time = 0

        # Step 2: Get tracking results for this batch
        logger.info(f"📊 Step 2: Retrieving tracking info for batch {batch_num}")
        result = client.get_tracking_results_batch(batch, carrier_code)

        if result:
            results.append(
                {
                    "batch_number": batch_num,
                    "batch_size": len(batch),
                    "tracking_numbers": batch,
                    "registration_result": registration_result,
                    "tracking_result": result,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            successful_batches += 1
            logger.info(
                f"✅ Batch {batch_num} completed successfully (registered + retrieved)"
            )
        else:
            failed_batches += 1
            logger.error(f"❌ Batch {batch_num} tracking retrieval failed")

        # Rate limiting delay between batches
        if i + batch_size < len(tracking_numbers):  # Don't delay after last batch
            time.sleep(API_DELAY)

    return results, successful_batches, failed_batches


def generate_date_range_iso(days_back: int = 7) -> Tuple[str, str]:
    """
    Generate ISO format date range for the last N days

    Args:
        days_back: Number of days to go back from today

    Returns:
        Tuple of (start_date_iso, end_date_iso)
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def monitor_tracking_status_changes(
    client: TrackingClient,
    tracking_numbers: List[str],
    carrier_code: int = DEFAULT_CARRIER_CODE,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Monitor tracking status changes and generate summary statistics

    Args:
        client: 17Track client instance
        tracking_numbers: List of tracking numbers to monitor
        carrier_code: Carrier code to use

    Returns:
        Tuple of (detailed_results, status_summary)
    """
    logger.info(f"📊 Monitoring status for {len(tracking_numbers)} tracking numbers")

    # Process tracking numbers
    results, successful, failed = process_tracking_numbers_in_batches(
        tracking_numbers, client, carrier_code
    )

    # Generate status summary
    status_summary = {
        "total_tracked": len(tracking_numbers),
        "successful_queries": successful,
        "failed_queries": failed,
        "status_counts": {},
        "delivery_status_breakdown": {},
        "timestamp": datetime.now().isoformat(),
    }

    # Analyze results for status breakdown
    for batch_result in results:
        tracking_result = batch_result.get("tracking_result") or batch_result.get(
            "result", {}
        )
        api_data = tracking_result.get("data", {})
        accepted_items = api_data.get("accepted", [])

        for item in accepted_items:
            track_info = item.get("track_info", {})
            latest_status = track_info.get("latest_status", {})
            delivery_status = latest_status.get("status", "unknown")

            # Count delivery statuses
            status_summary["status_counts"][delivery_status] = (
                status_summary["status_counts"].get(delivery_status, 0) + 1
            )

            # Detailed breakdown using 17Track fields
            substatus = latest_status.get("sub_status", "unknown")
            status_key = f"{delivery_status}_{substatus}"
            status_summary["delivery_status_breakdown"][status_key] = (
                status_summary["delivery_status_breakdown"].get(status_key, 0) + 1
            )

    logger.info(f"📈 Status monitoring complete: {status_summary['status_counts']}")
    return results, status_summary


def export_raw_json_results(
    results: List[Dict[str, Any]], output_filename: Optional[str] = None
) -> str:
    """
    Export raw tracking results to JSON file

    Args:
        results: List of tracking result dictionaries
        output_filename: Optional custom filename

    Returns:
        Path to the exported JSON file
    """
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"tracking_raw_results_{timestamp}.json"

    json_path = os.path.join(OUTPUT_DIR, output_filename)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"📄 Exported raw JSON results to {json_path}")
    return json_path


def export_tracking_results_to_csv(
    results: List[Dict[str, Any]], output_filename: Optional[str] = None
) -> str:
    """
    Export tracking results to CSV file

    Args:
        results: List of tracking result dictionaries
        output_filename: Optional custom filename

    Returns:
        Path to the exported CSV file
    """
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"tracking_results_{timestamp}.csv"

    csv_path = os.path.join(OUTPUT_DIR, output_filename)

    # Flatten the results for CSV export (17Track API format)
    flattened_data = []

    for batch_result in results:
        batch_num = batch_result["batch_number"]
        # Handle new data structure with registration and tracking results
        tracking_result = batch_result.get("tracking_result") or batch_result.get(
            "result", {}
        )

        # Handle case where tracking_result might be None
        if tracking_result is None:
            logger.warning(
                f"⚠️ No tracking result for batch {batch_num}, skipping CSV export for this batch"
            )
            continue

        api_data = tracking_result.get("data", {})
        accepted_items = api_data.get("accepted", [])

        for item in accepted_items:
            # Skip if item is None or not a dictionary
            if not item or not isinstance(item, dict):
                logger.warning(f"⚠️ Invalid item in batch {batch_num}, skipping")
                continue

            # 17Track API structure: item.track_info contains all tracking data
            track_info = item.get("track_info", {}) or {}
            latest_status = track_info.get("latest_status", {}) or {}
            latest_event = track_info.get("latest_event", {}) or {}
            shipping_info = track_info.get("shipping_info", {}) or {}
            recipient_address = shipping_info.get("recipient_address", {}) or {}
            misc_info = track_info.get("misc_info", {}) or {}

            flattened_item = {
                "batch_number": batch_num,
                "tracking_number": item.get("number"),
                "carrier_code": item.get("carrier"),
                "delivery_status": latest_status.get("status"),
                "sub_status": latest_status.get("sub_status"),
                "latest_event_description": latest_event.get("description"),
                "latest_event_time": latest_event.get("time_iso"),
                "latest_event_location": latest_event.get("location"),
                "destination_country": recipient_address.get("country"),
                "destination_state": recipient_address.get("state"),
                "destination_city": recipient_address.get("city"),
                "destination_postal_code": recipient_address.get("postal_code"),
                "service_type": misc_info.get("service_type"),
                "weight_raw": misc_info.get("weight_raw"),
                "weight_kg": misc_info.get("weight_kg"),
                "processed_timestamp": batch_result["timestamp"],
                # Include raw track data for debugging (truncated)
                "raw_track_data": (
                    json.dumps(track_info)[:500] + "..." if track_info else None
                ),
            }
            flattened_data.append(flattened_item)

    # Check if we have any data to export
    if not flattened_data:
        logger.warning("⚠️ No tracking data available for CSV export")
        # Create empty CSV with headers only
        empty_df = pd.DataFrame(
            columns=[
                "batch_number",
                "tracking_number",
                "carrier_code",
                "delivery_status",
                "sub_status",
                "latest_event_description",
                "latest_event_time",
                "latest_event_location",
                "destination_country",
                "destination_state",
                "destination_city",
                "destination_postal_code",
                "service_type",
                "weight_raw",
                "weight_kg",
                "processed_timestamp",
                "raw_track_data",
            ]
        )
        empty_df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info(
            f"📊 Exported empty CSV file (no tracking data found) to {csv_path}"
        )
        return csv_path

    # Create DataFrame and export to CSV
    df = pd.DataFrame(flattened_data)
    df.to_csv(csv_path, index=False, encoding="utf-8")

    logger.info(f"📊 Exported {len(df)} tracking records to {csv_path}")
    return csv_path


def export_status_monitoring_summary(
    status_summary: Dict[str, Any], output_filename: Optional[str] = None
) -> str:
    """
    Export status monitoring summary to JSON file

    Args:
        status_summary: Status summary dictionary
        output_filename: Optional custom filename

    Returns:
        Path to the exported JSON file
    """
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"tracking_status_summary_{timestamp}.json"

    json_path = os.path.join(OUTPUT_DIR, output_filename)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(status_summary, f, indent=2, ensure_ascii=False)

    logger.info(f"📋 Exported status summary to {json_path}")
    return json_path


def demo_tracking_pipeline(
    tracking_numbers: List[str],
    api_token: Optional[str] = None,
    carrier_code: int = DEFAULT_CARRIER_CODE,
    export_json: bool = True,
    export_csv: bool = True,
) -> Optional[Dict[str, str]]:
    """
    Demo pipeline for processing manually provided tracking numbers with 17Track API

    This demo pipeline follows the correct 17Track API workflow:
    1. Accept manually provided tracking numbers (no database required)
    2. Register tracking numbers with 17Track API
    3. Wait 5 minutes for 17Track to process the registration
    4. Retrieve tracking information for registered numbers
    5. Export results to JSON and CSV formats

    Args:
        tracking_numbers: List of tracking numbers to process
        api_token: 17Track API token
        carrier_code: Carrier code to use
        export_json: Whether to export raw results to JSON
        export_csv: Whether to export results to CSV

    Returns:
        Dictionary with paths to exported files if successful, None otherwise

    Note:
        Execution time will be approximately 5+ minutes per batch due to the
        required processing wait time between registration and retrieval steps.
        For 30 tracking numbers (1 batch), expect ~5 minutes total execution time.
    """
    try:
        logger.info("🚀 Starting 17Track Demo Pipeline")
        logger.info("=" * 60)

        # Validate input
        if not tracking_numbers:
            logger.error("❌ No tracking numbers provided")
            return None

        logger.info(
            f"📦 Processing {len(tracking_numbers)} manually provided tracking numbers"
        )
        logger.info(f"📋 Sample tracking numbers: {tracking_numbers[:5]}")

        # Initialize 17Track client
        client = TrackingClient(api_token)

        # Process in batches
        results, successful, failed = process_tracking_numbers_in_batches(
            tracking_numbers, client, carrier_code
        )

        logger.info(
            f"📊 Processing complete: {successful} successful, {failed} failed batches"
        )

        # Export results
        exported_files = {}

        if results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Export raw JSON
            if export_json:
                json_filename = f"demo_17track_raw_{timestamp}.json"
                json_path = export_raw_json_results(results, json_filename)
                exported_files["json"] = json_path

            # Export consolidated CSV
            if export_csv:
                csv_filename = f"demo_17track_consolidated_{timestamp}.csv"
                csv_path = export_tracking_results_to_csv(results, csv_filename)
                exported_files["csv"] = csv_path

            logger.info("✅ Demo pipeline completed successfully!")
            if exported_files:
                for file_type, file_path in exported_files.items():
                    logger.info(f"📄 {file_type.upper()} results: {file_path}")

            return exported_files

        logger.warning("⚠️ No results to export")
        return None

    except Exception as e:
        logger.error(f"❌ Demo pipeline failed: {e}")
        return None


# Demo tracking numbers for testing
DEMO_TRACKING_NUMBERS = [
    "1ZVX23230333926007",  # UPS tracking number
    "1ZX041680390454826",  # UPS tracking number
    "1ZX041680392116410",  # UPS tracking number
    "1ZX041680393993711",  # UPS tracking number
    "1ZX041680394889056",  # UPS tracking number
]


def main():
    """
    Main demo function - demonstrates the tracking pipeline with sample tracking numbers
    """
    print("🎯 17Track API Demo")
    print("=" * 50)
    print("This demo shows the complete 17Track API workflow:")
    print("1. Register tracking numbers")
    print("2. Wait 5 minutes for processing")
    print("3. Retrieve tracking information")
    print("4. Export to JSON and CSV")
    print("=" * 50)

    # Run demo with sample tracking numbers
    result = demo_tracking_pipeline(
        tracking_numbers=DEMO_TRACKING_NUMBERS,
        api_token=API_TOKEN,
        carrier_code=DEFAULT_CARRIER_CODE,
        export_json=True,
        export_csv=True,
    )

    if result:
        print("\n🎉 Demo completed successfully!")
        print("📄 Files exported:")
        for file_type, file_path in result.items():
            print(f"   • {file_type.upper()}: {os.path.basename(file_path)}")
    else:
        print("\n❌ Demo failed or no results")


if __name__ == "__main__":
    main()
