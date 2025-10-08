#!/usr/bin/env python3
"""
UPS Shipping History Automation Example

This script demonstrates how to:
1. Login to UPS account
2. Navigate to Shipping History page
3. Access the page for further automation

Usage:
    poetry run python examples/ups_shipping_history_example.py
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


def main():
    """Main function demonstrating UPS Shipping History automation"""

    print("=" * 70)
    print("🚀 UPS Shipping History Automation Example")
    print("=" * 70)

    try:
        # Create automation instance with visible browser
        # Note: headless=False is required for UPS (they block headless browsers)
        with UPSWebLoginAutomation(headless=False) as ups_login:

            # Step 1: Login
            print("\n📝 Step 1: Logging into UPS account...")
            print("-" * 70)

            login_result = ups_login.login(save_screenshots=True)

            if not login_result["success"]:
                print(f"❌ Login failed: {login_result['message']}")
                return False

            print(f"✅ Login successful!")
            print(f"   URL: {login_result['url']}")
            print(f"   Screenshot: {login_result['screenshot']}")

            # Step 2: Navigate to Shipping History
            print("\n📝 Step 2: Navigating to Shipping History...")
            print("-" * 70)

            nav_result = ups_login.navigate_to_shipping_history(save_screenshots=True)

            if not nav_result["success"]:
                print(f"❌ Navigation failed: {nav_result['message']}")
                return False

            print(f"✅ Navigation successful!")
            print(f"   URL: {nav_result['url']}")
            print(f"   Screenshot: {nav_result['screenshot']}")

            # Step 3: You can now interact with the Shipping History page
            print("\n📝 Step 3: Accessing Shipping History page...")
            print("-" * 70)

            page = ups_login.page

            # Get page title
            title = page.title()
            print(f"✅ Page title: {title}")

            # Get current URL
            current_url = page.url
            print(f"✅ Current URL: {current_url}")

            # Example: Wait for page to fully load
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
                print("✅ Page fully loaded")
            except:
                print("⚠️ Page still loading (this is normal for UPS)")

            # Example: Take a final screenshot
            screenshot_path = ups_login.save_screenshot("final_shipping_history")
            print(f"✅ Final screenshot: {screenshot_path}")

            # At this point, you can add your custom automation:
            # - Extract shipping data
            # - Filter by date range
            # - Search for specific tracking numbers
            # - Download reports
            # - etc.

            print("\n" + "=" * 70)
            print("🎉 Automation Complete!")
            print("=" * 70)
            print("\n💡 Next Steps:")
            print("   1. Inspect the page structure to identify data elements")
            print("   2. Add data extraction logic")
            print("   3. Export data to CSV or database")
            print("   4. Integrate with existing workflows")

            # Keep browser open for 10 seconds for manual inspection
            print("\n⏸️ Browser will stay open for 10 seconds...")
            page.wait_for_timeout(10000)

            return True

    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
