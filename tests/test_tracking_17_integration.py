#!/usr/bin/env python3
"""
17Track API Integration Tests and Demos
=======================================

Test, debug, and explore script for the 17Track API integration module.
Contains comprehensive tests for API methods, monitoring features, and pipeline functionality.

This file contains the test, debug, and exploration functions that were moved from tracking_17.py
to keep the main module clean and focused on core functionality.

Usage:
    # Run all tests and demos
    poetry run python tests/test_tracking_17_integration.py

    # Run individual test functions
    from tests.test_tracking_17_integration import test_api_methods
    test_api_methods()

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import os
import sys
from datetime import datetime

# Add the parent directory to the path to import from src.src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.src.tracking_17 import (
    API_TOKEN,
    DEFAULT_CARRIER_CODE,
    TrackingClient,
    export_status_monitoring_summary,
    export_tracking_results_to_csv,
    generate_date_range_iso,
    main_duckdb_tracking_pipeline,
    monitor_tracking_status_changes,
    query_tracking_by_date_range,
)


def test_api_methods():
    """Test individual API methods including new monitoring features"""
    # Use the API token from the existing project configuration
    api_token = API_TOKEN

    print("🧪 Testing 17Track API methods...")

    try:
        # Initialize client
        client = TrackingClient(api_token)

        # Test 1: Query single tracking number
        print("\n1️⃣ Testing single tracking query...")
        single_result = client.get_tracking_info(
            ["1Z005W760290052334"], DEFAULT_CARRIER_CODE
        )
        if single_result:
            print("✅ Single tracking query successful")
            print(f"   📦 Response: {single_result}")

        # Test 2: Batch query with multiple tracking numbers
        print("\n2️⃣ Testing batch tracking query...")
        test_tracking_numbers = [
            "1Z005W760290052334",
            "1Z005W760390165201",
        ]  # Using the known working tracking numbers
        batch_result = client.get_tracking_results_batch(
            test_tracking_numbers, DEFAULT_CARRIER_CODE
        )
        if batch_result:
            print("✅ Batch tracking query successful")
            print(f"   📦 Found {len(batch_result.get('data', []))} tracking results")

        # Test 3: Note about unsupported features
        print("\n3️⃣ Unsupported features:")
        print("   ⚠️ Date range queries not supported by 17Track API")
        print("   ⚠️ Carrier-wide queries not supported by 17Track API")

        # Test 4: Status monitoring
        print("\n4️⃣ Testing status monitoring...")
        results, status_summary = monitor_tracking_status_changes(
            client, test_tracking_numbers, DEFAULT_CARRIER_CODE
        )
        if results and status_summary:
            print(f"✅ Status monitoring successful")
            print(f"   📊 Status counts: {status_summary['status_counts']}")

            # Export status summary
            summary_path = export_status_monitoring_summary(status_summary)
            print(f"   📋 Summary exported to: {os.path.basename(summary_path)}")

    except Exception as e:
        print(f"❌ API test failed: {e}")


def demonstrate_monitoring_features():
    """Demonstrate the new tracking status monitoring features"""
    # Use the API token from the existing project configuration
    api_token = API_TOKEN

    print("🎯 Demonstrating 17Track Status Monitoring Features...")

    try:
        # Initialize client
        client = TrackingClient(api_token)

        # Demo 1: Query tracking data for last 7 days (not supported)
        print("\n📅 Demo 1: Query tracking data for last 7 days...")
        csv_path = query_tracking_by_date_range(
            client, days_back=7, carrier_code=DEFAULT_CARRIER_CODE
        )
        print("⚠️ Date range queries not supported by 17Track API")

        # Demo 2: Monitor status of specific tracking numbers
        print("\n📊 Demo 2: Monitor status of specific tracking numbers...")
        test_tracking_numbers = ["1Z005W760290052334", "1Z005W760390165201"]
        results, status_summary = monitor_tracking_status_changes(
            client, test_tracking_numbers, DEFAULT_CARRIER_CODE
        )

        if results and status_summary:
            print(f"✅ Monitoring complete!")
            print(f"   📦 Total tracked: {status_summary['total_tracked']}")
            print(f"   ✅ Successful queries: {status_summary['successful_queries']}")
            print(f"   ❌ Failed queries: {status_summary['failed_queries']}")
            print(f"   📊 Status breakdown: {status_summary['status_counts']}")

            # Export detailed results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = export_tracking_results_to_csv(
                results, f"monitoring_demo_{timestamp}.csv"
            )
            summary_path = export_status_monitoring_summary(
                status_summary, f"monitoring_summary_demo_{timestamp}.json"
            )

            print(f"   📄 Detailed results: {os.path.basename(csv_path)}")
            print(f"   📋 Summary report: {os.path.basename(summary_path)}")

        # Demo 3: Generate date ranges for different periods
        print("\n📆 Demo 3: Date range generation examples...")
        for days in [1, 7, 30]:
            start, end = generate_date_range_iso(days)
            print(f"   Last {days} day(s): {start} to {end}")

    except Exception as e:
        print(f"❌ Demo failed: {e}")


def run_main_pipeline_demo():
    """Run the main DuckDB to 17Track pipeline as a demo"""
    print("🚀 DuckDB to 17Track Pipeline Demo")
    print("=" * 60)

    # Use the API token from the existing project configuration
    api_token = API_TOKEN

    # Run the main DuckDB pipeline
    result_files = main_duckdb_tracking_pipeline(
        limit=30,  # Extract up to 30 tracking numbers
        api_token=api_token,
        carrier_code=DEFAULT_CARRIER_CODE,
        export_json=True,
        export_csv=True,
    )

    if result_files:
        print(f"🎉 Pipeline completed successfully!")
        print("📄 Results saved to:")
        for file_type, file_path in result_files.items():
            print(f"   • {file_type.upper()}: {os.path.basename(file_path)}")
    else:
        print("❌ Pipeline failed or no results to export")
        print("💡 Check the logs above for details")

    print("\n" + "=" * 60)
    print("💡 Available test functions:")
    print("   - test_api_methods() for API testing")
    print("   - demonstrate_monitoring_features() for monitoring demos")
    print("   - run_main_pipeline_demo() for pipeline testing")


if __name__ == "__main__":
    # Run all test and demo functions
    print("🧪 17Track Integration Tests and Demos")
    print("=" * 60)

    # Run API method tests
    test_api_methods()

    print("\n" + "=" * 60)

    # Run monitoring feature demos
    demonstrate_monitoring_features()

    print("\n" + "=" * 60)

    # Run main pipeline demo
    run_main_pipeline_demo()
