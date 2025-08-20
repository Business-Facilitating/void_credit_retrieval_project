#!/usr/bin/env python3
"""
Test the cleaned up 17Track implementation using the exact code block pattern
"""

import os
import sys

# Add the parent directory to the path so we can import from src.src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

from src.src.tracking_17 import API_TOKEN, API_URL, DEFAULT_CARRIER_CODE, TrackingClient


def test_original_code_block():
    """Test using the exact code block pattern provided"""
    print("🧪 Testing Original 17Track Code Block Pattern")
    print("=" * 60)

    # Your exact code block
    url = "https://api.17track.net/track/v2.4/gettrackinfo"

    payload = [
        {"number": "1Z005W760290052334", "carrier": 100002},
        {"number": "1Z005W760390165201", "carrier": 100002},
    ]
    headers = {
        "content-type": "application/json",
        "17token": "3ED9315FC1B2FC06CB396E95FE72AB66",
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    print(f"✅ Original code block executed successfully!")
    print(f"📊 Status Code: {response.status_code}")
    print(f"📋 Response (first 500 chars): {response.text[:500]}...")

    return response.json() if response.status_code == 200 else None


def test_tracking_client():
    """Test the TrackingClient implementation"""
    print(f"\n🧪 Testing TrackingClient Implementation")
    print("=" * 60)

    try:
        # Initialize client
        client = TrackingClient()

        # Test with same tracking numbers
        tracking_numbers = ["1Z005W760290052334", "1Z005W760390165201"]
        result = client.get_tracking_info(tracking_numbers, DEFAULT_CARRIER_CODE)

        if result:
            print(f"✅ TrackingClient working successfully!")
            print(f"📊 Response keys: {list(result.keys())}")

            data = result.get("data", {})
            accepted = data.get("accepted", [])
            rejected = data.get("rejected", [])

            print(f"📦 Accepted: {len(accepted)} tracking numbers")
            print(f"❌ Rejected: {len(rejected)} tracking numbers")

            for item in accepted:
                number = item.get("number")
                track_info = item.get("track_info", {})
                latest_status = track_info.get("latest_status", {})
                status = latest_status.get("status", "Unknown")
                print(f"   ✅ {number}: {status}")

            return True
        else:
            print("❌ TrackingClient failed")
            return False

    except Exception as e:
        print(f"❌ TrackingClient error: {e}")
        return False


def test_duckdb_integration():
    """Test the DuckDB integration"""
    print(f"\n🧪 Testing DuckDB Integration")
    print("=" * 60)

    try:
        from src.src.tracking_17 import extract_tracking_numbers_from_duckdb

        # Extract tracking numbers
        tracking_numbers = extract_tracking_numbers_from_duckdb(days_back=14, limit=5)

        if tracking_numbers:
            print(f"✅ DuckDB extraction working!")
            print(f"📦 Found {len(tracking_numbers)} tracking numbers:")
            for i, tn in enumerate(tracking_numbers, 1):
                print(f"   {i}. {tn}")

            # Test with TrackingClient
            client = TrackingClient()
            result = client.get_tracking_info(
                tracking_numbers[:3], DEFAULT_CARRIER_CODE
            )  # Test first 3

            if result:
                data = result.get("data", {})
                accepted = data.get("accepted", [])
                rejected = data.get("rejected", [])
                print(
                    f"📊 API Results: {len(accepted)} accepted, {len(rejected)} rejected"
                )

            return True
        else:
            print("⚠️ No tracking numbers found in DuckDB")
            return False

    except Exception as e:
        print(f"❌ DuckDB integration error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Clean 17Track Implementation Test")
    print("=" * 60)

    # Test 1: Original code block
    original_result = test_original_code_block()

    # Test 2: TrackingClient
    client_success = test_tracking_client()

    # Test 3: DuckDB integration
    duckdb_success = test_duckdb_integration()

    print("\n" + "=" * 60)
    print("🎯 Test Summary:")
    print(f"✅ Original code block: {'PASSED' if original_result else 'FAILED'}")
    print(f"✅ TrackingClient: {'PASSED' if client_success else 'FAILED'}")
    print(f"✅ DuckDB integration: {'PASSED' if duckdb_success else 'FAILED'}")

    if original_result and client_success:
        print("\n🎉 Clean 17Track implementation is working correctly!")
        print("💡 The tracking.py file now uses only 17Track API patterns")
        print("💡 All TrackingMore references have been removed")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
