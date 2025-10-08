#!/usr/bin/env python3
"""
UPS Void Shipment Automation Example

This script demonstrates how to:
1. Login to UPS account
2. Navigate to Shipping History page
3. Void a shipment

Usage:
    poetry run python examples/ups_void_shipment_example.py
    
    # Void a specific shipment by index (0 = first shipment)
    poetry run python examples/ups_void_shipment_example.py --index 0
"""

import sys
import argparse
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


def main():
    """Main function demonstrating UPS void shipment automation"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Void a UPS shipment')
    parser.add_argument(
        '--index',
        type=int,
        default=0,
        help='Index of shipment to void (0 = first shipment, default: 0)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Navigate to shipping history but do not void (for testing)'
    )
    args = parser.parse_args()
    
    print("=" * 70)
    print("🗑️  UPS Void Shipment Automation")
    print("=" * 70)
    
    if args.dry_run:
        print("⚠️  DRY RUN MODE - Will not actually void shipment")
        print("=" * 70)
    
    try:
        # Create automation instance with visible browser
        with UPSWebLoginAutomation(headless=False) as ups_login:
            
            # Step 1: Login
            print("\n📝 Step 1: Logging into UPS account...")
            print("-" * 70)
            
            login_result = ups_login.login(save_screenshots=True)
            
            if not login_result['success']:
                print(f"❌ Login failed: {login_result['message']}")
                return False
            
            print(f"✅ Login successful!")
            print(f"   URL: {login_result['url']}")
            
            # Step 2: Navigate to Shipping History
            print("\n📝 Step 2: Navigating to Shipping History...")
            print("-" * 70)
            
            nav_result = ups_login.navigate_to_shipping_history(save_screenshots=True)
            
            if not nav_result['success']:
                print(f"❌ Navigation failed: {nav_result['message']}")
                return False
            
            print(f"✅ Navigation successful!")
            print(f"   URL: {nav_result['url']}")
            
            if args.dry_run:
                print("\n" + "=" * 70)
                print("⏸️  DRY RUN - Stopping before void")
                print("=" * 70)
                print("   Browser will stay open for 30 seconds for inspection...")
                ups_login.page.wait_for_timeout(30000)
                return True
            
            # Step 3: Void Shipment
            print("\n📝 Step 3: Voiding shipment...")
            print("-" * 70)
            print(f"   Target: Shipment at index {args.index}")
            
            # Confirm with user
            print("\n⚠️  WARNING: This will void the shipment!")
            response = input("   Continue? (yes/no): ").strip().lower()
            
            if response != 'yes':
                print("❌ Void cancelled by user")
                return False
            
            void_result = ups_login.void_shipment(
                shipment_index=args.index,
                save_screenshots=True
            )
            
            # Display results
            print("\n" + "=" * 70)
            print("📊 VOID RESULT")
            print("=" * 70)
            
            if void_result['success']:
                print(f"✅ Success: {void_result['message']}")
                if void_result.get('tracking_number'):
                    print(f"   Tracking: {void_result['tracking_number']}")
                if void_result.get('screenshot'):
                    print(f"   Screenshot: {void_result['screenshot']}")
            else:
                print(f"❌ Failed: {void_result['message']}")
                if void_result.get('screenshot'):
                    print(f"   Screenshot: {void_result['screenshot']}")
            
            # Keep browser open for verification
            print("\n" + "=" * 70)
            print("⏸️  Browser will stay open for 10 seconds for verification...")
            print("=" * 70)
            ups_login.page.wait_for_timeout(10000)
            
            return void_result['success']
            
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        return False
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

