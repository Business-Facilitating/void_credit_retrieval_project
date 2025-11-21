#!/usr/bin/env python3
"""
Debug script to investigate why ups_label_only_filter.py returns no tracking numbers
"""

import os
from datetime import datetime, timedelta
import duckdb
from dotenv import load_dotenv

load_dotenv()

# Configuration
DUCKDB_PATH = os.getenv("DUCKDB_PATH", "carrier_invoice_extraction.duckdb")
TABLE_NAME = "carrier_invoice_extraction.carrier_invoice_data"

# Date configuration (same as ups_label_only_filter.py)
TRANSACTION_DATE_START_DAYS_AGO = int(os.getenv("UPS_FILTER_START_DAYS", "89"))
TRANSACTION_DATE_END_DAYS_AGO = int(os.getenv("UPS_FILTER_END_DAYS", "30"))

print("=" * 80)
print("DEBUG: Investigating why ups_label_only_filter.py returns no tracking numbers")
print("=" * 80)

# Calculate target date range
today = datetime.now().date()
start_target_date = today - timedelta(days=TRANSACTION_DATE_START_DAYS_AGO)
end_target_date = today - timedelta(days=TRANSACTION_DATE_END_DAYS_AGO)

print(f"\n📅 Today's date: {today}")
print(f"🎯 Target date range: {start_target_date} to {end_target_date}")
print(f"   ({TRANSACTION_DATE_START_DAYS_AGO} to {TRANSACTION_DATE_END_DAYS_AGO} days ago)")

# Check if database exists
if not os.path.exists(DUCKDB_PATH):
    print(f"\n❌ ERROR: Database file not found: {DUCKDB_PATH}")
    print("   Run dlt_pipeline_examples.py first to create the database")
    exit(1)

print(f"\n✅ Database file exists: {DUCKDB_PATH}")

# Connect to DuckDB
conn = duckdb.connect(DUCKDB_PATH, read_only=True)

# Check if table exists
try:
    table_check = conn.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()
    total_records = table_check[0]
    print(f"✅ Table exists: {TABLE_NAME}")
    print(f"📊 Total records in table: {total_records:,}")
except Exception as e:
    print(f"❌ ERROR: Table not found or error accessing table: {e}")
    conn.close()
    exit(1)

# Check UPS tracking numbers
print("\n" + "=" * 80)
print("STEP 1: Check total UPS tracking numbers (1Z%)")
print("=" * 80)

query1 = f"""
    SELECT COUNT(DISTINCT tracking_number) as count
    FROM {TABLE_NAME}
    WHERE tracking_number IS NOT NULL
    AND tracking_number != ''
    AND tracking_number LIKE '1Z%'
"""
result1 = conn.execute(query1).fetchone()
print(f"📊 Total distinct UPS tracking numbers: {result1[0]:,}")

# Check transaction_date distribution
print("\n" + "=" * 80)
print("STEP 2: Check transaction_date distribution")
print("=" * 80)

query2 = f"""
    SELECT 
        transaction_date,
        COUNT(*) as count,
        COUNT(DISTINCT tracking_number) as distinct_tracking
    FROM {TABLE_NAME}
    WHERE tracking_number IS NOT NULL
    AND tracking_number LIKE '1Z%'
    GROUP BY transaction_date
    ORDER BY transaction_date DESC
    LIMIT 20
"""
result2 = conn.execute(query2).fetchall()
print(f"\n📋 Top 20 most recent transaction_date values:")
print(f"{'Transaction Date':<20} {'Records':<15} {'Distinct Tracking':<20}")
print("-" * 60)
for row in result2:
    print(f"{str(row[0]):<20} {row[1]:<15,} {row[2]:<20,}")

# Check if any dates can be parsed
print("\n" + "=" * 80)
print("STEP 3: Check date parsing success rate")
print("=" * 80)

