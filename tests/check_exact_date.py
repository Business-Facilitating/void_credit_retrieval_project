#!/usr/bin/env python3
"""
Quick script to check tracking numbers for exact invoice date
"""

from datetime import datetime, timedelta

import duckdb


def check_exact_date_tracking():
    """Check tracking numbers for exactly 30 days ago"""

    # Calculate target date (exactly 30 days ago)
    target_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    print(f"🎯 Checking for invoice_date = {target_date}")

    # Connect to DuckDB
    conn = duckdb.connect("carrier_invoice_extraction.duckdb")

    try:
        # Check total records for exact date
        result = conn.execute(
            """
            SELECT
                COUNT(*) as total_records,
                COUNT(DISTINCT tracking_number) as unique_tracking_numbers
            FROM carrier_invoice_data.carrier_invoice_data
            WHERE invoice_date = ?
        """,
            [target_date],
        ).fetchone()

        total_records, unique_tracking = result
        print(f"📊 Records with invoice_date = {target_date}:")
        print(f"   - Total records: {total_records:,}")
        print(f"   - Unique tracking numbers: {unique_tracking:,}")

        if total_records > 0:
            # Get sample tracking numbers
            sample_tracking = conn.execute(
                """
                SELECT DISTINCT tracking_number 
                FROM carrier_invoice_data.carrier_invoice_data
                WHERE invoice_date = ? AND tracking_number IS NOT NULL AND tracking_number != ''
                LIMIT 10
            """,
                [target_date],
            ).fetchall()

            if sample_tracking:
                print(f"📋 Sample tracking numbers:")
                for i, (tracking,) in enumerate(sample_tracking, 1):
                    print(f"   {i}. {tracking}")

            # Export tracking numbers to file
            tracking_numbers = conn.execute(
                """
                SELECT DISTINCT tracking_number 
                FROM carrier_invoice_data.carrier_invoice_data
                WHERE invoice_date = ? AND tracking_number IS NOT NULL AND tracking_number != ''
                ORDER BY tracking_number
            """,
                [target_date],
            ).fetchall()

            if tracking_numbers:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"data/output/tracking_numbers_exact_{target_date.replace('-', '')}_{timestamp}.txt"

                with open(filename, "w") as f:
                    for (tracking,) in tracking_numbers:
                        f.write(f"{tracking}\n")

                print(
                    f"📁 Exported {len(tracking_numbers)} tracking numbers to: {filename}"
                )
        else:
            print(f"❌ No records found with invoice_date = {target_date}")

            # Check what dates are available
            print("\n🔍 Checking available invoice dates...")
            available_dates = conn.execute(
                """
                SELECT invoice_date, COUNT(*) as count
                FROM carrier_invoice_data.carrier_invoice_data
                WHERE invoice_date IS NOT NULL
                GROUP BY invoice_date 
                ORDER BY invoice_date DESC 
                LIMIT 10
            """
            ).fetchall()

            print("📅 Recent invoice dates in database:")
            for date, count in available_dates:
                print(f"   - {date}: {count:,} records")

    finally:
        conn.close()


if __name__ == "__main__":
    check_exact_date_tracking()
if __name__ == "__main__":
    check_exact_date_tracking()
if __name__ == "__main__":
    check_exact_date_tracking()
