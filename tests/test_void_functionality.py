#!/usr/bin/env python3
"""
Test Void Functionality
This script tests the complete void workflow without actually voiding
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

from src.src.ups_web_login import UPSWebLoginAutomation

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_void_workflow():
    """Test the void workflow up to the point of clicking void"""

    print("=" * 70)
    print("🧪 Testing Void Functionality")
    print("=" * 70)
    print("\nThis test will:")
    print("1. Login to UPS")
    print("2. Navigate to Shipping History")
    print("3. Find three-dot action buttons")
    print("4. Click the first three-dot button")
    print("5. Look for Void option in menu")
    print("6. Show you the menu (but NOT click void)")
    print("=" * 70)

    try:
        with UPSWebLoginAutomation(headless=False) as ups_login:
            # Step 1: Login
            print("\n📝 Step 1: Logging in...")
            login_result = ups_login.login(save_screenshots=True)

            if not login_result["success"]:
                print(f"❌ Login failed: {login_result['message']}")
                return False

            print(f"✅ Login successful!")

            # Step 2: Navigate to shipping history
            print("\n📝 Step 2: Navigating to Shipping History...")
            nav_result = ups_login.navigate_to_shipping_history(save_screenshots=True)

            if not nav_result["success"]:
                print(f"❌ Navigation failed: {nav_result['message']}")
                return False

            print(f"✅ On Shipping History page!")

            # Step 3: Wait for page to load
            print("\n📝 Step 3: Waiting for page to load...")
            ups_login.page.wait_for_timeout(5000)
            print("✅ Page loaded")

            # Step 4: Find action menu buttons
            print("\n📝 Step 4: Looking for Action Menu buttons...")

            selectors_to_try = [
                'tbody tr button:has-text("Action Menu")',
                "button.ups-btn_standalone_icon",
                "tbody tr button",
            ]

            action_buttons = []
            for selector in selectors_to_try:
                try:
                    elements = ups_login.page.query_selector_all(selector)
                    visible = [e for e in elements if e.is_visible()]
                    if visible:
                        print(f"   ✅ Found {len(visible)} buttons with: {selector}")
                        action_buttons = visible
                        break
                except:
                    print(f"   ❌ Selector failed: {selector}")

            if not action_buttons:
                print("❌ Could not find any three-dot buttons")
                print("   Taking screenshot for inspection...")
                ups_login.save_screenshot("test_void_no_buttons_found")
                ups_login.page.wait_for_timeout(30000)
                return False

            print(f"✅ Found {len(action_buttons)} three-dot action buttons")

            # Step 5: Click first button
            print("\n📝 Step 5: Clicking first three-dot button...")
            first_button = action_buttons[0]
            first_button.click()
            print("✅ Clicked three-dot button")

            # Wait for menu
            print("   Waiting for menu to appear...")
            ups_login.page.wait_for_timeout(2000)

            # Take screenshot of menu
            ups_login.save_screenshot("test_void_menu_opened")
            print("📸 Screenshot saved: test_void_menu_opened")

            # Step 6: Look for Void option
            print("\n📝 Step 6: Looking for Void option in menu...")

            void_selectors = [
                'a:has-text("Void")',
                'button:has-text("Void")',
                'li a:has-text("Void")',
            ]

            void_found = False
            for selector in void_selectors:
                try:
                    void_element = ups_login.page.query_selector(selector)
                    if void_element and void_element.is_visible():
                        print(f"   ✅ Found Void option: {selector}")
                        void_found = True
                        break
                except:
                    print(f"   ❌ Selector failed: {selector}")

            if void_found:
                print("\n" + "=" * 70)
                print("🎉 SUCCESS! Void option found in menu!")
                print("=" * 70)
                print("\n✅ All components working:")
                print("   ✅ Login")
                print("   ✅ Navigation to Shipping History")
                print("   ✅ Three-dot button found and clicked")
                print("   ✅ Menu opened")
                print("   ✅ Void option found")
                print("\n📸 Check screenshot: test_void_menu_opened")
                print("\n⏸️  Browser will stay open for 30 seconds...")
                print("=" * 70)

                ups_login.page.wait_for_timeout(30000)
                return True
            else:
                print("\n❌ Void option NOT found in menu")
                print("   Taking screenshot for inspection...")
                ups_login.save_screenshot("test_void_option_not_found")

                # List all visible text
                print("\n   Visible menu items:")
                try:
                    menu_items = ups_login.page.query_selector_all("a, button")
                    for i, item in enumerate(menu_items[:20], 1):
                        if item.is_visible():
                            text = item.inner_text().strip()
                            if text:
                                print(f"      {i}. {text}")
                except:
                    pass

                print("\n⏸️  Browser will stay open for 60 seconds for inspection...")
                ups_login.page.wait_for_timeout(60000)
                return False

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = test_void_workflow()
    sys.exit(0 if success else 1)
