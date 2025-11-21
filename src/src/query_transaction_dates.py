#!/usr/bin/env python3
"""
Query Transaction Dates from ClickHouse
========================================

This script queries the ClickHouse table directly to get distinct transaction_date values
without extracting the full dataset.

Usage:
    poetry run python src/src/query_transaction_dates.py

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import os
from datetime import datetime
from dotenv import load_dotenv

# ClickHouse imports
try:
    import clickhouse_connect
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False
    print("⚠️ clickhouse_connect not available")


def query_transaction_dates():
    """Query distinct transaction_date values from ClickHouse"""
    
    if not CLICKHOUSE_AVAILABLE:
        print("❌ ClickHouse library not available. Please install clickhouse-connect.")
        return
    
    # Load environment variables
    load_dotenv()
    
    print("🚀 Querying Transaction Dates from ClickHouse")
    print("=" * 60)
    
    # Validate required environment variables
    required_vars = [
        "CLICKHOUSE_HOST",
        "CLICKHOUSE_USERNAME",
        "CLICKHOUSE_PASSWORD",
        "CLICKHOUSE_DATABASE",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return
    
    try:
        # Disable SSL warnings
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Connect to ClickHouse
        client = clickhouse_connect.get_client(
            host=os.getenv("CLICKHOUSE_HOST"),
            port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
            username=os.getenv("CLICKHOUSE_USERNAME"),
            password=os.getenv("CLICKHOUSE_PASSWORD"),
            database=os.getenv("CLICKHOUSE_DATABASE"),
            secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true",
            connect_timeout=60,
            send_receive_timeout=300,
            verify=False,
        )
        
        print(f"✅ Connected to ClickHouse: {os.getenv('CLICKHOUSE_HOST')}")
        
        table_name = "carrier_carrier_invoice_original_flat_ups"
        
        # Query 1: Get min/max transaction_date
        print(f"\n📅 Query 1: Min/Max transaction_date")
        print("-" * 60)
        query1 = f"""
        SELECT 
            MIN(transaction_date) as min_date,
            MAX(transaction_date) as max_date,
            COUNT(DISTINCT transaction_date) as distinct_dates,
            COUNT(*) as total_rows
        FROM {table_name}
        WHERE transaction_date IS NOT NULL AND transaction_date != ''
        """
        result1 = client.query(query1)
        if result1.result_rows:
            min_date, max_date, distinct_dates, total_rows = result1.result_rows[0]
            print(f"   📊 Min transaction_date: {min_date}")
            print(f"   📊 Max transaction_date: {max_date}")
            print(f"   📊 Distinct dates: {distinct_dates:,}")
            print(f"   📊 Total rows: {total_rows:,}")
        
        # Query 2: Get all distinct transaction_date values (sorted)
        print(f"\n📅 Query 2: All Distinct transaction_date values")
        print("-" * 60)
        query2 = f"""
        SELECT DISTINCT transaction_date
        FROM {table_name}
        WHERE transaction_date IS NOT NULL AND transaction_date != ''
        ORDER BY transaction_date DESC
        """
        result2 = client.query(query2)
        if result2.result_rows:
            print(f"   Found {len(result2.result_rows):,} distinct transaction dates:")
            print()
            for i, (date,) in enumerate(result2.result_rows, 1):
                print(f"   {i:4d}. {date}")
        
        # Query 3: Count records per transaction_date (top 20)
        print(f"\n📅 Query 3: Top 20 transaction_date by record count")
        print("-" * 60)
        query3 = f"""
        SELECT 
            transaction_date,
            COUNT(*) as record_count
        FROM {table_name}
        WHERE transaction_date IS NOT NULL AND transaction_date != ''
        GROUP BY transaction_date
        ORDER BY transaction_date DESC
        LIMIT 20
        """
        result3 = client.query(query3)
        if result3.result_rows:
            print(f"   {'Date':<15} {'Record Count':>15}")
            print(f"   {'-'*15} {'-'*15}")
            for date, count in result3.result_rows:
                print(f"   {date:<15} {count:>15,}")
        
        # Query 4: Check specific date ranges
        print(f"\n📅 Query 4: Checking specific date ranges")
        print("-" * 60)
        
        # Calculate target dates
        from datetime import timedelta
        today = datetime.utcnow().date()
        
        # 89-79 days ago (current filter range)
        start_89 = (today - timedelta(days=89)).strftime("%Y-%m-%d")
        end_79 = (today - timedelta(days=79)).strftime("%Y-%m-%d")
        
        # 89-01 days ago (updated filter range)
        start_89_v2 = (today - timedelta(days=89)).strftime("%Y-%m-%d")
        end_01 = (today - timedelta(days=1)).strftime("%Y-%m-%d")
        
        print(f"\n   Range 1: {start_89} to {end_79} (89-79 days ago)")
        query4a = f"""
        SELECT COUNT(*) as count
        FROM {table_name}
        WHERE transaction_date >= '{start_89}' AND transaction_date <= '{end_79}'
        """
        result4a = client.query(query4a)
        if result4a.result_rows:
            count = result4a.result_rows[0][0]
            print(f"   📊 Records found: {count:,}")
        
        print(f"\n   Range 2: {start_89_v2} to {end_01} (89-1 days ago)")
        query4b = f"""
        SELECT COUNT(*) as count
        FROM {table_name}
        WHERE transaction_date >= '{start_89_v2}' AND transaction_date <= '{end_01}'
        """
        result4b = client.query(query4b)
        if result4b.result_rows:
            count = result4b.result_rows[0][0]
            print(f"   📊 Records found: {count:,}")
        
        print(f"\n✅ Query completed successfully!")
        
    except Exception as e:
        print(f"❌ Query failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    query_transaction_dates()

