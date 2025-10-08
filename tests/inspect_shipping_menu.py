#!/usr/bin/env python3
"""
Inspect UPS Shipping Menu Structure
This script logs in and inspects what's available in the Shipping menu
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


def inspect_shipping_menu():
    """Inspect the shipping menu structure after login"""
    
    print("=" * 70)
    print("🔍 UPS Shipping Menu Inspector")
    print("=" * 70)
    
    try:
        with UPSWebLoginAutomation(headless=False) as ups_login:
            # Login first
            print("\n🔐 Logging in...")
            login_result = ups_login.login(save_screenshots=True)
            
            if not login_result['success']:
                print(f"❌ Login failed: {login_result['message']}")
                return
            
            print(f"✅ Login successful! URL: {login_result['url']}")
            
            # Wait for page to be ready
            print("\n⏳ Waiting for page to load...")
            ups_login.page.wait_for_load_state('domcontentloaded', timeout=10000)
            ups_login.page.wait_for_timeout(2000)
            
            # Take screenshot of home page
            ups_login.save_screenshot("inspect_01_home_page")
            
            # Look for Shipping menu
            print("\n🔍 Looking for Shipping menu...")
            shipping_selectors = [
                'a:has-text("Shipping")',
                'button:has-text("Shipping")',
                'a[href*="shipping"]',
                'nav a:has-text("Ship")',
            ]
            
            shipping_link = None
            for selector in shipping_selectors:
                try:
                    shipping_link = ups_login.page.wait_for_selector(selector, timeout=3000)
                    if shipping_link and shipping_link.is_visible():
                        print(f"✅ Found Shipping menu: {selector}")
                        break
                except:
                    continue
            
            if not shipping_link:
                print("❌ Could not find Shipping menu")
                return
            
            # Click Shipping menu
            print("\n🖱️ Clicking Shipping menu...")
            shipping_link.click()
            
            # Wait for menu to open
            ups_login.page.wait_for_timeout(3000)
            
            # Take screenshot after clicking
            ups_login.save_screenshot("inspect_02_shipping_menu_clicked")
            
            # Get all links on the page
            print("\n" + "=" * 70)
            print("📋 ALL VISIBLE LINKS ON PAGE:")
            print("=" * 70)
            
            all_links = ups_login.page.query_selector_all('a')
            visible_links = []
            
            for i, link in enumerate(all_links):
                try:
                    if link.is_visible():
                        text = link.inner_text().strip()
                        href = link.get_attribute('href')
                        if text:  # Only show links with text
                            visible_links.append({
                                'text': text,
                                'href': href
                            })
                except:
                    continue
            
            # Print all visible links
            for i, link in enumerate(visible_links, 1):
                print(f"\n{i}. Text: {link['text'][:60]}")
                print(f"   Href: {link['href']}")
            
            # Look specifically for history-related links
            print("\n" + "=" * 70)
            print("🔍 HISTORY-RELATED LINKS:")
            print("=" * 70)
            
            history_keywords = ['history', 'view', 'shipment', 'recent', 'past']
            history_links = []
            
            for link in visible_links:
                text_lower = link['text'].lower()
                href_lower = (link['href'] or '').lower()
                
                if any(keyword in text_lower or keyword in href_lower for keyword in history_keywords):
                    history_links.append(link)
            
            if history_links:
                for i, link in enumerate(history_links, 1):
                    print(f"\n{i}. Text: {link['text']}")
                    print(f"   Href: {link['href']}")
            else:
                print("❌ No history-related links found")
            
            # Get all buttons
            print("\n" + "=" * 70)
            print("📋 ALL VISIBLE BUTTONS:")
            print("=" * 70)
            
            all_buttons = ups_login.page.query_selector_all('button')
            visible_buttons = []
            
            for button in all_buttons:
                try:
                    if button.is_visible():
                        text = button.inner_text().strip()
                        if text:
                            visible_buttons.append(text)
                except:
                    continue
            
            for i, text in enumerate(visible_buttons, 1):
                print(f"{i}. {text}")
            
            # Save page HTML for inspection
            print("\n" + "=" * 70)
            print("💾 Saving page HTML...")
            print("=" * 70)
            
            html_content = ups_login.page.content()
            output_dir = Path("data/output")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            html_file = output_dir / "shipping_menu_page.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"✅ HTML saved to: {html_file}")
            
            # Try to find navigation menu items
            print("\n" + "=" * 70)
            print("🔍 NAVIGATION MENU ITEMS:")
            print("=" * 70)
            
            nav_selectors = [
                'nav a',
                '.nav-link',
                '[role="menuitem"]',
                '.menu-item',
                '.dropdown-item',
                'ul li a'
            ]
            
            for selector in nav_selectors:
                try:
                    items = ups_login.page.query_selector_all(selector)
                    visible_items = []
                    
                    for item in items:
                        if item.is_visible():
                            text = item.inner_text().strip()
                            if text:
                                visible_items.append(text)
                    
                    if visible_items:
                        print(f"\n{selector}:")
                        for text in visible_items[:10]:  # Limit to first 10
                            print(f"  - {text}")
                except:
                    continue
            
            # Keep browser open for manual inspection
            print("\n" + "=" * 70)
            print("⏸️ Browser will stay open for 30 seconds for manual inspection...")
            print("=" * 70)
            ups_login.page.wait_for_timeout(30000)
            
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)


if __name__ == "__main__":
    inspect_shipping_menu()

