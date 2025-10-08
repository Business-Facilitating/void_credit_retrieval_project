#!/usr/bin/env python3
"""
Manual Void Test - Interactive
This script will navigate to shipping history and wait for you to manually
click the three-dot button and void option, so we can observe the exact behavior.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.src.ups_web_login import UPSWebLoginAutomation
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def manual_void_test():
    """Manual test - navigate to shipping history and let user manually void"""
    
    print("=" * 70)
    print("🔍 Manual Void Test - Interactive")
    print("=" * 70)
    print("\nThis script will:")
    print("1. Login to UPS")
    print("2. Navigate to Shipping History")
    print("3. Wait for YOU to manually click the three-dot button")
    print("4. Wait for YOU to manually click Void")
    print("5. Observe what happens")
    print("=" * 70)
    
    input("\nPress Enter to continue...")
    
    try:
        with UPSWebLoginAutomation(headless=False) as ups_login:
            # Login
            print("\n🔐 Step 1: Logging in...")
            login_result = ups_login.login(save_screenshots=True)
            
            if not login_result['success']:
                print(f"❌ Login failed: {login_result['message']}")
                return
            
            print(f"✅ Login successful!")
            
            # Navigate to shipping history
            print("\n🚢 Step 2: Navigating to Shipping History...")
            nav_result = ups_login.navigate_to_shipping_history(save_screenshots=True)
            
            if not nav_result['success']:
                print(f"❌ Navigation failed: {nav_result['message']}")
                return
            
            print(f"✅ On Shipping History page!")
            
            # Wait for page to load
            print("\n⏳ Waiting for page to fully load...")
            ups_login.page.wait_for_timeout(5000)
            
            # Take screenshot
            ups_login.save_screenshot("manual_test_01_history_page")
            print("📸 Screenshot saved: manual_test_01_history_page")
            
            # Manual interaction
            print("\n" + "=" * 70)
            print("👆 MANUAL INTERACTION REQUIRED")
            print("=" * 70)
            print("\nPlease do the following:")
            print("1. Look for a shipment in the list")
            print("2. Find the three-dot button (⋮) in the Actions column")
            print("3. Click the three-dot button")
            print("4. Look for the 'Void' option in the menu")
            print("5. Tell me what you see!")
            print("\n⏸️  Browser will stay open for 2 minutes...")
            print("=" * 70)
            
            # Wait 2 minutes for manual interaction
            ups_login.page.wait_for_timeout(120000)
            
            # Take final screenshot
            ups_login.save_screenshot("manual_test_02_after_interaction")
            print("\n📸 Final screenshot saved: manual_test_02_after_interaction")
            
            print("\n" + "=" * 70)
            print("✅ Manual test complete!")
            print("=" * 70)
            print("\nPlease describe what happened:")
            print("- Where was the three-dot button?")
            print("- What did the menu look like?")
            print("- Was there a Void option?")
            print("- What happened when you clicked it?")
            print("=" * 70)
            
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)


if __name__ == "__main__":
    manual_void_test()

