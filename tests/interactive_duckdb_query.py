#!/usr/bin/env python3
"""
Interactive DuckDB Query Tool
============================

Simple tool to run custom SQL queries against the DuckDB data.
"""

import os
import sys

import duckdb


def main():
    """Interactive query tool."""
    db_path = "carrier_invoice_extraction.duckdb"

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return

    print("🔍 Interactive DuckDB Query Tool")
    print("=" * 50)
    print(f"Database: {db_path}")
    print("Table: carrier_invoice_extraction.carrier_invoice_data")
    print("Records: ~935,481 (all dates)")
    print("\nType 'help' for example queries, 'quit' to exit")
    print("-" * 50)

    conn = duckdb.connect(db_path)

    while True:
        try:
            query = input("\nSQL> ").strip()

            if query.lower() in ["quit", "exit", "q"]:
                break

            if query.lower() == "help":
                show_help()
                continue

            if not query:
                continue

            # Execute query
            result = conn.execute(query).fetchall()

            if result:
                print(f"\n📊 Results ({len(result)} rows):")
                print("-" * 40)

                # Show first 20 rows
                for i, row in enumerate(result[:20]):
                    print(f"Row {i+1}: {row}")

                if len(result) > 20:
                    print(f"... and {len(result) - 20} more rows")
            else:
                print("✅ Query executed successfully (no results)")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

    conn.close()


def show_help():
    """Show example queries."""
    print("\n💡 Example Queries:")
    print("-" * 30)
    print("1. Count all records:")
    print("   SELECT COUNT(*) FROM carrier_invoice_extraction.carrier_invoice_data;")
    print()
    print("2. Show table structure:")
    print("   DESCRIBE carrier_invoice_extraction.carrier_invoice_data;")
    print()
    print("3. Top 10 tracking numbers:")
    print(
        "   SELECT tracking_number, invoice_number FROM carrier_invoice_extraction.carrier_invoice_data WHERE tracking_number IS NOT NULL LIMIT 10;"
    )
    print()
    print("4. Search by company:")
    print(
        "   SELECT * FROM carrier_invoice_extraction.carrier_invoice_data WHERE sender_company_name LIKE '%WALMART%' LIMIT 5;"
    )
    print()
    print("5. Financial summary:")
    print(
        "   SELECT SUM(CAST(net_amount AS DECIMAL)) as total FROM carrier_invoice_extraction.carrier_invoice_data;"
    )
    print()
    print("6. State analysis:")
    print(
        "   SELECT sender_state, COUNT(*) FROM carrier_invoice_extraction.carrier_invoice_data GROUP BY sender_state ORDER BY COUNT(*) DESC LIMIT 10;"
    )
    print()
    print("7. Date range analysis:")
    print(
        "   SELECT invoice_date, COUNT(*) FROM carrier_invoice_extraction.carrier_invoice_data GROUP BY invoice_date ORDER BY invoice_date DESC LIMIT 10;"
    )


if __name__ == "__main__":
    main()
    main()
