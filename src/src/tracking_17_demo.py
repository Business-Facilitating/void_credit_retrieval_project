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
from dateutil import parser

# 17Track API Configuration - Using environment variables
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv(
    "SEVENTEEN_TRACK_API_URL", "https://api.17track.net/track/v2.4/gettrackinfo"
)
REGISTER_API_URL = os.getenv(
    "SEVENTEEN_TRACK_REGISTER_URL", "https://api.17track.net/track/v2.2/register"
)
API_TOKEN = os.getenv("SEVENTEEN_TRACK_API_TOKEN")
DEFAULT_CARRIER_CODE = int(
    os.getenv("SEVENTEEN_TRACK_DEFAULT_CARRIER_CODE", "100002")
)  # UPS carrier code
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "40"))  # Maximum tracking numbers per API call
API_DELAY = float(os.getenv("API_DELAY", "1.0"))  # Delay between API calls in seconds

# Validate required environment variables
if not API_TOKEN:
    raise ValueError(
        "SEVENTEEN_TRACK_API_TOKEN environment variable is required. Please check your .env file."
    )

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


def find_label_created_event(track_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Find the "label created" event from tracking information

    Args:
        track_info: Track info dictionary from 17Track API response

    Returns:
        Label created event dictionary if found, None otherwise
    """
    try:
        # Check tracking providers for events
        tracking = track_info.get("tracking", {})
        providers = tracking.get("providers", [])

        for provider in providers:
            events = provider.get("events", [])

            # Look for InfoReceived stage or label creation descriptions
            for event in events:
                stage = event.get("stage", "")
                sub_status = event.get("sub_status", "")
                description = event.get("description", "").lower()

                # Check for label created indicators
                if (
                    stage == "InfoReceived"
                    or sub_status == "InfoReceived"
                    or "label" in description
                    or "shipper created" in description
                ):
                    return event

        # Also check milestone data for InfoReceived
        milestone = track_info.get("milestone", [])
        for milestone_event in milestone:
            if milestone_event.get("key_stage") == "InfoReceived":
                time_iso = milestone_event.get("time_iso")
                if time_iso:
                    return {
                        "time_iso": time_iso,
                        "stage": "InfoReceived",
                        "description": "Label created (from milestone)",
                        "sub_status": "InfoReceived",
                    }

    except Exception as e:
        logger.warning(f"Error finding label created event: {e}")

    return None


def calculate_days_since_label_created(label_event: Dict[str, Any]) -> Optional[int]:
    """
    Calculate the number of days since the label was created

    Args:
        label_event: Label created event dictionary

    Returns:
        Number of days since label creation, None if unable to calculate
    """
    try:
        time_iso = label_event.get("time_iso")
        if not time_iso:
            return None

        # Parse the ISO timestamp
        label_date = parser.parse(time_iso)
        current_date = datetime.now(label_date.tzinfo)  # Use same timezone

        # Calculate difference in days
        days_diff = (current_date - label_date).days
        return days_diff

    except Exception as e:
        logger.warning(f"Error calculating days since label created: {e}")
        return None


def analyze_tracking_for_void_candidates(
    results: List[Dict[str, Any]], min_days: int = 15, max_days: int = 20
) -> List[Dict[str, Any]]:
    """
    Analyze tracking results to find packages that need voiding

    Identifies tracking numbers with "label created" status that is between
    min_days and max_days old (inclusive).

    Args:
        results: List of tracking result dictionaries from API
        min_days: Minimum days since label creation (default: 15)
        max_days: Maximum days since label creation (default: 20)

    Returns:
        List of dictionaries containing tracking numbers that need voiding
    """
    void_candidates = []

    logger.info(
        f"🔍 Analyzing tracking results for void candidates ({min_days}-{max_days} days old)"
    )

    for batch_result in results:
        batch_num = batch_result.get("batch_number", "unknown")

        # Handle different result structures
        tracking_result = batch_result.get("tracking_result") or batch_result.get(
            "result", {}
        )

        if not tracking_result:
            logger.warning(f"⚠️ No tracking result for batch {batch_num}")
            continue

        api_data = tracking_result.get("data", {})
        accepted_items = api_data.get("accepted", [])

        for item in accepted_items:
            if not item or not isinstance(item, dict):
                continue

            tracking_number = item.get("number")
            track_info = item.get("track_info", {})

            if not tracking_number or not track_info:
                continue

            # Find label created event
            label_event = find_label_created_event(track_info)

            if not label_event:
                logger.debug(f"📋 No label created event found for {tracking_number}")
                continue

            # Calculate days since label creation
            days_since_label = calculate_days_since_label_created(label_event)

            if days_since_label is None:
                logger.warning(f"⚠️ Could not calculate days for {tracking_number}")
                continue

            # Check if it falls within the void candidate range
            if min_days <= days_since_label <= max_days:
                # Get current status for context
                latest_status = track_info.get("latest_status", {})
                current_status = latest_status.get("status", "unknown")
                current_sub_status = latest_status.get("sub_status", "unknown")

                void_candidate = {
                    "tracking_number": tracking_number,
                    "batch_number": batch_num,
                    "days_since_label_created": days_since_label,
                    "label_created_date": label_event.get("time_iso"),
                    "label_event_description": label_event.get("description", ""),
                    "current_status": current_status,
                    "current_sub_status": current_sub_status,
                    "void_reason": f"Label created {days_since_label} days ago",
                    "analysis_timestamp": datetime.now().isoformat(),
                    "needs_void": True,
                }

                void_candidates.append(void_candidate)

                logger.info(
                    f"🚨 VOID CANDIDATE: {tracking_number} - "
                    f"Label created {days_since_label} days ago "
                    f"(Status: {current_status})"
                )
            else:
                logger.debug(
                    f"📋 {tracking_number}: Label created {days_since_label} days ago "
                    f"(outside {min_days}-{max_days} day range)"
                )

    logger.info(f"🎯 Found {len(void_candidates)} tracking numbers that need voiding")
    return void_candidates


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


def export_void_candidates_to_csv(
    void_candidates: List[Dict[str, Any]], output_filename: Optional[str] = None
) -> str:
    """
    Export void candidates to CSV file

    Args:
        void_candidates: List of void candidate dictionaries
        output_filename: Optional custom filename

    Returns:
        Path to the exported CSV file
    """
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"void_candidates_{timestamp}.csv"

    csv_path = os.path.join(OUTPUT_DIR, output_filename)

    if not void_candidates:
        # Create empty CSV with headers
        empty_df = pd.DataFrame(
            columns=[
                "tracking_number",
                "batch_number",
                "days_since_label_created",
                "label_created_date",
                "label_event_description",
                "current_status",
                "current_sub_status",
                "void_reason",
                "analysis_timestamp",
                "needs_void",
            ]
        )
        empty_df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info(f"📊 Exported empty void candidates CSV to {csv_path}")
        return csv_path

    # Create DataFrame and export to CSV
    df = pd.DataFrame(void_candidates)
    df.to_csv(csv_path, index=False, encoding="utf-8")

    logger.info(f"📊 Exported {len(df)} void candidates to {csv_path}")
    return csv_path


def export_void_candidates_to_json(
    void_candidates: List[Dict[str, Any]], output_filename: Optional[str] = None
) -> str:
    """
    Export void candidates to JSON file

    Args:
        void_candidates: List of void candidate dictionaries
        output_filename: Optional custom filename

    Returns:
        Path to the exported JSON file
    """
    if not output_filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"void_candidates_{timestamp}.json"

    json_path = os.path.join(OUTPUT_DIR, output_filename)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(void_candidates, f, indent=2, ensure_ascii=False)

    logger.info(f"📄 Exported void candidates to {json_path}")
    return json_path


def demo_tracking_pipeline(
    tracking_numbers: List[str],
    api_token: Optional[str] = None,
    carrier_code: int = DEFAULT_CARRIER_CODE,
    export_json: bool = True,
    export_csv: bool = True,
    analyze_void_candidates: bool = True,
    void_min_days: int = 15,
    void_max_days: int = 20,
) -> Optional[Dict[str, str]]:
    """
    Demo pipeline for processing manually provided tracking numbers with 17Track API

    This demo pipeline follows the correct 17Track API workflow:
    1. Accept manually provided tracking numbers (no database required)
    2. Register tracking numbers with 17Track API
    3. Wait 5 minutes for 17Track to process the registration
    4. Retrieve tracking information for registered numbers
    5. Analyze tracking status for void candidates (optional)
    6. Export results to JSON and CSV formats

    Args:
        tracking_numbers: List of tracking numbers to process
        api_token: 17Track API token
        carrier_code: Carrier code to use
        export_json: Whether to export raw results to JSON
        export_csv: Whether to export results to CSV
        analyze_void_candidates: Whether to analyze for packages needing voiding
        void_min_days: Minimum days since label creation for void candidates
        void_max_days: Maximum days since label creation for void candidates

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

        # Analyze for void candidates if requested
        void_candidates = []
        if analyze_void_candidates and results:
            logger.info("🔍 Analyzing tracking results for void candidates...")
            void_candidates = analyze_tracking_for_void_candidates(
                results, void_min_days, void_max_days
            )

            if void_candidates:
                logger.info(
                    f"🚨 Found {len(void_candidates)} packages that need voiding!"
                )
                for candidate in void_candidates:
                    logger.info(
                        f"   • {candidate['tracking_number']}: "
                        f"{candidate['days_since_label_created']} days old "
                        f"({candidate['current_status']})"
                    )
            else:
                logger.info("✅ No packages found that need voiding")

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

            # Export void candidates if any were found
            if void_candidates:
                void_csv_filename = f"demo_void_candidates_{timestamp}.csv"
                void_csv_path = export_void_candidates_to_csv(
                    void_candidates, void_csv_filename
                )
                exported_files["void_csv"] = void_csv_path

                void_json_filename = f"demo_void_candidates_{timestamp}.json"
                void_json_path = export_void_candidates_to_json(
                    void_candidates, void_json_filename
                )
                exported_files["void_json"] = void_json_path

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
    "1ZX041680390454826",  # UPS tracking number void
    "1ZX041680392116410",  # UPS tracking number void
    "1ZX041680393993711",  # UPS tracking number void
    "1ZX041680394889056",  # UPS tracking number
]


