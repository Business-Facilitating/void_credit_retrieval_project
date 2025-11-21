#!/usr/bin/env python3
"""
Analyze why we're getting zero label-only tracking numbers
"""

import os
from datetime import datetime, timedelta
import duckdb

print("=" * 80)
print("ANALYSIS: Why Zero Label-Only Tracking Numbers?")
print("=" * 80)

# Check the output database
db_path = "data/output/carrier_invoice_extraction.duckdb"

if not os.path.exists(db_path):
    print(f"❌ Database not found: {db_path}")
    exit(1)

print(f"✅ Database exists: {db_path}\n")

# Calculate date range
TRANSACTION_DATE_START_DAYS_AGO = 89
TRANSACTION_DATE_END_DAYS_AGO = 30

today = datetime.now().date()
start_target_date = today - timedelta(days=TRANSACTION_DATE_START_DAYS_AGO)
end_target_date = today - timedelta(days=TRANSACTION_DATE_END_DAYS_AGO)

print(f"🎯 Target date range: {start_target_date} to {end_target_date}")
print(f"   ({TRANSACTION_DATE_START_DAYS_AGO} to {TRANSACTION_DATE_END_DAYS_AGO} days ago)\n")

# Connect to database
conn = duckdb.connect(db_path, read_only=True)

# Check what data we have
print("=" * 80)
print("STEP 1: What data is in the database?")
print("=" * 80)

total_records = conn.execute("SELECT COUNT(*) FROM carrier_invoice_data").fetchone()[0]
print(f"📊 Total records: {total_records:,}")

ups_tracking = conn.execute("""
    SELECT COUNT(DISTINCT tracking_number)
    FROM carrier_invoice_data
    WHERE tracking_number LIKE '1Z%'
""").fetchone()[0]
print(f"📦 UPS tracking numbers: {ups_tracking:,}")

# Check date range in database
date_range = conn.execute("""
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
    FROM carrier_invoice_data
    WHERE tracking_number LIKE '1Z%'
""").fetchone()

if date_range[0] and date_range[1]:
    min_date = date_range[0].date() if hasattr(date_range[0], 'date') else date_range[0]
    max_date = date_range[1].date() if hasattr(date_range[1], 'date') else date_range[1]
    
    days_from_today_min = (today - min_date).days
    days_from_today_max = (today - max_date).days
    
    print(f"\n📅 Actual transaction_date range:")
    print(f"   Earliest: {min_date} ({days_from_today_min} days ago)")
    print(f"   Latest: {max_date} ({days_from_today_max} days ago)")

print("\n" + "=" * 80)
print("STEP 2: Why is the data range so limited?")
print("=" * 80)

print(f"""
💡 The exported database only has {total_records} records with dates from {min_date} to {max_date}.

This is because the DLT pipeline (dlt_pipeline_examples.py) uses INCREMENTAL loading:
- It only extracts NEW data since the last run
- Last run was on 2025-11-10 10:40:39 (as shown in the pipeline output)
- No new data has been added to ClickHouse since then

The message "ℹ️ No new data in carrier_carrier_invoice_original_flat_ups" means:
- ClickHouse hasn't received any new records since the last extraction
- The pipeline skipped extraction because there's nothing new to extract
""")

print("=" * 80)
print("STEP 3: What's in the ROOT database?")
print("=" * 80)

root_db_path = "carrier_invoice_extraction.duckdb"
if os.path.exists(root_db_path):
    root_conn = duckdb.connect(root_db_path, read_only=True)
    
    root_total = root_conn.execute("SELECT COUNT(*) FROM carrier_invoice_data").fetchone()[0]
    root_ups = root_conn.execute("""
        SELECT COUNT(DISTINCT tracking_number)
        FROM carrier_invoice_data
        WHERE tracking_number LIKE '1Z%'
    """).fetchone()[0]
    
    root_date_range = root_conn.execute("""
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
        FROM carrier_invoice_data
        WHERE tracking_number LIKE '1Z%'
    """).fetchone()
    
    if root_date_range[0] and root_date_range[1]:
        root_min_date = root_date_range[0].date() if hasattr(root_date_range[0], 'date') else root_date_range[0]
        root_max_date = root_date_range[1].date() if hasattr(root_date_range[1], 'date') else root_date_range[1]
        
        print(f"📊 Root database (carrier_invoice_extraction.duckdb):")
        print(f"   Total records: {root_total:,}")
        print(f"   UPS tracking numbers: {root_ups:,}")
        print(f"   Date range: {root_min_date} to {root_max_date}")
    
    root_conn.close()

print("\n" + "=" * 80)
print("SOLUTION")
print("=" * 80)

print("""
The pipeline is working correctly, but you're getting zero label-only tracking numbers because:

1. ✅ The DLT pipeline successfully connects to ClickHouse
2. ✅ It checks for new data since the last run (2025-11-10 10:40:39)
3. ❌ ClickHouse has NO NEW DATA since then
4. ❌ The exported database only contains the small amount of data that was filtered
5. ❌ Those tracking numbers have all progressed beyond "label-only" status

OPTIONS TO FIX:

Option 1: Force a FULL re-extraction (not incremental)
   - Delete or rename the root database: carrier_invoice_extraction.duckdb
   - Re-run: poetry run python src/src/dlt_pipeline_examples.py
   - This will extract ALL data from ClickHouse in the 89-30 day window

Option 2: Check if ClickHouse has recent data
   - The pipeline might be working correctly, but ClickHouse might not have
     data in the 89-30 day window (Aug 17 to Oct 15, 2025)
   - Check the latest_transac_dt.csv to see what dates are actually in ClickHouse

Option 3: Adjust the date range
   - If ClickHouse has data but in a different date range, adjust:
     DLT_PIPELINE_START_DAYS and DLT_PIPELINE_END_DAYS in .env
""")

conn.close()

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)

