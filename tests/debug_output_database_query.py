#!/usr/bin/env python3
"""
Debug why ups_label_only_filter.py can't find tracking numbers in the output database
"""

import os
from datetime import datetime, timedelta
import duckdb

print("=" * 80)
print("DEBUG: Query Output Database with Same Logic as ups_label_only_filter.py")
print("=" * 80)

db_path = "data/output/carrier_invoice_extraction.duckdb"
table_name = "carrier_invoice_extraction.carrier_invoice_data"

if not os.path.exists(db_path):
    print(f"❌ Database not found: {db_path}")
    exit(1)

print(f"✅ Database exists: {db_path}")

# Calculate date range (same as ups_label_only_filter.py)
TRANSACTION_DATE_START_DAYS_AGO = 89
TRANSACTION_DATE_END_DAYS_AGO = 30

today = datetime.now().date()
start_target_date = today - timedelta(days=TRANSACTION_DATE_START_DAYS_AGO)
end_target_date = today - timedelta(days=TRANSACTION_DATE_END_DAYS_AGO)
start_date_str = start_target_date.strftime("%Y-%m-%d")
end_date_str = end_target_date.strftime("%Y-%m-%d")

print(f"\n🎯 Target date range: {start_date_str} to {end_date_str}")
print(f"   ({TRANSACTION_DATE_START_DAYS_AGO} to {TRANSACTION_DATE_END_DAYS_AGO} days ago)")

# Connect to database
conn = duckdb.connect(db_path, read_only=True)

# Check if table exists
try:
    tables = conn.execute("SHOW TABLES").fetchall()
    print(f"\n📋 Tables in database: {[t[0] for t in tables]}")
    
    # Try different table name variations
    table_variations = [
        "carrier_invoice_extraction.carrier_invoice_data",
        "carrier_invoice_data"
    ]
    
    for table_var in table_variations:
        print(f"\n{'=' * 80}")
        print(f"Testing table name: {table_var}")
        print("=" * 80)
        
        try:
            # Check total records
            total = conn.execute(f"SELECT COUNT(*) FROM {table_var}").fetchone()[0]
            print(f"✅ Table exists: {table_var}")
            print(f"📊 Total records: {total:,}")
            
            # Check UPS tracking numbers
            ups_total = conn.execute(f"""
                SELECT COUNT(DISTINCT tracking_number)
                FROM {table_var}
                WHERE tracking_number LIKE '1Z%'
            """).fetchone()[0]
            print(f"📦 Total UPS tracking numbers: {ups_total:,}")
            
            # Check with date filtering (same logic as ups_label_only_filter.py)
            query = f"""
                SELECT COUNT(DISTINCT tracking_number)
                FROM {table_var}
                WHERE tracking_number IS NOT NULL
                AND tracking_number != ''
                AND LENGTH(TRIM(tracking_number)) > 0
                AND tracking_number LIKE '1Z%'
                AND (
                    COALESCE(
                        TRY_STRPTIME(transaction_date, '%Y-%m-%d'),
                        TRY_STRPTIME(transaction_date, '%m/%d/%Y'),
                        TRY_STRPTIME(transaction_date, '%-m/%-d/%Y')
                    ) BETWEEN CAST('{start_date_str}' AS DATE) AND CAST('{end_date_str}' AS DATE)
                )
            """
            
            result = conn.execute(query).fetchone()[0]
            print(f"\n🎯 UPS tracking numbers in date range ({start_date_str} to {end_date_str}): {result:,}")
            
            # Show actual date range in the table
            date_range_query = f"""
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
                FROM {table_var}
                WHERE tracking_number LIKE '1Z%'
            """
            
            date_range = conn.execute(date_range_query).fetchone()
            if date_range[0] and date_range[1]:
                min_date = date_range[0].date() if hasattr(date_range[0], 'date') else date_range[0]
                max_date = date_range[1].date() if hasattr(date_range[1], 'date') else date_range[1]
                
                days_from_today_min = (today - min_date).days
                days_from_today_max = (today - max_date).days
                
                print(f"\n📅 Actual transaction_date range in table:")
                print(f"   Earliest: {min_date} ({days_from_today_min} days ago)")
                print(f"   Latest: {max_date} ({days_from_today_max} days ago)")
                
                # Show sample records
                sample_query = f"""
                    SELECT tracking_number, transaction_date
                    FROM {table_var}
                    WHERE tracking_number LIKE '1Z%'
                    LIMIT 5
                """
                samples = conn.execute(sample_query).fetchall()
                print(f"\n📋 Sample records:")
                for i, (tn, td) in enumerate(samples, 1):
                    print(f"   {i}. {tn} | {td}")
            
        except Exception as e:
            print(f"❌ Error with table name '{table_var}': {e}")
            continue

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    conn.close()

print("\n" + "=" * 80)
print("DEBUG COMPLETE")
print("=" * 80)

