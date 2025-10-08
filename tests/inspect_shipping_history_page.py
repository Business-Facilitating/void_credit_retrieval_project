#!/usr/bin/env python3
"""
Inspect UPS Shipping History Page Structure
This script logs in, navigates to shipping history, and inspects the page structure
to find the actions menu and void option.
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def inspect_shipping_history_page():
    """Inspect the shipping history page structure"""
    
    print("=" * 70)
    print("🔍 UPS Shipping History Page Inspector")
    print("=" * 70)
    
    try:
        with UPSWebLoginAutomation(headless=False) as ups_login:
            # Login
            print("\n🔐 Logging in...")
            login_result = ups_login.login(save_screenshots=True)
            
            if not login_result['success']:
                print(f"❌ Login failed: {login_result['message']}")
                return
            
            print(f"✅ Login successful!")
            
            # Navigate to shipping history
            print("\n🚢 Navigating to Shipping History...")
            nav_result = ups_login.navigate_to_shipping_history(save_screenshots=True)
            
            if not nav_result['success']:
                print(f"❌ Navigation failed: {nav_result['message']}")
                return
            
            print(f"✅ On Shipping History page!")
            
            # Wait for page to load
            print("\n⏳ Waiting for page to fully load...")
            ups_login.page.wait_for_timeout(5000)
            
            # Take screenshot
            ups_login.save_screenshot("inspect_shipping_history_01")
            
            # Look for shipment rows/items
            print("\n" + "=" * 70)
            print("📦 LOOKING FOR SHIPMENT ITEMS:")
            print("=" * 70)
            
            # Common selectors for shipment rows
            shipment_selectors = [
                'tr[data-test*="shipment"]',
                '.shipment-row',
                '[class*="shipment"]',
                'tbody tr',
                '[role="row"]',
                '.history-item',
                '[data-shipment-id]',
            ]
            
            shipments = []
            for selector in shipment_selectors:
                try:
                    elements = ups_login.page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        print(f"\n✅ Found {len(elements)} elements with selector: {selector}")
                        shipments = elements
                        break
                except Exception as e:
                    continue
            
            if not shipments:
                print("⚠️ No shipment rows found with common selectors")
                print("   Trying to find any table rows...")
                shipments = ups_login.page.query_selector_all('tr')
                print(f"   Found {len(shipments)} total table rows")
            
            # Look for action buttons (three dots)
            print("\n" + "=" * 70)
            print("🔍 LOOKING FOR ACTION BUTTONS (Three Dots):")
            print("=" * 70)
            
            action_button_selectors = [
                'button[aria-label*="action"]',
                'button[aria-label*="Action"]',
                'button[aria-label*="menu"]',
                'button[aria-label*="Menu"]',
                'button[aria-label*="more"]',
                'button[aria-label*="More"]',
                '[data-test*="action"]',
                '[data-test*="menu"]',
                'button:has-text("⋮")',
                'button:has-text("...")',
                '.action-button',
                '.menu-button',
                '[class*="action"]',
                '[class*="menu"]',
                'button[title*="action"]',
                'button[title*="Action"]',
            ]
            
            action_buttons = []
            for selector in action_button_selectors:
                try:
                    elements = ups_login.page.query_selector_all(selector)
                    visible_elements = [e for e in elements if e.is_visible()]
                    if visible_elements:
                        print(f"\n✅ Found {len(visible_elements)} action buttons: {selector}")
                        action_buttons = visible_elements
                        break
                except:
                    continue
            
            if not action_buttons:
                print("⚠️ No action buttons found with common selectors")
                print("   Looking for all buttons...")
                all_buttons = ups_login.page.query_selector_all('button')
                visible_buttons = [b for b in all_buttons if b.is_visible()]
                print(f"   Found {len(visible_buttons)} total visible buttons")
                
                # Print first 20 buttons
                print("\n   First 20 visible buttons:")
                for i, btn in enumerate(visible_buttons[:20], 1):
                    try:
                        text = btn.inner_text().strip()
                        aria_label = btn.get_attribute('aria-label') or ''
                        title = btn.get_attribute('title') or ''
                        class_name = btn.get_attribute('class') or ''
                        print(f"   {i}. Text: '{text}' | Aria: '{aria_label}' | Title: '{title}' | Class: '{class_name[:50]}'")
                    except:
                        continue
            else:
                # Inspect action buttons
                print(f"\n📋 Action Button Details:")
                for i, btn in enumerate(action_buttons[:5], 1):
                    try:
                        text = btn.inner_text().strip()
                        aria_label = btn.get_attribute('aria-label') or ''
                        title = btn.get_attribute('title') or ''
                        class_name = btn.get_attribute('class') or ''
                        print(f"\n{i}. Action Button:")
                        print(f"   Text: '{text}'")
                        print(f"   Aria-label: '{aria_label}'")
                        print(f"   Title: '{title}'")
                        print(f"   Class: '{class_name}'")
                    except:
                        continue
            
            # Try clicking the first action button if found
            if action_buttons:
                print("\n" + "=" * 70)
                print("🖱️ CLICKING FIRST ACTION BUTTON:")
                print("=" * 70)
                
                try:
                    first_button = action_buttons[0]
                    print(f"Clicking action button...")
                    first_button.click()
                    
                    # Wait for menu to appear
                    ups_login.page.wait_for_timeout(2000)
                    
                    # Take screenshot
                    ups_login.save_screenshot("inspect_shipping_history_02_menu_opened")
                    
                    # Look for void option
                    print("\n🔍 Looking for VOID option in menu...")
                    
                    void_selectors = [
                        'a:has-text("Void")',
                        'button:has-text("Void")',
                        '[role="menuitem"]:has-text("Void")',
                        'li:has-text("Void")',
                        '[data-test*="void"]',
                        'a:has-text("Cancel")',
                        'button:has-text("Cancel")',
                    ]
                    
                    void_option = None
                    for selector in void_selectors:
                        try:
                            element = ups_login.page.wait_for_selector(selector, timeout=3000)
                            if element and element.is_visible():
                                print(f"✅ Found void option: {selector}")
                                text = element.inner_text()
                                href = element.get_attribute('href') or 'N/A'
                                print(f"   Text: '{text}'")
                                print(f"   Href: '{href}'")
                                void_option = element
                                break
                        except:
                            continue
                    
                    if not void_option:
                        print("⚠️ Void option not found with common selectors")
                        print("   Looking for all menu items...")
                        
                        # Get all visible links and buttons
                        all_links = ups_login.page.query_selector_all('a, button, [role="menuitem"]')
                        visible_items = [item for item in all_links if item.is_visible()]
                        
                        print(f"\n   Found {len(visible_items)} visible menu items:")
                        for i, item in enumerate(visible_items[:20], 1):
                            try:
                                text = item.inner_text().strip()
                                if text:
                                    print(f"   {i}. {text}")
                            except:
                                continue
                    
                except Exception as e:
                    print(f"❌ Error clicking action button: {e}")
            
            # Save page HTML
            print("\n" + "=" * 70)
            print("💾 Saving page HTML...")
            print("=" * 70)
            
            html_content = ups_login.page.content()
            output_dir = Path("data/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            html_file = output_dir / "shipping_history_page.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ HTML saved to: {html_file}")
            
            # Keep browser open for manual inspection
            print("\n" + "=" * 70)
            print("⏸️ Browser will stay open for 30 seconds for manual inspection...")
            print("=" * 70)
            ups_login.page.wait_for_timeout(30000)
            
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)


if __name__ == "__main__":
    inspect_shipping_history_page()