query3 = f"""
    SELECT 
        COUNT(*) as total_records,
        COUNT(CASE 
            WHEN COALESCE(
                TRY_STRPTIME(transaction_date, '%Y-%m-%d'),
                TRY_STRPTIME(transaction_date, '%m/%d/%Y'),
                TRY_STRPTIME(transaction_date, '%-m/%-d/%Y')
            ) IS NOT NULL THEN 1 
        END) as parseable_dates,
        COUNT(CASE 
            WHEN COALESCE(
                TRY_STRPTIME(transaction_date, '%Y-%m-%d'),
                TRY_STRPTIME(transaction_date, '%m/%d/%Y'),
                TRY_STRPTIME(transaction_date, '%-m/%-d/%Y')
            ) IS NULL THEN 1 
        END) as unparseable_dates
    FROM {TABLE_NAME}
    WHERE tracking_number IS NOT NULL
    AND tracking_number LIKE '1Z%'
"""
result3 = conn.execute(query3).fetchone()
print(f"📊 Total UPS tracking records: {result3[0]:,}")
print(f"✅ Parseable dates: {result3[1]:,} ({result3[1]/result3[0]*100:.1f}%)")
print(f"❌ Unparseable dates: {result3[2]:,} ({result3[2]/result3[0]*100:.1f}%)")

# Check records in target date range
print("\n" + "=" * 80)
print("STEP 4: Check records in target date range")
print("=" * 80)

start_date_str = start_target_date.strftime("%Y-%m-%d")
end_date_str = end_target_date.strftime("%Y-%m-%d")

query4 = f"""
    SELECT COUNT(DISTINCT tracking_number) as count
    FROM {TABLE_NAME}
    WHERE tracking_number IS NOT NULL
    AND tracking_number != ''
    AND tracking_number LIKE '1Z%'
    AND (
        COALESCE(
            TRY_STRPTIME(transaction_date, '%Y-%m-%d'),
            TRY_STRPTIME(transaction_date, '%m/%d/%Y'),
            TRY_STRPTIME(transaction_date, '%-m/%-d/%Y')
        ) BETWEEN CAST('{start_date_str}' AS DATE) AND CAST('{end_date_str}' AS DATE)
    )
"""
result4 = conn.execute(query4).fetchone()
print(f"🎯 Target range: {start_date_str} to {end_date_str}")
print(f"📊 Distinct tracking numbers in range: {result4[0]:,}")

if result4[0] == 0:
    print("\n⚠️ NO TRACKING NUMBERS FOUND IN TARGET DATE RANGE!")
    print("\nLet's check what date ranges actually exist in the data...")
    
    query5 = f"""
        SELECT 
            MIN(COALESCE(
                TRY_STRPTIME(transaction_date, '%Y-%m-%d'),
                TRY_STRPTIME(transaction_date, '%m/%d/%Y'),
                TRY_STRPTIME(transaction_date, '%-m/%-d/%Y')
            )) as min_date,
            MAX(COALESCE(
                TRY_STRPTIME(transaction_date, '%Y-%m-%d'),
                TRY_STRPTIME(transaction_date, '%m/%d/%Y'),
                TRY_STRPTIME(transaction_date, '%-m/%-d/%Y')
            )) as max_date
        FROM {TABLE_NAME}
        WHERE tracking_number IS NOT NULL
        AND tracking_number LIKE '1Z%'
    """
    result5 = conn.execute(query5).fetchone()
    print(f"\n📅 Actual date range in database:")
    print(f"   Earliest: {result5[0]}")
    print(f"   Latest: {result5[1]}")
    
    if result5[0] and result5[1]:
        min_date = result5[0].date() if hasattr(result5[0], 'date') else result5[0]
        max_date = result5[1].date() if hasattr(result5[1], 'date') else result5[1]
        
        days_from_today_min = (today - min_date).days
        days_from_today_max = (today - max_date).days
        
        print(f"\n📊 Days from today:")
        print(f"   Earliest date is {days_from_today_min} days ago")
        print(f"   Latest date is {days_from_today_max} days ago")
        
        print(f"\n💡 RECOMMENDATION:")
        print(f"   Your current filter is looking for dates {TRANSACTION_DATE_START_DAYS_AGO}-{TRANSACTION_DATE_END_DAYS_AGO} days ago")
        print(f"   But your data ranges from {days_from_today_min} to {days_from_today_max} days ago")
        print(f"\n   To extract data, adjust the configuration variables in ups_label_only_filter.py:")
        print(f"   TRANSACTION_DATE_START_DAYS_AGO = {days_from_today_min}")
        print(f"   TRANSACTION_DATE_END_DAYS_AGO = {days_from_today_max}")

conn.close()

print("\n" + "=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)