def analyze_existing_tracking_data_for_voids(
    json_file_path: str,
    min_days: int = 15,
    max_days: int = 20,
    export_results: bool = True,
) -> Optional[List[Dict[str, Any]]]:
    """
    Analyze existing tracking data from JSON file for void candidates

    This function allows you to analyze previously collected tracking data
    without needing to make new API calls.

    Args:
        json_file_path: Path to existing tracking results JSON file
        min_days: Minimum days since label creation for void candidates
        max_days: Maximum days since label creation for void candidates
        export_results: Whether to export void candidates to files

    Returns:
        List of void candidates if found, None if error
    """
    try:
        logger.info(f"📂 Loading tracking data from {json_file_path}")

        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, list):
            results = data
        elif isinstance(data, dict) and "results" in data:
            results = data["results"]
        else:
            # Assume it's a single result
            results = [data]

        logger.info(f"📊 Analyzing {len(results)} tracking result batches")

        # Analyze for void candidates
        void_candidates = analyze_tracking_for_void_candidates(
            results, min_days, max_days
        )

        if export_results and void_candidates:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Export void candidates
            void_csv_path = export_void_candidates_to_csv(
                void_candidates, f"analysis_void_candidates_{timestamp}.csv"
            )
            void_json_path = export_void_candidates_to_json(
                void_candidates, f"analysis_void_candidates_{timestamp}.json"
            )

            logger.info("📄 Exported void analysis results:")
            logger.info(f"   • CSV: {os.path.basename(void_csv_path)}")
            logger.info(f"   • JSON: {os.path.basename(void_json_path)}")

        return void_candidates

    except Exception as e:
        logger.error(f"❌ Error analyzing existing tracking data: {e}")
        return None


