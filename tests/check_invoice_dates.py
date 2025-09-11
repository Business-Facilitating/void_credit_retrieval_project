#!/usr/bin/env python3
"""
Quick script to check invoice date distribution in DuckDB
"""

from datetime import datetime, timedelta

import duckdb


def main():
    print("🔍 Checking invoice date distribution in DuckDB...")

    try:
        # Connect to DuckDB
        conn = duckdb.connect("carrier_invoice_extraction.duckdb")

        # Get invoice date distribution
        print("\n📊 Invoice Date Distribution:")
        result = conn.execute(
            """
            SELECT invoice_date, COUNT(*) as count
            FROM carrier_invoice_data.carrier_invoice_data
            GROUP BY invoice_date
            ORDER BY invoice_date
        """
        ).fetchall()

        total_records = 0
        for row in result:
            print(f"  {row[0]}: {row[1]:,} records")
            total_records += row[1]

        print(f"\n📈 Total records: {total_records:,}")

        # Check what the target date should be (30 days ago)
        target_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        print(f"\n🎯 Target date (30 days ago): {target_date}")

        # Check if we have data for the target date
        target_result = conn.execute(
            """
            SELECT COUNT(*) 
            FROM carrier_invoice_data.carrier_invoice_data
            WHERE invoice_date = ?
        """,
            [target_date],
        ).fetchone()

        target_count = target_result[0] if target_result else 0
        print(f"📦 Records for target date {target_date}: {target_count:,}")

        if target_count == 0:
            print("⚠️  No records found for the exact target date!")
            print(
                "💡 The database contains data from previous extractions with different date ranges."
            )
            print(
                "🔧 Need to clear the database and re-extract with exact date filtering."
            )

        conn.close()

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
if __name__ == "__main__":
    main()
