#!/usr/bin/env python3
"""
17Track API Integration Module
==============================

Clean implementation of 17Track API (api.17track.net/track/v2.4/gettrackinfo)
for the gsr_automation project. Provides tracking functionality with batch processing,
error handling, and CSV export capabilities.

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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# DuckDB integration
try:
    import duckdb

    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

# 17Track API Configuration - Using environment variables
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

# DuckDB Configuration
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "carrier_invoice_extraction.duckdb")
TABLE_NAME = "carrier_invoice_data.carrier_invoice_data"

# Ensure output directory exists
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data/output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def connect_to_duckdb() -> Optional[duckdb.DuckDBPyConnection]:
    """Connect to the DuckDB file and return connection"""
    if not DUCKDB_AVAILABLE:
        logger.error("❌ DuckDB not available. Install with: pip install duckdb")
        return None

    if not os.path.exists(DUCKDB_PATH):
        logger.error(f"❌ DuckDB file not found: {DUCKDB_PATH}")
        logger.info(
            "💡 Run the pipeline first: poetry run python src/src/dlt_pipeline_examples.py"
        )
        return None

    try:
        conn = duckdb.connect(DUCKDB_PATH)
        logger.info(f"✅ Connected to DuckDB: {DUCKDB_PATH}")
        return conn
    except Exception as e:
        logger.error(f"❌ Failed to connect to DuckDB: {e}")
        return None


def extract_tracking_numbers_from_duckdb(limit: int = 30) -> List[str]:
    """
    Extract unique tracking numbers from DuckDB (no date filtering)

    Args:
        limit: Maximum number of tracking numbers to return (default: 30)

    Returns:
        List of unique tracking numbers
    """
    conn = connect_to_duckdb()
    if not conn:
        return []

    try:
        logger.info(f"🔍 Extracting {limit} tracking numbers from {TABLE_NAME}...")

        # Simple query to get unique tracking numbers without date filtering
        query = f"""
            SELECT DISTINCT tracking_number
            FROM {TABLE_NAME}
            WHERE tracking_number IS NOT NULL
            AND tracking_number != ''
            AND LENGTH(TRIM(tracking_number)) > 0
            ORDER BY tracking_number
            LIMIT {limit}
        """

        result = conn.execute(query).fetchall()
        tracking_numbers = [row[0] for row in result]

        logger.info(f"📊 Found {len(tracking_numbers)} unique tracking numbers")

        if tracking_numbers:
            logger.info(f"📋 Sample tracking numbers: {tracking_numbers[:5]}")

        return tracking_numbers

    except Exception as e:
        logger.error(f"❌ Failed to extract tracking numbers from DuckDB: {e}")
        return []
    finally:
        if conn:
            conn.close()


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
            API response dict or None if failed
        """
        try:
            # Prepare payload based on 17Track documentation
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
        List of tracking numbers extracted from batch files
    """
    tracking_numbers = []

    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            summary_data = json.load(f)

        # Get the directory containing the summary file
        base_dir = os.path.dirname(json_file_path)

        # Process each batch file mentioned in the summary
        for batch_file in summary_data.get("batch_files", []):
            batch_file_path = os.path.join(base_dir, batch_file)

            if os.path.exists(batch_file_path):
                with open(batch_file_path, "r", encoding="utf-8") as bf:
                    batch_data = json.load(bf)

                # Extract tracking numbers from API response data
                # Handle both TrackingMore and 17Track formats
                api_data = batch_data.get("api_response", {}).get("data", [])
                if not api_data:
                    # Try alternative structure for 17Track format
                    result_data = batch_data.get("result", {}).get("data", {})
                    api_data = (
                        result_data.get("accepted", [])
                        if isinstance(result_data, dict)
                        else []
                    )

                for item in api_data:
                    # TrackingMore format
                    if "tracking_number" in item:
                        tracking_numbers.append(item["tracking_number"])
                    # 17Track format
                    elif "number" in item:
                        tracking_numbers.append(item["number"])

        logger.info(
            f"📋 Loaded {len(tracking_numbers)} tracking numbers from {json_file_path}"
        )
        return tracking_numbers

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

    # Format as ISO 8601 with timezone
    start_iso = start_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    end_iso = end_date.strftime("%Y-%m-%dT%H:%M:%S+00:00")

    return start_iso, end_iso


def monitor_tracking_status_changes(
    client: TrackingClient,
    tracking_numbers: List[str],
    carrier_code: int = DEFAULT_CARRIER_CODE,
    batch_size: int = BATCH_SIZE,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Monitor tracking status changes for a list of tracking numbers

    Args:
        client: 17Track client instance
        tracking_numbers: List of tracking numbers to monitor
        carrier_code: Carrier code to use
        batch_size: Number of tracking numbers per batch

    Returns:
        Tuple of (detailed_results, status_summary)
    """
    logger.info(
        f"📊 Starting status monitoring for {len(tracking_numbers)} tracking numbers"
    )

    # Process tracking numbers in batches
    results, successful, failed = process_tracking_numbers_in_batches(
        tracking_numbers, client, carrier_code, batch_size
    )

    # Analyze status changes and create summary
    status_summary = {
        "total_tracked": len(tracking_numbers),
        "successful_queries": successful,
        "failed_queries": failed,
        "status_counts": {},
        "delivery_status_breakdown": {},
        "monitoring_timestamp": datetime.now().isoformat(),
    }

    # Count status occurrences (17Track API format)
    for batch_result in results:
        api_data = batch_result["result"].get("data", {})
        accepted_items = api_data.get("accepted", [])

        for item in accepted_items:
            # 17Track API structure: item.track_info.latest_status
            track_info = item.get("track_info", {})
            latest_status = track_info.get("latest_status", {})
            delivery_status = latest_status.get("status", "unknown")
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
        api_data = tracking_result.get("data", {})
        accepted_items = api_data.get("accepted", [])

        for item in accepted_items:
            # 17Track API structure: item.track_info contains all tracking data
            track_info = item.get("track_info", {})
            latest_status = track_info.get("latest_status", {})
            latest_event = track_info.get("latest_event", {})
            shipping_info = track_info.get("shipping_info", {})
            recipient_address = shipping_info.get("recipient_address", {})
            misc_info = track_info.get("misc_info", {})

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

    # Create DataFrame and export to CSV
    df = pd.DataFrame(flattened_data)
    df.to_csv(csv_path, index=False, encoding="utf-8")

    logger.info(f"📊 Exported {len(df)} tracking records to {csv_path}")
    return csv_path


