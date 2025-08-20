#!/usr/bin/env python3
"""
Test script for the new 17Track API integration
"""

import os
import sys

# Add the parent directory to the path so we can import from src.src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.src.tracking_17 import API_TOKEN, DEFAULT_CARRIER_CODE, TrackingClient


def test_17track_basic():
    """Test basic 17Track API functionality"""
    print("🧪 Testing 17Track API Integration")
    print("=" * 50)

    try:
        # Initialize client
        client = TrackingClient(API_TOKEN)
        print("✅ Client initialized successfully")

        # Test single tracking number
        print("\n📦 Testing single tracking number...")
        tracking_number = "1Z005W760290052334"
        result = client.get_tracking_info(tracking_number, DEFAULT_CARRIER_CODE)

        if result:
            print(f"✅ Single tracking query successful!")
            print(f"   📊 Response keys: {list(result.keys())}")

            # Check if we have data
            data = result.get("data", [])
            print(f"   🔍 Data type: {type(data)}")
            print(f"   🔍 Data content: {data}")

            if data and isinstance(data, list):
                print(f"   📦 Found {len(data)} tracking records")
                for i, item in enumerate(data[:2]):  # Show first 2 items
                    print(
                        f"   📋 Item {i+1}: {item.get('number', 'Unknown')} - Status: {item.get('track', {}).get('status', 'Unknown')}"
                    )
            elif data:
                print(f"   📦 Found data (not a list): {data}")
            else:
                print("   ⚠️ No tracking data found in response")
        else:
            print("❌ Single tracking query failed")

        # Test batch tracking
        print("\n📦 Testing batch tracking...")
        tracking_numbers = ["1Z005W760290052334", "1Z005W760390165201"]
        batch_result = client.get_tracking_results_batch(
            tracking_numbers, DEFAULT_CARRIER_CODE
        )

        if batch_result:
            print(f"✅ Batch tracking query successful!")
            print(f"   📊 Response keys: {list(batch_result.keys())}")

            # Check if we have data
            data = batch_result.get("data", [])
            print(f"   🔍 Batch data type: {type(data)}")

            if data and isinstance(data, list):
                print(f"   📦 Found {len(data)} tracking records")
                for i, item in enumerate(data):
                    print(
                        f"   📋 Item {i+1}: {item.get('number', 'Unknown')} - Status: {item.get('track', {}).get('status', 'Unknown')}"
                    )
            elif data:
                print(f"   📦 Found data (not a list): {data}")
            else:
                print("   ⚠️ No tracking data found in response")
        else:
            print("❌ Batch tracking query failed")

        print("\n✅ Basic 17Track API test completed!")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_api_response_format():
    """Test and display the actual API response format"""
    print("\n🔍 Testing API Response Format")
    print("=" * 50)

    try:
        client = TrackingClient(API_TOKEN)
        tracking_number = "1Z005W760290052334"
        result = client.get_tracking_info(tracking_number, DEFAULT_CARRIER_CODE)

        if result:
            print("📋 Raw API Response Structure:")
            import json

            print(
                json.dumps(result, indent=2, default=str)[:1000] + "..."
                if len(str(result)) > 1000
                else json.dumps(result, indent=2, default=str)
            )
        else:
            print("❌ No response received")

    except Exception as e:
        print(f"❌ Error testing response format: {e}")


if __name__ == "__main__":
    # Run basic test
    success = test_17track_basic()

    if success:
        # Show response format
        test_api_response_format()

    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print(
        "✅ 17Track API integration test completed"
        if success
        else "❌ 17Track API integration test failed"
    )
    print("💡 Check the response format above to understand the data structure")
    print("💡 Check the response format above to understand the data structure")
    print("💡 Check the response format above to understand the data structure")