def main():
    """
    Main demo function - demonstrates the tracking pipeline with sample tracking numbers
    """
    print("🎯 17Track API Demo with Void Analysis")
    print("=" * 60)
    print("This demo shows the complete 17Track API workflow:")
    print("1. Register tracking numbers")
    print("2. Wait 5 minutes for processing")
    print("3. Retrieve tracking information")
    print("4. Analyze for packages needing voiding (15-20 days old)")
    print("5. Export to JSON and CSV")
    print("=" * 60)

    # Run demo with sample tracking numbers
    result = demo_tracking_pipeline(
        tracking_numbers=DEMO_TRACKING_NUMBERS,
        api_token=API_TOKEN,
        carrier_code=DEFAULT_CARRIER_CODE,
        export_json=True,
        export_csv=True,
        analyze_void_candidates=True,
        void_min_days=15,
        void_max_days=20,
    )

    if result:
        print("\n🎉 Demo completed successfully!")
        print("📄 Files exported:")
        for file_type, file_path in result.items():
            if "void" in file_type:
                print(f"   • {file_type.upper()}: {os.path.basename(file_path)} 🚨")
            else:
                print(f"   • {file_type.upper()}: {os.path.basename(file_path)}")
    else:
        print("\n❌ Demo failed or no results")


if __name__ == "__main__":
    main()
    main()
    main()
