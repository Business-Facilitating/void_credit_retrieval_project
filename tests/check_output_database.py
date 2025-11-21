#!/usr/bin/env python3
"""
Check the exported database in data/output folder
"""

import os
from datetime import datetime, timedelta
import duckdb

print("=" * 80)
print("Checking Exported Database in data/output/")
print("=" * 80)

# Check both database locations
databases = [
    ("Root directory", "carrier_invoice_extraction.duckdb"),
    ("Output directory", "data/output/carrier_invoice_extraction.duckdb")
]

for name, db_path in databases:
    print(f"\n{'=' * 80}")
    print(f"Checking: {name}")
    print(f"Path: {db_path}")
    print("=" * 80)
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        continue
    
    print(f"✅ Database exists: {db_path}")
    file_size = os.path.getsize(db_path) / (1024 * 1024)
    print(f"📊 File size: {file_size:.1f} MB")
    
    # Connect and check data
    conn = duckdb.connect(db_path, read_only=True)
    
    try:
        # Check table exists
        tables = conn.execute("SHOW TABLES").fetchall()
        print(f"\n📋 Tables: {[t[0] for t in tables]}")
        
        if not tables:
            print("⚠️ No tables found in database")
            conn.close()
            continue
        
        # Check carrier_invoice_data table
        table_name = "carrier_invoice_data"
        total_records = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"\n📊 Total records in {table_name}: {total_records:,}")
        
        if total_records == 0:
            print("⚠️ Table is empty!")
            conn.close()
            continue
        
        # Check UPS tracking numbers
        ups_count = conn.execute(f"""
            SELECT COUNT(DISTINCT tracking_number)
            FROM {table_name}
            WHERE tracking_number LIKE '1Z%'
        """).fetchone()[0]
        print(f"📦 UPS tracking numbers: {ups_count:,}")
        
        # Check date range
        date_range = conn.execute(f"""
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
            FROM {table_name}
            WHERE tracking_number LIKE '1Z%'
        """).fetchone()
        
        if date_range[0] and date_range[1]:
            min_date = date_range[0].date() if hasattr(date_range[0], 'date') else date_range[0]
            max_date = date_range[1].date() if hasattr(date_range[1], 'date') else date_range[1]
            
            today = datetime.now().date()
            days_from_today_min = (today - min_date).days
            days_from_today_max = (today - max_date).days
            
            print(f"\n📅 Transaction date range:")
            print(f"   Earliest: {min_date} ({days_from_today_min} days ago)")
            print(f"   Latest: {max_date} ({days_from_today_max} days ago)")
            
            # Check if data is in the 89-30 day window
            start_days_ago = 89
            end_days_ago = 30
            
            start_target_date = today - timedelta(days=start_days_ago)
            end_target_date = today - timedelta(days=end_days_ago)
            
            print(f"\n🎯 Target range (89-30 days ago):")
            print(f"   {start_target_date} to {end_target_date}")
            
            if max_date >= start_target_date and min_date <= end_target_date:
                print(f"   ✅ Data overlaps with target range!")
            else:
                print(f"   ❌ No overlap with target range")
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
    finally:
        conn.close()

print("\n" + "=" * 80)
print("CHECK COMPLETE")
print("=" * 80)

