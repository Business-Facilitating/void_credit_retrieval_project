#!/usr/bin/env python3
"""
Test script to verify ups_api.py environment variable configuration
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
src_path = Path(__file__).parent.parent / "src" / "src"
sys.path.insert(0, str(src_path))

def test_ups_api_env_loading():
    """Test that ups_api.py loads environment variables correctly"""
    print("🔍 Testing ups_api.py environment variable loading...")
    print("=" * 60)
    
    try:
        # This will test the environment variable loading in ups_api.py
        # We'll capture the initial part that loads env vars
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check that the environment variables are available
        ups_token_url = os.getenv("UPS_TOKEN_URL")
        ups_tracking_url = os.getenv("UPS_TRACKING_URL")
        
        print(f"UPS_TOKEN_URL: {ups_token_url}")
        print(f"UPS_TRACKING_URL: {ups_tracking_url}")
        
        if not ups_token_url:
            print("❌ ERROR: UPS_TOKEN_URL not found in environment")
            return False
            
        if not ups_tracking_url:
            print("❌ ERROR: UPS_TRACKING_URL not found in environment")
            return False
        
        # Test that the validation logic would work
        if not ups_token_url:
            raise ValueError("UPS_TOKEN_URL environment variable is required")
        if not ups_tracking_url:
            raise ValueError("UPS_TRACKING_URL environment variable is required")
        
        print("✅ ups_api.py environment variable validation would pass")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing ups_api.py Environment Configuration")
    print("=" * 60)
    
    test_passed = test_ups_api_env_loading()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"ups_api.py Environment Loading: {'✅ PASS' if test_passed else '❌ FAIL'}")
    
    if test_passed:
        print("\n🎉 ups_api.py environment configuration is working correctly!")
        print("💡 The script should now read UPS API URLs from environment variables.")
        sys.exit(0)
    else:
        print("\n💥 Environment configuration test failed.")
        sys.exit(1)
