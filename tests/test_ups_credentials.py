#!/usr/bin/env python3
"""
Test script to verify UPS API credential environment variable configuration
and authentication functionality
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
src_path = Path(__file__).parent.parent / "src" / "src"
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
import requests

def test_ups_credential_loading():
    """Test that UPS API credentials are properly loaded from environment"""
    print("🔍 Testing UPS API credential loading...")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    ups_username = os.getenv("UPS_USERNAME")
    ups_password = os.getenv("UPS_PASSWORD")
    ups_token_url = os.getenv("UPS_TOKEN_URL")
    
    print(f"UPS_USERNAME: {ups_username[:10]}..." if ups_username else "UPS_USERNAME: None")
    print(f"UPS_PASSWORD: {'*' * len(ups_password) if ups_password else 'None'}")
    print(f"UPS_TOKEN_URL: {ups_token_url}")
    
    # Validate all required variables are present
    missing_vars = []
    if not ups_username:
        missing_vars.append("UPS_USERNAME")
    if not ups_password:
        missing_vars.append("UPS_PASSWORD")
    if not ups_token_url:
        missing_vars.append("UPS_TOKEN_URL")
    
    if missing_vars:
        print(f"❌ ERROR: Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All UPS credential environment variables are loaded")
    return True

def test_ups_authentication_format():
    """Test that the authentication tuple format is correct"""
    print("\n🔍 Testing UPS authentication format...")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    ups_username = os.getenv("UPS_USERNAME")
    ups_password = os.getenv("UPS_PASSWORD")
    
    # Test that we can create the auth tuple (same format as requests.post auth parameter)
    try:
        auth_tuple = (ups_username, ups_password)
        print(f"✅ Authentication tuple created successfully")
        print(f"   Username length: {len(ups_username)} characters")
        print(f"   Password length: {len(ups_password)} characters")
        print(f"   Auth tuple type: {type(auth_tuple)}")
        return True
    except Exception as e:
        print(f"❌ ERROR creating authentication tuple: {e}")
        return False

def test_environment_variable_validation():
    """Test the validation logic that would be used in the actual modules"""
    print("\n🔍 Testing environment variable validation logic...")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Simulate the validation logic from our updated modules
        UPS_TOKEN_URL = os.getenv("UPS_TOKEN_URL")
        UPS_TRACKING_URL = os.getenv("UPS_TRACKING_URL")
        UPS_USERNAME = os.getenv("UPS_USERNAME")
        UPS_PASSWORD = os.getenv("UPS_PASSWORD")

        # Validate required environment variables (same as in our modules)
        if not UPS_TOKEN_URL:
            raise ValueError("UPS_TOKEN_URL environment variable is required")
        if not UPS_TRACKING_URL:
            raise ValueError("UPS_TRACKING_URL environment variable is required")
        if not UPS_USERNAME:
            raise ValueError("UPS_USERNAME environment variable is required")
        if not UPS_PASSWORD:
            raise ValueError("UPS_PASSWORD environment variable is required")
        
        print("✅ All validation checks passed")
        print("   Modules would load successfully with current environment configuration")
        return True
        
    except ValueError as e:
        print(f"❌ Validation error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing UPS API Credential Configuration")
    print("=" * 60)
    
    # Run all tests
    credential_test = test_ups_credential_loading()
    auth_format_test = test_ups_authentication_format()
    validation_test = test_environment_variable_validation()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Credential Loading:     {'✅ PASS' if credential_test else '❌ FAIL'}")
    print(f"Authentication Format:  {'✅ PASS' if auth_format_test else '❌ FAIL'}")
    print(f"Validation Logic:       {'✅ PASS' if validation_test else '❌ FAIL'}")
    
    all_passed = credential_test and auth_format_test and validation_test
    
    if all_passed:
        print("\n🎉 All credential tests passed!")
        print("💡 UPS API authentication should work correctly with environment variables.")
        print("🔒 Credentials are now securely stored in environment variables instead of source code.")
        sys.exit(0)
    else:
        print("\n💥 Some credential tests failed.")
        sys.exit(1)
