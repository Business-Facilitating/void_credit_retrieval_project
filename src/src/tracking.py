import json
import os
import time
from datetime import datetime
from typing import List, Optional

import trackingmore
from dotenv import load_dotenv
from trackingmore.exception import TrackingMoreException

# Load environment variables from .env file
load_dotenv()

# DuckDB imports
try:
    import duckdb

    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
    print("❌ DuckDB library not available. Install with: poetry add duckdb")

# Configuration - Using environment variables
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "40"))  # API rate limit consideration
API_DELAY = float(os.getenv("API_DELAY", "1.0"))  # Delay between API calls in seconds
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "carrier_invoice_extraction.duckdb")
TABLE_NAME = "carrier_invoice_data.carrier_invoice_data"

# Ensure output directory exists
output_dir = os.getenv("OUTPUT_DIR", "data/output")
os.makedirs(output_dir, exist_ok=True)

# TrackingMore API configuration - Using environment variables
API_KEY = os.getenv("TRACKINGMORE_API_KEY")
if not API_KEY:
    raise ValueError(
        "TRACKINGMORE_API_KEY environment variable is required. Please check your .env file."
    )

trackingmore.api_key = API_KEY


def connect_to_duckdb() -> Optional[duckdb.DuckDBPyConnection]:
    """Connect to the DuckDB file and return connection"""
    if not DUCKDB_AVAILABLE:
        print("❌ DuckDB not available")
        return None

    if not os.path.exists(DUCKDB_PATH):
        print(f"❌ DuckDB file not found: {DUCKDB_PATH}")
        print(
            "💡 Run the pipeline first: poetry run python src/src/dlt_pipeline_examples.py"
        )
        return None

    try:
        conn = duckdb.connect(DUCKDB_PATH)
        print(f"✅ Connected to DuckDB: {DUCKDB_PATH}")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to DuckDB: {e}")
        return None


def extract_tracking_numbers(conn: duckdb.DuckDBPyConnection) -> List[str]:
    """Extract unique tracking numbers from the database"""
    try:
        print(f"🔍 Extracting unique tracking numbers from {TABLE_NAME}...")

        # Query to get unique, non-empty tracking numbers (limited to 30 for testing)
        query = f"""
            SELECT DISTINCT tracking_number
            FROM {TABLE_NAME}
            WHERE tracking_number IS NOT NULL
            AND tracking_number != ''
            AND LENGTH(TRIM(tracking_number)) > 0
            ORDER BY tracking_number
            LIMIT 30
        """

        result = conn.execute(query).fetchall()
        tracking_numbers = [row[0] for row in result]

        print(f"📊 Found {len(tracking_numbers)} unique tracking numbers")
        return tracking_numbers

    except Exception as e:
        print(f"❌ Failed to extract tracking numbers: {e}")
        return []


def create_batches(tracking_numbers: List[str], batch_size: int) -> List[List[str]]:
    """Split tracking numbers into batches"""
    batches = []
    for i in range(0, len(tracking_numbers), batch_size):
        batch = tracking_numbers[i : i + batch_size]
        batches.append(batch)
    return batches


def call_tracking_api(tracking_numbers: List[str]) -> dict:
    """Make API call to TrackingMore for a batch of tracking numbers using trackingmore SDK"""
    try:
        # Format tracking numbers as comma-separated string (exact documentation format)
        tracking_string = ",".join(tracking_numbers)

        # Use trackingmore SDK with exact pattern from documentation
        params = {"tracking_numbers": tracking_string, "courier_code": "ups"}

        result = trackingmore.tracking.get_tracking_results(params)

        return {
            "success": True,
            "data": result,
            "status_code": 200,
            "tracking_numbers": tracking_numbers,
        }

    except TrackingMoreException as ce:
        return {
            "success": False,
            "error": str(ce),
            "status_code": None,
            "tracking_numbers": tracking_numbers,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"other error: {e}",
            "status_code": None,
            "tracking_numbers": tracking_numbers,
        }


