#!/usr/bin/env python3
"""
Bulk Void Label-Only Shipments
===============================

This script automates the process of voiding UPS shipments that have label-only status.

Workflow:
1. Loads tracking numbers from ups_label_only_filter.py CSV output
2. Loads UPS login credentials from PeerDB industry_index_logins table
3. Maps tracking numbers to credentials using account_number (last 6 digits)
4. Logs in with appropriate credentials for each account
5. Voids shipments via UPS web interface
6. Saves results to CSV

Account Mapping:
- industry_index_login.account_number = RIGHT(carrier_invoice.account_number, 6)
- This maps the last 6 digits of the invoice account number to the login credentials

Usage:
    # Basic usage - void all shipments from CSV
    poetry run python examples/bulk_void_label_only_shipments.py --csv data/output/ups_label_only_tracking_*.csv
    
    # Specify custom PeerDB path
    poetry run python examples/bulk_void_label_only_shipments.py --csv data/output/ups_label_only_tracking_*.csv --peerdb peerdb_industry_index_logins.duckdb
    
    # Dry run mode (no actual voiding)
    poetry run python examples/bulk_void_label_only_shipments.py --csv data/output/ups_label_only_tracking_*.csv --dry-run

Prerequisites:
1. Run peerdb_pipeline.py to extract login credentials:
   poetry run python src/src/peerdb_pipeline.py
   
2. Run ups_label_only_filter.py to get tracking numbers:
   poetry run python src/src/ups_label_only_filter.py

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import argparse
import glob
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.src.ups_web_login import UPSWebLoginAutomation

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def find_latest_csv(pattern: str) -> str:
    """Find the most recent CSV file matching the pattern"""
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time, most recent first
    files.sort(key=lambda x: Path(x).stat().st_mtime, reverse=True)
    return files[0]


def main():
    """Main function to run bulk void automation"""
    parser = argparse.ArgumentParser(
        description="Bulk void UPS label-only shipments from CSV"
    )
    parser.add_argument(
        "--csv",
        type=str,
        help="Path to ups_label_only_filter.py CSV output (supports wildcards)",
        default="data/output/ups_label_only_tracking_*.csv",
    )
    parser.add_argument(
        "--peerdb",
        type=str,
        help="Path to PeerDB DuckDB file with login credentials",
        default="peerdb_industry_index_logins.duckdb",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to save results CSV (default: auto-generated)",
        default=None,
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode (default: visible)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode - load data and map credentials but don't void",
    )
    parser.add_argument(
        "--no-screenshots",
        action="store_true",
        help="Disable screenshot capture",
    )

    args = parser.parse_args()

    # Print header
    logger.info("=" * 70)
    logger.info("🚀 BULK VOID LABEL-ONLY SHIPMENTS")
    logger.info("=" * 70)

    # Find CSV file
    csv_path = args.csv
    if "*" in csv_path:
        logger.info(f"🔍 Searching for CSV files: {csv_path}")
        csv_path = find_latest_csv(csv_path)
        if not csv_path:
            logger.error(f"❌ No CSV files found matching pattern: {args.csv}")
            logger.info("💡 Run ups_label_only_filter.py first to generate CSV")
            return False
        logger.info(f"✅ Found latest CSV: {csv_path}")
    else:
        if not Path(csv_path).exists():
            logger.error(f"❌ CSV file not found: {csv_path}")
            return False

    # Check PeerDB file
    if not Path(args.peerdb).exists():
        logger.error(f"❌ PeerDB DuckDB file not found: {args.peerdb}")
        logger.info("💡 Run peerdb_pipeline.py first to extract login credentials:")
        logger.info("   poetry run python src/src/peerdb_pipeline.py")
        return False

    logger.info(f"📊 CSV file: {csv_path}")
    logger.info(f"🔑 PeerDB file: {args.peerdb}")
    logger.info(f"🌐 Headless mode: {args.headless}")
    logger.info(f"📸 Screenshots: {not args.no_screenshots}")

    if args.dry_run:
        logger.info("⚠️  DRY RUN MODE - No shipments will be voided")

    # Confirm with user
    if not args.dry_run:
        logger.info("\n" + "=" * 70)
        logger.info("⚠️  WARNING: This will void shipments in UPS!")
        logger.info("=" * 70)
        response = input("Continue? (yes/no): ").strip().lower()

        if response != "yes":
            logger.info("❌ Operation cancelled by user")
            return False

    try:
        # Create automation instance
        with UPSWebLoginAutomation(headless=args.headless) as ups_login:
            if args.dry_run:
                # In dry run mode, just load and map data
                logger.info("\n📊 DRY RUN - Loading and mapping data...")

                from src.src.ups_web_login import (
                    load_login_credentials_from_peerdb,
                    load_tracking_numbers_from_csv,
                    map_tracking_to_credentials,
                )

                # Load data
                tracking_data = load_tracking_numbers_from_csv(csv_path)
                credentials_map = load_login_credentials_from_peerdb(args.peerdb)
                mapped_data = map_tracking_to_credentials(
                    tracking_data, credentials_map
                )

                # Group by account
                account_groups = {}
                for item in mapped_data:
                    account_key = item["account_number_key"]
                    if account_key not in account_groups:
                        account_groups[account_key] = []
                    account_groups[account_key].append(item)

                # Print summary
                logger.info("\n" + "=" * 70)
                logger.info("📊 DRY RUN SUMMARY")
                logger.info("=" * 70)
                logger.info(f"Total tracking numbers: {len(tracking_data)}")
                logger.info(f"Successfully mapped: {len(mapped_data)}")
                logger.info(f"Unique accounts: {len(account_groups)}")

                logger.info("\n📦 Shipments by account:")
                for account_key, items in account_groups.items():
                    logger.info(f"   Account {account_key}: {len(items)} shipments")
                    for item in items[:3]:  # Show first 3
                        logger.info(f"      - {item['tracking_number']}")
                    if len(items) > 3:
                        logger.info(f"      ... and {len(items) - 3} more")

                logger.info("\n✅ Dry run completed successfully!")
                return True

            else:
                # Actual void operation
                logger.info("\n🚀 Starting bulk void operation...")

                result = ups_login.bulk_void_shipments_from_csv(
                    csv_path=csv_path,
                    peerdb_path=args.peerdb,
                    save_screenshots=not args.no_screenshots,
                    output_csv=args.output,
                )

                # Print final summary
                logger.info("\n" + "=" * 70)
                logger.info("✅ BULK VOID OPERATION COMPLETED")
                logger.info("=" * 70)
                logger.info(f"Total tracking numbers: {result['total_tracking_numbers']}")
                logger.info(f"Successfully voided: {result['total_voided']}")
                logger.info(f"Failed: {result['total_failed']}")

                if result["total_voided"] > 0:
                    success_rate = (
                        result["total_voided"] / result["total_tracking_numbers"]
                    ) * 100
                    logger.info(f"Success rate: {success_rate:.1f}%")

                return result["total_voided"] > 0

    except KeyboardInterrupt:
        logger.info("\n⚠️  Operation interrupted by user")
        return False
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

