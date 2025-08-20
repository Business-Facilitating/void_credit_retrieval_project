#!/usr/bin/env python3
"""
Test script demonstrating the exact trackingmore SDK usage pattern
"""

import trackingmore
from trackingmore.exception import TrackingMoreException

# Set API key
trackingmore.api_key = '6i1yot9f-802k-he7c-iv03-mduqzvgi9bh2'

def test_single_tracking_numbers():
    """Test with single tracking numbers"""
    print("🧪 Testing single tracking numbers...")
    
    try:
        # Test with known working tracking numbers
        params = {
            'tracking_numbers': '1Z005W760290052334,1Z005W760390165201', 
            'courier_code': 'ups'
        }
        result = trackingmore.tracking.get_tracking_results(params)
        print("✅ Success!")
        print(f"📊 Found {len(result.get('data', []))} tracking records")
        
        # Print tracking statuses
        for item in result.get('data', []):
            tracking_num = item.get('tracking_number', 'Unknown')
            status = item.get('delivery_status', 'Unknown')
            destination = f"{item.get('destination_city', '')}, {item.get('destination_state', '')}"
            print(f"   📦 {tracking_num}: {status} → {destination}")
            
    except TrackingMoreException as ce:
        print(f"❌ TrackingMore Exception: {ce}")
    except Exception as e:
        print(f"❌ Other error: {e}")

def test_batch_tracking_numbers():
    """Test with larger batch of tracking numbers"""
    print("\n🧪 Testing batch tracking numbers...")
    
    try:
        # Test with multiple tracking numbers from our database
        tracking_numbers = [
            '1Z005W760290052334',
            '1Z005W760390165201', 
            '1Z005W760390186411',
            '1Z005W760390008309',
            '1Z005W760390012992'
        ]
        
        params = {
            'tracking_numbers': ','.join(tracking_numbers), 
            'courier_code': 'ups'
        }
        result = trackingmore.tracking.get_tracking_results(params)
        print("✅ Success!")
        print(f"📊 Requested {len(tracking_numbers)} tracking numbers")
        print(f"📊 Found {len(result.get('data', []))} tracking records")
        
        # Print tracking statuses
        for item in result.get('data', []):
            tracking_num = item.get('tracking_number', 'Unknown')
            status = item.get('delivery_status', 'Unknown')
            latest_event = item.get('latest_event', 'No events')
            print(f"   📦 {tracking_num}: {status}")
            print(f"      🔄 Latest: {latest_event}")
            
    except TrackingMoreException as ce:
        print(f"❌ TrackingMore Exception: {ce}")
    except Exception as e:
        print(f"❌ Other error: {e}")

def test_courier_only():
    """Test querying by courier only"""
    print("\n🧪 Testing courier-only query...")
    
    try:
        params = {'courier_code': 'ups'}
        result = trackingmore.tracking.get_tracking_results(params)
        print("✅ Success!")
        print(f"📊 Found {len(result.get('data', []))} UPS tracking records")
        
        # Show first few results
        for i, item in enumerate(result.get('data', [])[:3]):
            tracking_num = item.get('tracking_number', 'Unknown')
            status = item.get('delivery_status', 'Unknown')
            print(f"   {i+1}. 📦 {tracking_num}: {status}")
            
        if len(result.get('data', [])) > 3:
            print(f"   ... and {len(result.get('data', [])) - 3} more records")
            
    except TrackingMoreException as ce:
        print(f"❌ TrackingMore Exception: {ce}")
    except Exception as e:
        print(f"❌ Other error: {e}")

if __name__ == "__main__":
    print("🚀 TrackingMore SDK Test Script")
    print("=" * 50)
    
    # Run all tests
    test_single_tracking_numbers()
    test_batch_tracking_numbers()
    test_courier_only()
    
    print("\n🎯 All tests completed!")