def save_batch_results(
    batch_num: int, total_batches: int, result: dict, timestamp: str
) -> str:
    """Save batch results to JSON file"""
    if result["success"]:
        filename = (
            f"tracking_batch_{batch_num:03d}_of_{total_batches:03d}_{timestamp}.json"
        )
        filepath = os.path.join(output_dir, filename)

        # Add comprehensive batch metadata and API response in detailed tracking_batch format
        batch_data = {
            "batch_info": {
                "batch_number": batch_num,
                "total_batches": total_batches,
                "timestamp": timestamp,
                "tracking_count": len(result["data"].get("data", [])),
                "status": "success",
                "api_endpoint": "trackings/get",
                "request_method": "GET",
            },
            "tracking_numbers_requested": result.get("tracking_numbers", []),
            "api_response": result["data"],
            "response_metadata": {
                "status_code": result["status_code"],
                "response_time": timestamp,
                "total_records_found": len(result["data"].get("data", [])),
                "api_success": True,
            },
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(batch_data, f, indent=2, ensure_ascii=False)

        return filepath
    else:
        # Save error data in detailed tracking_batch format
        filename = f"tracking_batch_{batch_num:03d}_of_{total_batches:03d}_ERROR_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        error_data = {
            "batch_info": {
                "batch_number": batch_num,
                "total_batches": total_batches,
                "timestamp": timestamp,
                "tracking_count": 0,
                "status": "error",
                "api_endpoint": "trackings/get",
                "request_method": "GET",
            },
            "tracking_numbers_requested": result["tracking_numbers"],
            "api_response": None,
            "error_details": {
                "status_code": result["status_code"],
                "error_message": result["error"],
                "error_type": "API_ERROR",
            },
            "response_metadata": {
                "status_code": result["status_code"],
                "response_time": timestamp,
                "total_records_found": 0,
                "api_success": False,
            },
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(error_data, f, indent=2, ensure_ascii=False)

        return filepath


def main():
    """Main execution function"""
    print("🚀 TrackingMore Status Query from DuckDB")
    print("=" * 50)

    # Connect to DuckDB
    conn = connect_to_duckdb()
    if not conn:
        return

    try:
        # Extract tracking numbers
        tracking_numbers = extract_tracking_numbers(conn)
        if not tracking_numbers:
            print("❌ No tracking numbers found in database")
            return

        # Create batches
        batches = create_batches(tracking_numbers, BATCH_SIZE)
        total_batches = len(batches)

        print(
            f"📦 Processing {len(tracking_numbers)} tracking numbers in {total_batches} batches"
        )
        print(f"⚙️ Batch size: {BATCH_SIZE}")
        print(f"⏱️ API delay: {API_DELAY} seconds between calls")

        # Generate timestamp for this run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Process each batch
        successful_batches = 0
        failed_batches = 0
        total_tracking_records = 0

        for batch_num, batch in enumerate(batches, 1):
            print(
                f"\n🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} tracking numbers)"
            )
            print(
                f"   📋 Tracking numbers: {', '.join(batch[:3])}{'...' if len(batch) > 3 else ''}"
            )

            # Query tracking information
            print("   🔍 Querying tracking information...")
            result = call_tracking_api(batch)

            # Save results
            filepath = save_batch_results(batch_num, total_batches, result, timestamp)

            if result["success"]:
                successful_batches += 1
                tracking_count = len(result["data"].get("data", []))
                total_tracking_records += tracking_count

                print(f"   ✅ Success! Found {tracking_count} tracking records")
                print(f"   📁 Saved to: {os.path.basename(filepath)}")

                # Print summary of tracking statuses in this batch
                for item in result["data"].get("data", []):
                    status = item.get("delivery_status", "Unknown")
                    tracking_num = item.get("tracking_number", "Unknown")
                    print(f"      📦 {tracking_num}: {status}")

            else:
                failed_batches += 1
                print(f"   ❌ Failed! Status: {result.get('status_code', 'Unknown')}")
                print(f"   📁 Error saved to: {os.path.basename(filepath)}")
                print(f"   💬 Error: {result.get('error', 'Unknown error')}")

            # Add delay between API calls (except for the last batch)
            if batch_num < total_batches:
                print(f"   ⏳ Waiting {API_DELAY} seconds before next batch...")
                time.sleep(API_DELAY)

        # Final summary
        print("\n🎯 Processing Complete!")
        print("=" * 30)
        print(f"📊 Total tracking numbers processed: {len(tracking_numbers)}")
        print(f"📦 Total batches: {total_batches}")
        print(f"✅ Successful batches: {successful_batches}")
        print(f"❌ Failed batches: {failed_batches}")
        print(f"📋 Total tracking records found: {total_tracking_records}")
        print(f"📁 Results saved in: {output_dir}")
        print(f"🕒 Run timestamp: {timestamp}")

        # Create summary file
        summary_data = {
            "run_summary": {
                "timestamp": timestamp,
                "total_tracking_numbers": len(tracking_numbers),
                "total_batches": total_batches,
                "successful_batches": successful_batches,
                "failed_batches": failed_batches,
                "total_tracking_records_found": total_tracking_records,
                "batch_size": BATCH_SIZE,
                "api_delay": API_DELAY,
            },
            "batch_files": [
                f"tracking_batch_{i:03d}_of_{total_batches:03d}_{timestamp}.json"
                for i in range(1, successful_batches + 1)
            ],
        }

        summary_filepath = os.path.join(
            output_dir, f"tracking_summary_{timestamp}.json"
        )
        with open(summary_filepath, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        print(f"📋 Summary saved to: {os.path.basename(summary_filepath)}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Close database connection
        if conn:
            conn.close()
            print("🔌 Database connection closed")


if __name__ == "__main__":
    main()
