#!/usr/bin/env python3
"""
Test DuckDB Date Parsing
=========================

This script tests how DuckDB's TRY_CAST handles different date formats.
"""

from datetime import datetime, timedelta

import duckdb

# Create in-memory database
conn = duckdb.connect(":memory:")

# Create test table
conn.execute(
    """
    CREATE TABLE test_dates (
        id INT,
        date_str VARCHAR,
        format_desc VARCHAR
    )
"""
)

# Calculate test dates
today = datetime.now()


# Helper function to format date as M/D/YYYY (without leading zeros)
def format_single_digit_date(dt):
    """Format date as M/D/YYYY without leading zeros"""
    return f"{dt.month}/{dt.day}/{dt.year}"


# Insert test data
test_data = [
    (1, (today - timedelta(days=85)).strftime("%Y-%m-%d"), "YYYY-MM-DD (ISO)"),
    (2, (today - timedelta(days=80)).strftime("%m/%d/%Y"), "MM/DD/YYYY (padded)"),
    (
        3,
        format_single_digit_date(today - timedelta(days=75)),
        "M/D/YYYY (single digit)",
    ),
    (4, "2024-01-15", "YYYY-MM-DD literal"),
    (5, "01/15/2024", "MM/DD/YYYY literal"),
    (6, "1/15/2024", "M/D/YYYY literal"),
    (7, "8/5/2024", "M/D/YYYY literal (single digits)"),
    (8, "12/27/2023", "MM/DD/YYYY literal"),
    (9, "", "Empty string"),
    (10, None, "NULL value"),
]

for id_val, date_str, desc in test_data:
    if date_str is None:
        conn.execute("INSERT INTO test_dates VALUES (?, NULL, ?)", [id_val, desc])
    else:
        conn.execute(
            "INSERT INTO test_dates VALUES (?, ?, ?)", [id_val, date_str, desc]
        )

# Test TRY_CAST parsing
print("=" * 80)
print("Testing DuckDB TRY_CAST Date Parsing")
print("=" * 80)
print()

query = """
    SELECT
        id,
        date_str,
        format_desc,
        TRY_CAST(date_str AS DATE) as parsed_date,
        CASE
            WHEN TRY_CAST(date_str AS DATE) IS NOT NULL THEN '✓ Parsed'
            ELSE '✗ Failed'
        END as status
    FROM test_dates
    ORDER BY id
"""

result = conn.execute(query).fetchall()

print(
    f"{'ID':<4} {'Original String':<20} {'Format':<30} {'Parsed Date':<15} {'Status'}"
)
print("-" * 80)

for row in result:
    id_val, date_str, format_desc, parsed_date, status = row
    date_str_display = date_str if date_str else "NULL"
    parsed_date_display = str(parsed_date) if parsed_date else "NULL"
    print(
        f"{id_val:<4} {date_str_display:<20} {format_desc:<30} {parsed_date_display:<15} {status}"
    )

print()
print("=" * 80)
print("Testing DuckDB COALESCE + TRY_STRPTIME Date Parsing")
print("=" * 80)
print()

query2 = """
    SELECT
        id,
        date_str,
        format_desc,
        COALESCE(
            TRY_STRPTIME(date_str, '%Y-%m-%d'),  -- YYYY-MM-DD
            TRY_STRPTIME(date_str, '%m/%d/%Y'),  -- MM/DD/YYYY
            TRY_STRPTIME(date_str, '%-m/%-d/%Y')   -- M/D/YYYY (single digit)
        ) as parsed_date,
        CASE
            WHEN COALESCE(
                TRY_STRPTIME(date_str, '%Y-%m-%d'),
                TRY_STRPTIME(date_str, '%m/%d/%Y'),
                TRY_STRPTIME(date_str, '%-m/%-d/%Y')
            ) IS NOT NULL THEN '✓ Parsed'
            ELSE '✗ Failed'
        END as status
    FROM test_dates
    ORDER BY id
"""

result2 = conn.execute(query2).fetchall()

print(
    f"{'ID':<4} {'Original String':<20} {'Format':<30} {'Parsed Date':<15} {'Status'}"
)
print("-" * 80)

for row in result2:
    id_val, date_str, format_desc, parsed_date, status = row
    date_str_display = date_str if date_str else "NULL"
    parsed_date_display = str(parsed_date) if parsed_date else "NULL"
    print(
        f"{id_val:<4} {date_str_display:<20} {format_desc:<30} {parsed_date_display:<15} {status}"
    )

print()
print("=" * 80)
print("Summary:")
print("=" * 80)

# Count successful parses
success_count = sum(1 for row in result2 if row[3] is not None)
total_count = len(result2)
print(
    f"Successfully parsed with COALESCE + TRY_STRPTIME: {success_count}/{total_count}"
)

conn.close()
