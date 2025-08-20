#!/usr/bin/env python3
"""
Test script for the complete 17Track pipeline functionality
"""

import json
import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import from src.src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.src.tracking_17 import (
    API_TOKEN,
    DEFAULT_CARRIER_CODE,
    TrackingClient,
    export_tracking_results_to_csv,
    monitor_tracking_status_changes,
    process_tracking_numbers_in_batches,
)


def test_full_pipeline():
    """Test the complete 17Track pipeline"""
    print("🚀 Testing Complete 17Track Pipeline")
    print("=" * 60)

    try:
        # Initialize client
        client = TrackingClient(API_TOKEN)
        print("✅ Client initialized successfully")

        # Test tracking numbers
        tracking_numbers = ["1Z005W760290052334", "1Z005W760390165201"]

        print(
            f"\n📦 Testing batch processing with {len(tracking_numbers)} tracking numbers..."
        )

        # Process in batches
        results, successful, failed = process_tracking_numbers_in_batches(
            tracking_numbers, client, DEFAULT_CARRIER_CODE, batch_size=40
        )

        print(f"✅ Batch processing complete:")
        print(f"   📊 Successful batches: {successful}")
        print(f"   ❌ Failed batches: {failed}")
        print(f"   📋 Total results: {len(results)}")

        if results:
            # Test CSV export
            print(f"\n📄 Testing CSV export...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"test_17track_results_{timestamp}.csv"
            csv_path = export_tracking_results_to_csv(results, csv_filename)
            print(f"✅ CSV exported to: {csv_path}")

            # Test status monitoring
            print(f"\n📊 Testing status monitoring...")
            monitor_results, status_summary = monitor_tracking_status_changes(
                client, tracking_numbers, DEFAULT_CARRIER_CODE
            )

            print(f"✅ Status monitoring complete:")
            print(f"   📦 Total tracked: {status_summary['total_tracked']}")
            print(f"   ✅ Successful queries: {status_summary['successful_queries']}")
            print(f"   ❌ Failed queries: {status_summary['failed_queries']}")
            print(f"   📊 Status counts: {status_summary['status_counts']}")

            # Show sample data structure
            print(f"\n🔍 Sample result structure:")
            if results and len(results) > 0:
                sample_result = results[0]
                print(f"   📋 Batch number: {sample_result.get('batch_number')}")
                print(f"   📦 Batch size: {sample_result.get('batch_size')}")
                print(f"   🕐 Timestamp: {sample_result.get('timestamp')}")

                # Show sample tracking data
                api_data = sample_result["result"].get("data", {})
                accepted_items = api_data.get("accepted", [])
                if accepted_items:
                    sample_item = accepted_items[0]
                    track_info = sample_item.get("track_info", {})
                    latest_status = track_info.get("latest_status", {})
                    print(f"   📋 Sample tracking:")
                    print(f"      🔢 Number: {sample_item.get('number')}")
                    print(f"      📊 Status: {latest_status.get('status')}")
                    print(f"      🏷️ Sub-status: {latest_status.get('sub_status')}")

            return True
        else:
            print("❌ No results to process")
            return False

    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_data_structure_compatibility():
    """Test that the data structure is compatible with existing patterns"""
    print("\n🔧 Testing Data Structure Compatibility")
    print("=" * 60)

    try:
        client = TrackingClient(API_TOKEN)
        tracking_numbers = ["1Z005W760290052334"]

        # Get a single result
        results, successful, failed = process_tracking_numbers_in_batches(
            tracking_numbers, client, DEFAULT_CARRIER_CODE, batch_size=1
        )

        if results and len(results) > 0:
            result = results[0]

            # Check expected structure
            required_keys = [
                "batch_number",
                "batch_size",
                "tracking_numbers",
                "result",
                "timestamp",
            ]
            missing_keys = [key for key in required_keys if key not in result]

            if missing_keys:
                print(f"❌ Missing required keys: {missing_keys}")
                return False
            else:
                print("✅ All required keys present in result structure")

            # Check API response structure
            api_data = result["result"].get("data", {})
            if "accepted" in api_data and "rejected" in api_data:
                print("✅ 17Track API response structure is correct")

                accepted_items = api_data.get("accepted", [])
                if accepted_items:
                    item = accepted_items[0]
                    if "number" in item and "track_info" in item:
                        print("✅ Tracking item structure is correct")
                        return True
                    else:
                        print("❌ Tracking item missing required fields")
                        return False
                else:
                    print("⚠️ No accepted tracking items found")
                    return True
            else:
                print("❌ Invalid 17Track API response structure")
                return False
        else:
            print("❌ No results to check")
            return False

    except Exception as e:
        print(f"❌ Compatibility test failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 17Track Pipeline Integration Test")
    print("=" * 60)

    # Run full pipeline test
    pipeline_success = test_full_pipeline()

    # Run compatibility test
    compatibility_success = test_data_structure_compatibility()

    print("\n" + "=" * 60)
    print("🎯 Test Summary:")
    print(f"✅ Pipeline test: {'PASSED' if pipeline_success else 'FAILED'}")
    print(f"✅ Compatibility test: {'PASSED' if compatibility_success else 'FAILED'}")

    if pipeline_success and compatibility_success:
        print("🎉 All tests passed! 17Track integration is working correctly.")
        print(
            "💡 The new tracking.py file is ready to use with the same interface as the original."
        )
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("❌ Some tests failed. Please check the errors above.")
        print("❌ Some tests failed. Please check the errors above.")
