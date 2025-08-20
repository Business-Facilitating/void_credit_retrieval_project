#!/usr/bin/env python3
"""
Explore DuckDB data to understand the tracking numbers and dates available
"""

import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import from src.src
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.src.tracking_17 import TABLE_NAME, connect_to_duckdb


def explore_tracking_data():
    """Explore the tracking data in DuckDB"""
    print("🔍 Exploring DuckDB Tracking Data")
    print("=" * 60)

    conn = connect_to_duckdb()
    if not conn:
        return

    try:
        # 1. Check total records
        total_count = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
        print(f"📊 Total records in database: {total_count:,}")

        # 2. Check tracking number statistics
        tracking_stats = conn.execute(
            f"""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT tracking_number) as unique_tracking_numbers,
                COUNT(CASE WHEN tracking_number IS NOT NULL AND tracking_number != '' THEN 1 END) as non_empty_tracking
            FROM {TABLE_NAME}
        """
        ).fetchone()

        print(f"📦 Tracking number statistics:")
        print(f"   Total records: {tracking_stats[0]:,}")
        print(f"   Unique tracking numbers: {tracking_stats[1]:,}")
        print(f"   Non-empty tracking numbers: {tracking_stats[2]:,}")

        # 3. Check date ranges
        print(f"\n📅 Date Analysis:")

        # Shipment dates
        shipment_date_stats = conn.execute(
            f"""
            SELECT 
                MIN(shipment_date) as min_shipment_date,
                MAX(shipment_date) as max_shipment_date,
                COUNT(CASE WHEN shipment_date IS NOT NULL THEN 1 END) as shipment_date_count
            FROM {TABLE_NAME}
        """
        ).fetchone()

        print(f"   Shipment dates:")
        print(f"     Min: {shipment_date_stats[0]}")
        print(f"     Max: {shipment_date_stats[1]}")
        print(f"     Count: {shipment_date_stats[2]:,}")

        # Invoice dates
        invoice_date_stats = conn.execute(
            f"""
            SELECT 
                MIN(invoice_date) as min_invoice_date,
                MAX(invoice_date) as max_invoice_date,
                COUNT(CASE WHEN invoice_date IS NOT NULL THEN 1 END) as invoice_date_count
            FROM {TABLE_NAME}
        """
        ).fetchone()

        print(f"   Invoice dates:")
        print(f"     Min: {invoice_date_stats[0]}")
        print(f"     Max: {invoice_date_stats[1]}")
        print(f"     Count: {invoice_date_stats[2]:,}")

        # 4. Sample recent tracking numbers (last 30 days)
        print(f"\n📦 Recent tracking numbers (last 30 days):")
        recent_tracking = conn.execute(
            f"""
            SELECT DISTINCT tracking_number, shipment_date, invoice_date
            FROM {TABLE_NAME}
            WHERE tracking_number IS NOT NULL 
            AND tracking_number != ''
            AND (
                TRY_STRPTIME(shipment_date, '%Y-%m-%d') >= CURRENT_DATE - INTERVAL '30 days'
                OR TRY_STRPTIME(invoice_date, '%Y-%m-%d') >= CURRENT_DATE - INTERVAL '30 days'
                OR TRY_STRPTIME(shipment_date, '%m/%d/%Y') >= CURRENT_DATE - INTERVAL '30 days'
                OR TRY_STRPTIME(invoice_date, '%m/%d/%Y') >= CURRENT_DATE - INTERVAL '30 days'
            )
            ORDER BY shipment_date DESC, invoice_date DESC
            LIMIT 10
        """
        ).fetchall()

        if recent_tracking:
            for i, (tracking_num, ship_date, inv_date) in enumerate(recent_tracking, 1):
                print(
                    f"   {i:2d}. {tracking_num} | Ship: {ship_date} | Invoice: {inv_date}"
                )
        else:
            print("   ❌ No recent tracking numbers found")

        # 5. Try different date ranges
        print(f"\n📊 Tracking numbers by date range:")

        date_ranges = [7, 14, 30, 60, 90, 180]
        for days in date_ranges:
            count = conn.execute(
                f"""
                SELECT COUNT(DISTINCT tracking_number)
                FROM {TABLE_NAME}
                WHERE tracking_number IS NOT NULL 
                AND tracking_number != ''
                AND (
                    TRY_STRPTIME(shipment_date, '%Y-%m-%d') >= CURRENT_DATE - INTERVAL '{days} days'
                    OR TRY_STRPTIME(invoice_date, '%Y-%m-%d') >= CURRENT_DATE - INTERVAL '{days} days'
                    OR TRY_STRPTIME(shipment_date, '%m/%d/%Y') >= CURRENT_DATE - INTERVAL '{days} days'
                    OR TRY_STRPTIME(invoice_date, '%m/%d/%Y') >= CURRENT_DATE - INTERVAL '{days} days'
                )
            """
            ).fetchone()[0]
            print(f"   Last {days:3d} days: {count:3d} tracking numbers")

        # 6. Sample some tracking numbers that might work better
        print(f"\n🎯 Suggested tracking numbers to test:")

        # Get some tracking numbers from different time periods
        suggested = conn.execute(
            f"""
            SELECT DISTINCT tracking_number, shipment_date, invoice_date
            FROM {TABLE_NAME}
            WHERE tracking_number IS NOT NULL 
            AND tracking_number != ''
            AND LENGTH(tracking_number) > 10
            ORDER BY RANDOM()
            LIMIT 5
        """
        ).fetchall()

        for i, (tracking_num, ship_date, inv_date) in enumerate(suggested, 1):
            print(f"   {i}. {tracking_num} | Ship: {ship_date} | Invoice: {inv_date}")

    except Exception as e:
        print(f"❌ Error exploring data: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    explore_tracking_data()
    explore_tracking_data()
    explore_tracking_data()