def query_tracking_by_date_range(
    client: TrackingClient,
    days_back: int = 7,
    carrier_code: Optional[int] = None,
    export_csv: bool = True,
) -> Optional[str]:
    """
    Query tracking results for a specific date range

    Note: 17Track API doesn't support date range queries directly.
    This function is kept for compatibility but will return None.

    Args:
        client: 17Track client instance
        days_back: Number of days to go back from today (not used)
        carrier_code: Optional carrier code filter (not used)
        export_csv: Whether to export results to CSV (not used)

    Returns:
        None (17Track API doesn't support date range queries)
    """
    logger.warning(
        f"⚠️ Date range queries are not supported by 17Track API for last {days_back} days. "
        "Use process_tracking_numbers_in_batches() with specific tracking numbers instead."
    )
    return None


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

    logger.info(f"📋 Status summary exported to {json_path}")
    return json_path


def main_tracking_pipeline(
    json_file_path: str,
    api_token: Optional[str] = None,
    carrier_code: int = DEFAULT_CARRIER_CODE,
    export_csv: bool = True,
) -> Optional[str]:
    """
    Main pipeline for querying tracking information from JSON file

    Args:
        json_file_path: Path to tracking summary JSON file
        api_token: 17Track API token
        carrier_code: Carrier code to use
        export_csv: Whether to export results to CSV

    Returns:
        Path to exported CSV file if successful, None otherwise
    """
    try:
        # Initialize client
        client = TrackingClient(api_token)

        # Load tracking numbers
        tracking_numbers = load_tracking_numbers_from_json(json_file_path)
        if not tracking_numbers:
            logger.error("❌ No tracking numbers found to process")
            return None

        # Process in batches
        results, successful, failed = process_tracking_numbers_in_batches(
            tracking_numbers, client, carrier_code
        )

        logger.info(
            f"📊 Processing complete: {successful} successful, {failed} failed batches"
        )

        # Export to CSV if requested and we have results
        if export_csv and results:
            csv_path = export_tracking_results_to_csv(results)
            return csv_path

        return None

    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        return None


def main_duckdb_tracking_pipeline(
    limit: int = 30,
    api_token: Optional[str] = None,
    carrier_code: int = DEFAULT_CARRIER_CODE,
    export_json: bool = True,
    export_csv: bool = True,
) -> Optional[Dict[str, str]]:
    """
    Main pipeline for extracting tracking numbers from DuckDB and querying 17Track API

    This pipeline follows the correct 17Track API workflow:
    1. Extract tracking numbers from DuckDB (no date filtering)
    2. Register tracking numbers with 17Track API
    3. Wait 5 minutes for 17Track to process the registration
    4. Retrieve tracking information for registered numbers
    5. Export results to JSON and CSV formats

    Args:
        limit: Maximum number of tracking numbers to extract (default: 30)
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
        logger.info("🚀 Starting DuckDB to 17Track Pipeline")
        logger.info("=" * 60)

        # Extract tracking numbers from DuckDB
        tracking_numbers = extract_tracking_numbers_from_duckdb(limit)
        if not tracking_numbers:
            logger.error("❌ No tracking numbers found in DuckDB")
            return None

        logger.info(f"📦 Found {len(tracking_numbers)} tracking numbers to process")

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
                json_filename = f"duckdb_17track_raw_{timestamp}.json"
                json_path = export_raw_json_results(results, json_filename)
                exported_files["json"] = json_path

            # Export consolidated CSV
            if export_csv:
                csv_filename = f"duckdb_17track_consolidated_{timestamp}.csv"
                csv_path = export_tracking_results_to_csv(results, csv_filename)
                exported_files["csv"] = csv_path

            logger.info("✅ Pipeline completed successfully!")
            if exported_files:
                for file_type, file_path in exported_files.items():
                    logger.info(f"📄 {file_type.upper()} results: {file_path}")

            return exported_files

        logger.warning("⚠️ No results to export")
        return None

    except Exception as e:
        logger.error(f"❌ DuckDB pipeline failed: {e}")
        return None
