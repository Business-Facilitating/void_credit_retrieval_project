#!/usr/bin/env python3
"""
Test script for UPS Web Login Automation
=========================================

This script tests the UPS web login automation functionality including:
- Environment variable validation
- Browser initialization
- Login flow execution
- Error handling
- Screenshot capture

Usage:
    # Run the test
    poetry run python tests/test_ups_web_login.py
    
    # Run with visible browser (non-headless)
    poetry run python tests/test_ups_web_login.py --headed

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_environment_variables():
    """Test that required environment variables are set"""
    print("🔍 Testing UPS Web Login environment variables...")
    print("=" * 60)
    
    required_vars = {
        'UPS_WEB_USERNAME': os.getenv('UPS_WEB_USERNAME'),
        'UPS_WEB_PASSWORD': os.getenv('UPS_WEB_PASSWORD'),
        'UPS_WEB_LOGIN_URL': os.getenv('UPS_WEB_LOGIN_URL', 'https://www.ups.com/lasso/login')
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if var_value:
            if 'PASSWORD' in var_name:
                print(f"✅ {var_name}: {'*' * len(var_value)}")
            elif 'USERNAME' in var_name:
                print(f"✅ {var_name}: {var_value[:10]}...")
            else:
                print(f"✅ {var_name}: {var_value}")
        else:
            print(f"❌ {var_name}: Not set")
            missing_vars.append(var_name)
    
    if missing_vars:
        print(f"\n❌ ERROR: Missing environment variables: {', '.join(missing_vars)}")
        print("\n💡 To fix this:")
        print("   1. Copy .env.example to .env")
        print("   2. Add your UPS web credentials:")
        print("      UPS_WEB_USERNAME=your_username")
        print("      UPS_WEB_PASSWORD=your_password")
        return False
    
    print("\n✅ All required environment variables are set")
    return True


def test_playwright_installation():
    """Test that Playwright is installed and browsers are available"""
    print("\n🔍 Testing Playwright installation...")
    print("=" * 60)
    
    try:
        from playwright.sync_api import sync_playwright
        print("✅ Playwright module imported successfully")
        
        # Try to start playwright
        with sync_playwright() as p:
            print("✅ Playwright started successfully")
            
            # Check available browsers
            browsers = []
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                browsers.append("Chromium")
                print("✅ Chromium browser available")
            except Exception as e:
                print(f"⚠️ Chromium not available: {e}")
            
            if browsers:
                print(f"\n✅ Available browsers: {', '.join(browsers)}")
                return True
            else:
                print("\n❌ No browsers available")
                print("\n💡 To install Playwright browsers:")
                print("   poetry run playwright install chromium")
                return False
                
    except ImportError as e:
        print(f"❌ Playwright not installed: {e}")
        print("\n💡 To install Playwright:")
        print("   poetry add playwright")
        print("   poetry run playwright install chromium")
        return False
    except Exception as e:
        print(f"❌ Playwright test failed: {e}")
        return False


def test_ups_login_automation(headless: bool = True):
    """Test the UPS login automation"""
    print("\n🔍 Testing UPS login automation...")
    print("=" * 60)
    
    try:
        from src.src.ups_web_login import UPSWebLoginAutomation
        print("✅ UPSWebLoginAutomation imported successfully")
        
        # Create automation instance
        print(f"\n🚀 Initializing automation (headless={headless})...")
        with UPSWebLoginAutomation(headless=headless) as ups_login:
            print("✅ Automation initialized successfully")
            
            # Perform login
            print("\n🔐 Attempting login...")
            result = ups_login.login(save_screenshots=True)
            
            # Display results
            print("\n" + "=" * 60)
            print("📊 LOGIN TEST RESULT")
            print("=" * 60)
            print(f"Success: {'✅ YES' if result['success'] else '❌ NO'}")
            print(f"Message: {result['message']}")
            print(f"Final URL: {result['url']}")
            if result['screenshot']:
                print(f"Screenshot: {result['screenshot']}")
            
            return result['success']
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Make sure the ups_web_login.py module exists in src/src/")
        return False
    except Exception as e:
        print(f"❌ Login automation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description='Test UPS Web Login Automation')
    parser.add_argument(
        '--headed',
        action='store_true',
        help='Run browser in headed mode (visible browser window)'
    )
    parser.add_argument(
        '--skip-login',
        action='store_true',
        help='Skip the actual login test (only test environment and installation)'
    )
    args = parser.parse_args()
    
    print("🚀 UPS Web Login Automation Test Suite")
    print("=" * 60)
    
    # Track test results
    results = {}
    
    # Test 1: Environment variables
    results['environment'] = test_environment_variables()
    
    # Test 2: Playwright installation
    results['playwright'] = test_playwright_installation()
    
    # Test 3: Login automation (if not skipped)
    if not args.skip_login and results['environment'] and results['playwright']:
        headless = not args.headed
        results['login'] = test_ups_login_automation(headless=headless)
    elif args.skip_login:
        print("\n⏭️ Skipping login test (--skip-login flag)")
        results['login'] = None
    else:
        print("\n⏭️ Skipping login test (prerequisites not met)")
        results['login'] = None
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Environment Variables: {'✅ PASS' if results['environment'] else '❌ FAIL'}")
    print(f"Playwright Installation: {'✅ PASS' if results['playwright'] else '❌ FAIL'}")
    if results['login'] is not None:
        print(f"Login Automation: {'✅ PASS' if results['login'] else '❌ FAIL'}")
    else:
        print(f"Login Automation: ⏭️ SKIPPED")
    
    # Overall result
    all_tests = [v for v in results.values() if v is not None]
    all_passed = all(all_tests) if all_tests else False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

