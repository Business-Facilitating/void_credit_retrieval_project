#!/usr/bin/env python3
"""
Test script to verify UPS API environment variable configuration
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
src_path = Path(__file__).parent.parent / "src" / "src"
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv


def test_env_variables():
    """Test that UPS API environment variables are properly loaded"""
    print("🔍 Testing UPS API environment variable configuration...")
    print("=" * 60)

    # Load environment variables
    load_dotenv()

    # Check UPS API URLs
    ups_token_url = os.getenv("UPS_TOKEN_URL")
    ups_tracking_url = os.getenv("UPS_TRACKING_URL")
    ups_username = os.getenv("UPS_USERNAME")
    ups_password = os.getenv("UPS_PASSWORD")

    print(f"UPS_TOKEN_URL: {ups_token_url}")
    print(f"UPS_TRACKING_URL: {ups_tracking_url}")
    print(
        f"UPS_USERNAME: {ups_username[:10]}..."
        if ups_username
        else "UPS_USERNAME: None"
    )
    print(f"UPS_PASSWORD: {'*' * len(ups_password) if ups_password else 'None'}")

    # Validate URLs
    if not ups_token_url:
        print("❌ ERROR: UPS_TOKEN_URL environment variable is not set")
        return False

    if not ups_tracking_url:
        print("❌ ERROR: UPS_TRACKING_URL environment variable is not set")
        return False

    # Validate credentials
    if not ups_username:
        print("❌ ERROR: UPS_USERNAME environment variable is not set")
        return False

    if not ups_password:
        print("❌ ERROR: UPS_PASSWORD environment variable is not set")
        return False

    # Check if URLs look correct
    expected_token_url = "https://onlinetools.ups.com/security/v1/oauth/token"
    expected_tracking_url = "https://onlinetools.ups.com/api/track/v1/details/"

    if ups_token_url != expected_token_url:
        print(f"⚠️  WARNING: UPS_TOKEN_URL doesn't match expected value")
        print(f"   Expected: {expected_token_url}")
        print(f"   Actual:   {ups_token_url}")

    if ups_tracking_url != expected_tracking_url:
        print(f"⚠️  WARNING: UPS_TRACKING_URL doesn't match expected value")
        print(f"   Expected: {expected_tracking_url}")
        print(f"   Actual:   {ups_tracking_url}")

    # Check credential format (UPS usernames are typically long alphanumeric strings)
    if len(ups_username) < 20:
        print(
            f"⚠️  WARNING: UPS_USERNAME seems unusually short: {len(ups_username)} characters"
        )

    if len(ups_password) < 20:
        print(
            f"⚠️  WARNING: UPS_PASSWORD seems unusually short: {len(ups_password)} characters"
        )

    print("✅ All UPS API environment variables are properly configured!")
    return True


def test_import_modules():
    """Test that our updated modules can be imported without errors"""
    print("\n🔍 Testing module imports...")
    print("=" * 60)

    try:
        # Test importing ups_label_only_filter (this will validate env vars)
        print("📦 Importing ups_label_only_filter...")
        import ups_label_only_filter

        print("✅ ups_label_only_filter imported successfully")

        # Check that the URLs and credentials are loaded correctly
        print(f"   UPS_TOKEN_URL: {ups_label_only_filter.UPS_TOKEN_URL}")
        print(f"   UPS_TRACKING_URL: {ups_label_only_filter.UPS_TRACKING_URL}")
        print(f"   UPS_USERNAME: {ups_label_only_filter.UPS_USERNAME[:10]}...")
        print(f"   UPS_PASSWORD: {'*' * len(ups_label_only_filter.UPS_PASSWORD)}")

        return True

    except Exception as e:
        print(f"❌ ERROR importing modules: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting UPS API Environment Configuration Test")
    print("=" * 60)

    # Test environment variables
    env_test_passed = test_env_variables()

    # Test module imports
    import_test_passed = test_import_modules()

    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Environment Variables: {'✅ PASS' if env_test_passed else '❌ FAIL'}")
    print(f"Module Imports:        {'✅ PASS' if import_test_passed else '❌ FAIL'}")

    if env_test_passed and import_test_passed:
        print("\n🎉 All tests passed! UPS API configuration is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the configuration.")
        sys.exit(1)
        sys.exit(1)
