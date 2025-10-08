#!/usr/bin/env python3
"""
Find the exact selector for the three-dot action button
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.src.ups_web_login import UPSWebLoginAutomation
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_action_button():
    """Find the exact selector for action buttons"""
    
    print("=" * 70)
    print("🔍 Finding Action Button Selector")
    print("=" * 70)
    
    try:
        with UPSWebLoginAutomation(headless=False) as ups_login:
            # Login and navigate
            ups_login.login()
            ups_login.navigate_to_shipping_history()
            ups_login.page.wait_for_timeout(5000)
            
            print("\n📋 Looking for ALL buttons in the page...")
            
            # Get all buttons
            all_buttons = ups_login.page.query_selector_all('button')
            print(f"   Total buttons found: {len(all_buttons)}")
            
            # Find buttons in table rows
            print("\n📋 Looking for buttons in table rows...")
            row_buttons = ups_login.page.query_selector_all('tbody tr button')
            print(f"   Buttons in table rows: {len(row_buttons)}")
            
            if row_buttons:
                print("\n📝 Details of buttons in table rows:")
                for i, btn in enumerate(row_buttons, 1):
                    try:
                        text = btn.inner_text().strip()
                        aria_label = btn.get_attribute('aria-label') or ''
                        class_name = btn.get_attribute('class') or ''
                        
                        print(f"\n   Button {i}:")
                        print(f"      Text: '{text}'")
                        print(f"      Aria-label: '{aria_label}'")
                        print(f"      Class: '{class_name}'")
                        print(f"      Visible: {btn.is_visible()}")
                    except:
                        continue
            
            # Look for buttons in Actions column specifically
            print("\n📋 Looking in Actions column header...")
            try:
                actions_header = ups_login.page.query_selector('th:has-text("Actions")')
                if actions_header:
                    print("   ✅ Found Actions column header")
                    
                    # Get the column index
                    headers = ups_login.page.query_selector_all('thead th')
                    actions_index = None
                    for i, header in enumerate(headers):
                        if 'action' in header.inner_text().lower():
                            actions_index = i
                            print(f"   Actions column is at index: {i}")
                            break
                    
                    if actions_index is not None:
                        # Get buttons in that column
                        print(f"\n📋 Looking for buttons in column {actions_index}...")
                        rows = ups_login.page.query_selector_all('tbody tr')
                        print(f"   Found {len(rows)} rows")
                        
                        for row_idx, row in enumerate(rows[:3], 1):  # First 3 rows
                            cells = row.query_selector_all('td')
                            if actions_index < len(cells):
                                action_cell = cells[actions_index]
                                buttons_in_cell = action_cell.query_selector_all('button')
                                
                                print(f"\n   Row {row_idx}, Actions cell:")
                                print(f"      Buttons in cell: {len(buttons_in_cell)}")
                                
                                for btn_idx, btn in enumerate(buttons_in_cell, 1):
                                    text = btn.inner_text().strip()
                                    aria = btn.get_attribute('aria-label') or ''
                                    cls = btn.get_attribute('class') or ''
                                    
                                    print(f"      Button {btn_idx}:")
                                    print(f"         Text: '{text}'")
                                    print(f"         Aria: '{aria}'")
                                    print(f"         Class: '{cls[:60]}'")
            except Exception as e:
                print(f"   Error: {e}")
            
            print("\n⏸️  Browser will stay open for 60 seconds...")
            print("   Please manually inspect the page")
            print("=" * 70)
            ups_login.page.wait_for_timeout(60000)
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    find_action_button()

