#!/usr/bin/env python3
"""
Inspect UPS Void Action - Three Dots Menu
This script specifically looks for the three-dot action button and void option
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


def inspect_void_action():
    """Inspect the three-dot action menu and void option"""
    
    print("=" * 70)
    print("🔍 UPS Void Action Inspector - Three Dots Menu")
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
            ups_login.save_screenshot("void_inspect_01_history_page")
            
            # Look for three-dot buttons specifically
            print("\n" + "=" * 70)
            print("🔍 LOOKING FOR THREE-DOT ACTION BUTTONS:")
            print("=" * 70)
            
            # Try different selectors for three-dot menu
            three_dot_selectors = [
                'button:has-text("⋮")',  # Vertical three dots
                'button:has-text("⋯")',  # Horizontal three dots
                'button:has-text("...")',  # Three periods
                'button[aria-label*="more"]',
                'button[aria-label*="More"]',
                'button[aria-label*="action"]',
                'button[aria-label*="Action"]',
                'button[title*="more"]',
                'button[title*="More"]',
                'button[title*="action"]',
                'button[title*="Action"]',
                '.action-menu-button',
                '[data-test*="action-menu"]',
                'button.ups-table_col_standalone_action',
            ]
            
            three_dot_buttons = []
            for selector in three_dot_selectors:
                try:
                    elements = ups_login.page.query_selector_all(selector)
                    visible_elements = [e for e in elements if e.is_visible()]
                    if visible_elements:
                        print(f"\n✅ Found {len(visible_elements)} buttons with: {selector}")
                        three_dot_buttons = visible_elements
                        break
                except:
                    continue
            
            if not three_dot_buttons:
                print("\n⚠️ No three-dot buttons found with specific selectors")
                print("   Looking for all buttons in the table/list area...")
                
                # Get all buttons
                all_buttons = ups_login.page.query_selector_all('button')
                visible_buttons = [b for b in all_buttons if b.is_visible()]
                
                print(f"\n   Found {len(visible_buttons)} total visible buttons")
                print("\n   Inspecting buttons for three-dot patterns:")
                
                for i, btn in enumerate(visible_buttons, 1):
                    try:
                        text = btn.inner_text().strip()
                        aria_label = btn.get_attribute('aria-label') or ''
                        title = btn.get_attribute('title') or ''
                        class_name = btn.get_attribute('class') or ''
                        
                        # Look for action-related buttons
                        if ('action' in class_name.lower() or 
                            'action' in aria_label.lower() or
                            'action' in title.lower() or
                            text in ['⋮', '⋯', '...', 'Actions']):
                            
                            print(f"\n   Button {i} (Potential Action Button):")
                            print(f"      Text: '{text}'")
                            print(f"      Aria-label: '{aria_label}'")
                            print(f"      Title: '{title}'")
                            print(f"      Class: '{class_name[:80]}'")
                            
                            if not three_dot_buttons:
                                three_dot_buttons.append(btn)
                    except:
                        continue
            
            if not three_dot_buttons:
                print("\n❌ Could not find any action buttons")
                print("   Please check the page manually")
                ups_login.page.wait_for_timeout(30000)
                return
            
            # Click the first three-dot button
            print("\n" + "=" * 70)
            print("🖱️ CLICKING FIRST THREE-DOT BUTTON:")
            print("=" * 70)
            
            first_button = three_dot_buttons[0]
            
            try:
                text = first_button.inner_text().strip()
                print(f"   Button text: '{text}'")
            except:
                print(f"   Button text: (unable to read)")
            
            print(f"   Clicking...")
            first_button.click()
            
            # Wait for menu to appear
            print("   Waiting for menu to appear...")
            ups_login.page.wait_for_timeout(2000)
            
            # Take screenshot of opened menu
            ups_login.save_screenshot("void_inspect_02_menu_opened")
            
            # Look for all menu items
            print("\n" + "=" * 70)
            print("📋 MENU ITEMS AFTER CLICKING:")
            print("=" * 70)
            
            # Get all visible elements that could be menu items
            menu_item_selectors = [
                '[role="menuitem"]',
                '.menu-item',
                '.dropdown-item',
                'li a',
                'li button',
                'ul li',
            ]
            
            all_menu_items = []
            for selector in menu_item_selectors:
                try:
                    elements = ups_login.page.query_selector_all(selector)
                    visible_elements = [e for e in elements if e.is_visible()]
                    if visible_elements:
                        print(f"\n✅ Found {len(visible_elements)} menu items with: {selector}")
                        all_menu_items.extend(visible_elements)
                except:
                    continue
            
            # Remove duplicates
            all_menu_items = list(set(all_menu_items))
            
            if all_menu_items:
                print(f"\n📋 Total unique menu items: {len(all_menu_items)}")
                print("\nMenu item details:")
                
                for i, item in enumerate(all_menu_items, 1):
                    try:
                        text = item.inner_text().strip()
                        tag = item.evaluate('el => el.tagName')
                        href = item.get_attribute('href') or 'N/A'
                        
                        print(f"\n{i}. {tag}: '{text}'")
                        if href != 'N/A':
                            print(f"   Href: {href}")
                        
                        # Check if this is the void option
                        if 'void' in text.lower():
                            print(f"   ⭐ THIS IS THE VOID OPTION!")
                    except:
                        continue
            else:
                print("\n⚠️ No menu items found with standard selectors")
                print("   Looking for any newly visible elements...")
                
                # Get all links and buttons
                all_links = ups_login.page.query_selector_all('a, button')
                visible_links = [link for link in all_links if link.is_visible()]
                
                print(f"\n   Found {len(visible_links)} visible links/buttons")
                print("\n   First 20 items:")
                
                for i, link in enumerate(visible_links[:20], 1):
                    try:
                        text = link.inner_text().strip()
                        if text:
                            print(f"   {i}. {text}")
                            if 'void' in text.lower():
                                print(f"      ⭐ THIS IS THE VOID OPTION!")
                    except:
                        continue
            
            # Specifically look for void option
            print("\n" + "=" * 70)
            print("🔍 SPECIFICALLY LOOKING FOR VOID OPTION:")
            print("=" * 70)
            
            void_selectors = [
                'button:has-text("Void")',
                'a:has-text("Void")',
                '[role="menuitem"]:has-text("Void")',
                'li:has-text("Void")',
                '.menu-item:has-text("Void")',
                '[data-test*="void"]',
            ]
            
            void_found = False
            for selector in void_selectors:
                try:
                    void_element = ups_login.page.query_selector(selector)
                    if void_element and void_element.is_visible():
                        print(f"\n✅ FOUND VOID OPTION: {selector}")
                        text = void_element.inner_text()
                        tag = void_element.evaluate('el => el.tagName')
                        print(f"   Tag: {tag}")
                        print(f"   Text: '{text}'")
                        print(f"   Visible: {void_element.is_visible()}")
                        print(f"   Enabled: {void_element.is_enabled()}")
                        void_found = True
                        break
                except Exception as e:
                    continue
            
            if not void_found:
                print("\n⚠️ Void option not found with standard selectors")
            
            # Keep browser open for manual inspection
            print("\n" + "=" * 70)
            print("⏸️ Browser will stay open for 60 seconds for manual inspection...")
            print("   Please manually check the menu for the void option")
            print("=" * 70)
            ups_login.page.wait_for_timeout(60000)
            
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)


if __name__ == "__main__":
    inspect_void_action()

