#!/usr/bin/env python3
"""
UPS Login Page Structure Inspector
===================================

This script inspects the UPS login page to understand its structure,
identify form fields, and determine the correct selectors for automation.

Usage:
    poetry run python tests/test_ups_page_structure.py

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()

UPS_WEB_LOGIN_URL = os.getenv("UPS_WEB_LOGIN_URL", "https://www.ups.com/lasso/login")


def inspect_ups_login_page():
    """Inspect the UPS login page structure"""
    print("🔍 UPS Login Page Structure Inspector")
    print("=" * 70)
    
    with sync_playwright() as p:
        # Launch browser in headed mode so we can see what's happening
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        try:
            # Navigate to login page
            print(f"\n🌐 Navigating to: {UPS_WEB_LOGIN_URL}")
            page.goto(UPS_WEB_LOGIN_URL, wait_until='domcontentloaded', timeout=30000)
            
            # Wait a bit for any redirects
            page.wait_for_timeout(3000)
            
            current_url = page.url
            title = page.title()
            
            print(f"✅ Page loaded successfully")
            print(f"   Current URL: {current_url}")
            print(f"   Title: {title}")
            
            # Take screenshot
            output_dir = Path("data/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = output_dir / "ups_login_page_structure.png"
            page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"   Screenshot: {screenshot_path}")
            
            # Find all input fields
            print("\n📝 Input Fields Found:")
            print("-" * 70)
            
            inputs = page.query_selector_all('input')
            for i, input_elem in enumerate(inputs, 1):
                input_type = input_elem.get_attribute('type') or 'text'
                input_name = input_elem.get_attribute('name') or 'N/A'
                input_id = input_elem.get_attribute('id') or 'N/A'
                input_placeholder = input_elem.get_attribute('placeholder') or 'N/A'
                is_visible = input_elem.is_visible()
                
                print(f"\nInput {i}:")
                print(f"   Type: {input_type}")
                print(f"   Name: {input_name}")
                print(f"   ID: {input_id}")
                print(f"   Placeholder: {input_placeholder}")
                print(f"   Visible: {is_visible}")
            
            # Find all buttons
            print("\n\n🔘 Buttons Found:")
            print("-" * 70)
            
            buttons = page.query_selector_all('button')
            for i, button in enumerate(buttons, 1):
                button_type = button.get_attribute('type') or 'button'
                button_text = button.inner_text() or 'N/A'
                button_id = button.get_attribute('id') or 'N/A'
                button_name = button.get_attribute('name') or 'N/A'
                is_visible = button.is_visible()
                
                print(f"\nButton {i}:")
                print(f"   Type: {button_type}")
                print(f"   Text: {button_text}")
                print(f"   ID: {button_id}")
                print(f"   Name: {button_name}")
                print(f"   Visible: {is_visible}")
            
            # Find forms
            print("\n\n📋 Forms Found:")
            print("-" * 70)
            
            forms = page.query_selector_all('form')
            for i, form in enumerate(forms, 1):
                form_action = form.get_attribute('action') or 'N/A'
                form_method = form.get_attribute('method') or 'N/A'
                form_id = form.get_attribute('id') or 'N/A'
                
                print(f"\nForm {i}:")
                print(f"   Action: {form_action}")
                print(f"   Method: {form_method}")
                print(f"   ID: {form_id}")
            
            # Get page HTML (first 2000 chars)
            print("\n\n📄 Page HTML (first 2000 chars):")
            print("-" * 70)
            html = page.content()
            print(html[:2000])
            
            # Save full HTML
            html_path = output_dir / "ups_login_page.html"
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"\n💾 Full HTML saved to: {html_path}")
            
            # Wait for user to inspect
            print("\n\n⏸️  Browser will stay open for 30 seconds for manual inspection...")
            print("   You can manually interact with the page to see what happens.")
            page.wait_for_timeout(30000)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()
            print("\n✅ Browser closed")


def main():
    """Main function"""
    try:
        inspect_ups_login_page()
        return 0
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

