#!/usr/bin/env python3
"""
Test Mixed Date Format Filtering
==================================

This script tests the date filtering logic to ensure it correctly handles
multiple date formats in the transaction_date column:
- YYYY-MM-DD (ISO format)
- M/D/YYYY (US format with single digits)
- MM/DD/YYYY (US format with leading zeros)
- Empty strings

It creates a test DuckDB database with sample data in different formats
and verifies that the filtering logic correctly extracts records within
the specified date range.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import duckdb

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "src"))

# Test configuration
TEST_DB_PATH = "tests/test_mixed_dates.duckdb"
TEST_START_DAYS_AGO = 89
TEST_END_DAYS_AGO = 70


def create_test_database():
    """Create a test DuckDB database with mixed date formats"""
    print("🔧 Creating test database with mixed date formats...")

    # Remove existing test database
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    conn = duckdb.connect(TEST_DB_PATH)

    # Create test table
    conn.execute(
        """
        CREATE TABLE carrier_invoice_data (
            tracking_number VARCHAR,
            account_number VARCHAR,
            transaction_date VARCHAR,
            invoice_date VARCHAR
        )
    """
    )

    # Calculate test dates
    today = datetime.now()

    # Helper function to format date as M/D/YYYY (without leading zeros) - Windows compatible
    def format_single_digit_date(dt):
        """Format date as M/D/YYYY without leading zeros"""
        return f"{dt.month}/{dt.day}/{dt.year}"

    # Insert test data with different date formats
    test_data = [
        # YYYY-MM-DD format (ISO) - within range (85 days ago)
        (
            "1Z12345E0205271688",
            "123456",
            (today - timedelta(days=85)).strftime("%Y-%m-%d"),
            "2024-01-01",
        ),
        # M/D/YYYY format (US, single digit) - within range (80 days ago)
        (
            "1Z12345E0305271689",
            "123456",
            format_single_digit_date(today - timedelta(days=80)),
            "2024-01-01",
        ),
        # MM/DD/YYYY format (US, leading zeros) - within range (75 days ago)
        (
            "1Z12345E0405271690",
            "123456",
            (today - timedelta(days=75)).strftime("%m/%d/%Y"),
            "2024-01-01",
        ),
        # YYYY-MM-DD format - outside range (too old, 95 days ago)
        (
            "1Z12345E0505271691",
            "123456",
            (today - timedelta(days=95)).strftime("%Y-%m-%d"),
            "2024-01-01",
        ),
        # M/D/YYYY format - outside range (too recent, 65 days ago)
        (
            "1Z12345E0605271692",
            "123456",
            format_single_digit_date(today - timedelta(days=65)),
            "2024-01-01",
        ),
        # MM/DD/YYYY format - edge case (exactly START_DAYS_AGO)
        (
            "1Z12345E0705271693",
            "123456",
            (today - timedelta(days=TEST_START_DAYS_AGO)).strftime("%m/%d/%Y"),
            "2024-01-01",
        ),
        # YYYY-MM-DD format - edge case (exactly END_DAYS_AGO)
        (
            "1Z12345E0805271694",
            "123456",
            (today - timedelta(days=TEST_END_DAYS_AGO)).strftime("%Y-%m-%d"),
            "2024-01-01",
        ),
        # Empty string - should be excluded
        ("1Z12345E0905271695", "123456", "", "2024-01-01"),
        # NULL value - should be excluded
        ("1Z12345E1005271696", "123456", None, "2024-01-01"),
    ]

    for tracking, account, trans_date, inv_date in test_data:
        if trans_date is None:
            conn.execute(
                "INSERT INTO carrier_invoice_data VALUES (?, ?, NULL, ?)",
                [tracking, account, inv_date],
            )
        else:
            conn.execute(
                "INSERT INTO carrier_invoice_data VALUES (?, ?, ?, ?)",
                [tracking, account, trans_date, inv_date],
            )

    conn.close()
    print(f"✅ Test database created: {TEST_DB_PATH}")
    print(f"📊 Inserted {len(test_data)} test records with mixed date formats")


def test_date_filtering():
    """Test the date filtering logic with mixed formats"""
    print("\n🧪 Testing date filtering logic...")

    conn = duckdb.connect(TEST_DB_PATH)

    # Calculate target date range
    start_target_date = (datetime.now() - timedelta(days=TEST_START_DAYS_AGO)).date()
    end_target_date = (datetime.now() - timedelta(days=TEST_END_DAYS_AGO)).date()
    start_date_str = start_target_date.strftime("%Y-%m-%d")
    end_date_str = end_target_date.strftime("%Y-%m-%d")

    print(f"🎯 Target date range: {start_date_str} to {end_date_str}")
    print(f"   ({TEST_START_DAYS_AGO} to {TEST_END_DAYS_AGO} days ago)")

    # Test the filtering query (same logic as ups_label_only_filter.py)
    query = f"""
        SELECT
            tracking_number,
            account_number,
            transaction_date,
            COALESCE(
                TRY_STRPTIME(transaction_date, '%Y-%m-%d'),  -- YYYY-MM-DD
                TRY_STRPTIME(transaction_date, '%m/%d/%Y'),  -- MM/DD/YYYY
                TRY_STRPTIME(transaction_date, '%-m/%-d/%Y')   -- M/D/YYYY (single digit)
            ) as parsed_date
        FROM carrier_invoice_data
        WHERE tracking_number IS NOT NULL
        AND tracking_number != ''
        AND tracking_number LIKE '1Z%'
        AND (
            -- Try parsing with multiple formats using COALESCE
            COALESCE(
                TRY_STRPTIME(transaction_date, '%Y-%m-%d'),  -- YYYY-MM-DD
                TRY_STRPTIME(transaction_date, '%m/%d/%Y'),  -- MM/DD/YYYY
                TRY_STRPTIME(transaction_date, '%-m/%-d/%Y')   -- M/D/YYYY (single digit)
            ) BETWEEN CAST('{start_date_str}' AS DATE) AND CAST('{end_date_str}' AS DATE)
        )
        ORDER BY tracking_number
    """

    result = conn.execute(query).fetchall()

    print(f"\n📋 Query Results:")
    print(f"   Found {len(result)} records matching the date range")
    print()

    for row in result:
        tracking, account, trans_date, parsed_date = row
        # Determine format based on the original string
        if "-" in trans_date:
            parsed_format = "YYYY-MM-DD"
        elif "/" in trans_date:
            # Check if it has leading zeros
            parts = trans_date.split("/")
            if len(parts[0]) == 2 or len(parts[1]) == 2:
                parsed_format = "MM/DD/YYYY"
            else:
                parsed_format = "M/D/YYYY"
        else:
            parsed_format = "Unknown"
        print(f"   ✓ {tracking}: {trans_date} ({parsed_format}) -> {parsed_date}")

    # Verify expected results
    expected_count = (
        5  # Should match: 85, 80, 75 days ago, and both edge cases (89 and 70 days ago)
    )

    if len(result) == expected_count:
        print(f"\n✅ TEST PASSED: Found expected {expected_count} records")
    else:
        print(
            f"\n❌ TEST FAILED: Expected {expected_count} records, but found {len(result)}"
        )

    # Show records that were excluded
    print(f"\n📋 Excluded Records (outside date range or invalid):")
    excluded_query = f"""
        SELECT
            tracking_number,
            transaction_date,
            CASE
                WHEN transaction_date IS NULL THEN 'NULL value'
                WHEN transaction_date = '' THEN 'Empty string'
                ELSE 'Outside date range'
            END as reason
        FROM carrier_invoice_data
        WHERE tracking_number IS NOT NULL
        AND tracking_number LIKE '1Z%'
        AND NOT (
            COALESCE(
                TRY_STRPTIME(transaction_date, '%Y-%m-%d'),
                TRY_STRPTIME(transaction_date, '%m/%d/%Y'),
                TRY_STRPTIME(transaction_date, '%-m/%-d/%Y')
            ) BETWEEN CAST('{start_date_str}' AS DATE) AND CAST('{end_date_str}' AS DATE)
        )
        ORDER BY tracking_number
    """

    excluded_result = conn.execute(excluded_query).fetchall()
    for row in excluded_result:
        tracking, trans_date, reason = row
        print(f"   ✗ {tracking}: {trans_date if trans_date else 'NULL'} ({reason})")

    conn.close()

    return len(result) == expected_count


def cleanup():
    """Remove test database"""
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
        print(f"\n🧹 Cleaned up test database: {TEST_DB_PATH}")


if __name__ == "__main__":
    print("=" * 70)
    print("Testing Mixed Date Format Filtering Logic")
    print("=" * 70)

    try:
        create_test_database()
        test_passed = test_date_filtering()

        if test_passed:
            print("\n" + "=" * 70)
            print("✅ ALL TESTS PASSED")
            print("=" * 70)
            exit(0)
        else:
            print("\n" + "=" * 70)
            print("❌ TESTS FAILED")
            print("=" * 70)
            exit(1)
    finally:
        cleanup()
