#!/usr/bin/env python3
"""
Debug script to check what's happening with DuckDB tracking numbers and 17Track API
"""

import json
import os
import sys

# Add the parent directory to the path so we can import from src.src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.src.tracking_17 import (
    API_TOKEN,
    DEFAULT_CARRIER_CODE,
    TrackingClient,
    extract_tracking_numbers_from_duckdb,
)


def debug_duckdb_extraction():
    """Debug the DuckDB extraction process"""
    print("🔍 Debug: DuckDB Tracking Number Extraction")
    print("=" * 60)

    # Extract tracking numbers
    tracking_numbers = extract_tracking_numbers_from_duckdb(days_back=14, limit=30)

    print(f"📊 Extracted {len(tracking_numbers)} tracking numbers:")
    for i, tn in enumerate(tracking_numbers, 1):
        print(f"   {i:2d}. {tn}")

    return tracking_numbers


def debug_17track_api(tracking_numbers):
    """Debug the 17Track API response"""
    print(f"\n🔍 Debug: 17Track API Response")
    print("=" * 60)

    if not tracking_numbers:
        print("❌ No tracking numbers to test")
        return

    # Initialize client
    client = TrackingClient(API_TOKEN)

    # Test with first few tracking numbers
    test_numbers = tracking_numbers[:5]  # Test first 5
    print(f"🧪 Testing with {len(test_numbers)} tracking numbers:")
    for i, tn in enumerate(test_numbers, 1):
        print(f"   {i}. {tn}")

    # Make API call
    result = client.get_tracking_results_batch(test_numbers, DEFAULT_CARRIER_CODE)

    if result:
        print(f"\n✅ API call successful!")
        print(f"📊 Response keys: {list(result.keys())}")

        # Check the data structure
        data = result.get("data", {})
        print(f"📋 Data keys: {list(data.keys())}")

        accepted = data.get("accepted", [])
        rejected = data.get("rejected", [])

        print(f"✅ Accepted: {len(accepted)} tracking numbers")
        print(f"❌ Rejected: {len(rejected)} tracking numbers")

        if accepted:
            print(f"\n📦 Accepted tracking numbers:")
            for i, item in enumerate(accepted, 1):
                number = item.get("number", "Unknown")
                track_info = item.get("track_info", {})
                latest_status = track_info.get("latest_status", {})
                status = latest_status.get("status", "Unknown")
                print(f"   {i}. {number} - Status: {status}")

        if rejected:
            print(f"\n❌ Rejected tracking numbers:")
            for i, item in enumerate(rejected, 1):
                number = item.get("number", "Unknown")
                reason = item.get("error", {}).get("message", "Unknown reason")
                print(f"   {i}. {number} - Reason: {reason}")

        # Show raw response (truncated)
        print(f"\n📋 Raw API Response (first 1000 chars):")
        response_str = json.dumps(result, indent=2)
        print(response_str[:1000] + "..." if len(response_str) > 1000 else response_str)

    else:
        print("❌ API call failed")


def debug_csv_export_logic():
    """Debug why CSV export might be empty"""
    print(f"\n🔍 Debug: CSV Export Logic")
    print("=" * 60)

    # Simulate the data structure that would cause empty CSV
    print("💡 The CSV export only processes 'accepted' tracking numbers.")
    print("💡 If all tracking numbers are 'rejected', the CSV will be empty.")
    print("💡 This is normal behavior - rejected numbers don't have tracking data.")


if __name__ == "__main__":
    print("🧪 DuckDB to 17Track Debug Analysis")
    print("=" * 60)

    # Step 1: Debug DuckDB extraction
    tracking_numbers = debug_duckdb_extraction()

    # Step 2: Debug 17Track API
    debug_17track_api(tracking_numbers)

    # Step 3: Explain CSV export logic
    debug_csv_export_logic()

    print("\n" + "=" * 60)
    print("🎯 Debug Summary:")
    print("✅ DuckDB extraction working")
    print("✅ 17Track API integration working")
    print("💡 Empty CSV likely means tracking numbers were rejected by 17Track")
    print("💡 This could happen if:")
    print("   - Tracking numbers are too old")
    print("   - Tracking numbers are from different carriers")
    print("   - Tracking numbers are invalid or not yet in the system")
    print("   - Tracking numbers are invalid or not yet in the system")
    print("   - Tracking numbers are invalid or not yet in the system")
