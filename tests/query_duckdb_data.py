#!/usr/bin/env python3
"""
DuckDB Data Query Script
========================

This script provides comprehensive querying capabilities for the carrier invoice DuckDB data.
You can query both the main database and the filtered export files.

Usage:
    poetry run python query_duckdb_data.py
"""

import duckdb
import os
from datetime import datetime, timedelta
import pandas as pd


def list_available_databases():
    """List all available DuckDB files."""
    print("🗄️ Available DuckDB Files:")
    print("=" * 50)
    
    # Main database
    main_db = "carrier_invoice_extraction.duckdb"
    if os.path.exists(main_db):
        size_mb = os.path.getsize(main_db) / (1024 * 1024)
        print(f"📊 Main Database: {main_db} ({size_mb:.1f} MB)")
    
    # Export files
    output_dir = "data/output"
    if os.path.exists(output_dir):
        duckdb_files = [f for f in os.listdir(output_dir) if f.endswith('.duckdb')]
        if duckdb_files:
            print(f"\n📁 Export Files in {output_dir}:")
            for file in sorted(duckdb_files):
                file_path = os.path.join(output_dir, file)
                size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"   • {file} ({size_mb:.1f} MB)")
    print()


def get_database_info(db_path):
    """Get basic information about a DuckDB database."""
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print(f"📊 Database Info: {db_path}")
    print("=" * 60)
    
    try:
        conn = duckdb.connect(db_path)
        
        # List tables
        tables = conn.execute("SHOW TABLES").fetchall()
        print(f"📋 Tables: {len(tables)}")
        for table in tables:
            print(f"   • {table[0]}")
        
        # Get record count for main table
        if tables:
            main_table = tables[0][0]  # Assume first table is main
            count = conn.execute(f"SELECT COUNT(*) FROM {main_table}").fetchone()[0]
            print(f"\n📦 Total Records in {main_table}: {count:,}")
            
            # Get column info
            columns = conn.execute(f"DESCRIBE {main_table}").fetchall()
            print(f"📋 Columns: {len(columns)}")
            
            # Show date range if invoice_date exists
            try:
                date_range = conn.execute(f"""
                    SELECT 
                        MIN(invoice_date) as min_date,
                        MAX(invoice_date) as max_date,
                        COUNT(DISTINCT invoice_date) as unique_dates
                    FROM {main_table}
                    WHERE invoice_date IS NOT NULL
                """).fetchone()
                
                if date_range:
                    print(f"📅 Date Range: {date_range[0]} to {date_range[1]}")
                    print(f"📅 Unique Dates: {date_range[2]:,}")
            except:
                pass
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
    
    print()


def query_invoice_date_distribution(db_path):
    """Show distribution of records by invoice_date."""
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print(f"📅 Invoice Date Distribution: {db_path}")
    print("=" * 60)
    
    try:
        conn = duckdb.connect(db_path)
        
        # Get table name
        tables = conn.execute("SHOW TABLES").fetchall()
        if not tables:
            print("❌ No tables found")
            return
        
        table_name = tables[0][0]
        
        # Query date distribution
        result = conn.execute(f"""
            SELECT 
                invoice_date,
                COUNT(*) as record_count,
                COUNT(DISTINCT tracking_number) as unique_tracking_numbers
            FROM {table_name}
            WHERE invoice_date IS NOT NULL
            GROUP BY invoice_date
            ORDER BY invoice_date DESC
            LIMIT 20
        """).fetchall()
        
        if result:
            print("Date           | Records    | Unique Tracking")
            print("-" * 45)
            for row in result:
                print(f"{row[0]:<14} | {row[1]:>8,} | {row[2]:>14,}")
        else:
            print("No data found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
    
    print()


def query_tracking_numbers(db_path, limit=10):
    """Show sample tracking numbers and their details."""
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print(f"📦 Sample Tracking Numbers: {db_path}")
    print("=" * 60)
    
    try:
        conn = duckdb.connect(db_path)
        
        # Get table name
        tables = conn.execute("SHOW TABLES").fetchall()
        if not tables:
            print("❌ No tables found")
            return
        
        table_name = tables[0][0]
        
        # Query sample tracking numbers
        result = conn.execute(f"""
            SELECT 
                tracking_number,
                invoice_date,
                invoice_number,
                sender_company_name,
                receiver_company_name,
                net_amount
            FROM {table_name}
            WHERE tracking_number IS NOT NULL
            ORDER BY invoice_date DESC, tracking_number
            LIMIT {limit}
        """).fetchall()
        
        if result:
            print("Tracking Number    | Invoice Date | Invoice #      | Sender -> Receiver")
            print("-" * 80)
            for row in result:
                sender = (row[3] or "")[:15]
                receiver = (row[4] or "")[:15]
                print(f"{row[0]:<18} | {row[1]:<12} | {row[2]:<14} | {sender} -> {receiver}")
        else:
            print("No tracking numbers found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
    
    print()


def query_custom_sql(db_path, sql_query):
    """Execute a custom SQL query."""
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    print(f"🔍 Custom Query Results: {db_path}")
    print("=" * 60)
    print(f"Query: {sql_query}")
    print("-" * 60)
    
    try:
        conn = duckdb.connect(db_path)
        result = conn.execute(sql_query).fetchall()
        
        if result:
            # Show first few rows
            for i, row in enumerate(result[:20]):  # Limit to first 20 rows
                print(f"Row {i+1}: {row}")
            
            if len(result) > 20:
                print(f"... and {len(result) - 20} more rows")
            
            print(f"\nTotal rows returned: {len(result)}")
        else:
            print("No results returned")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error executing query: {e}")
    
    print()


def main():
    """Main function to demonstrate DuckDB querying."""
    print("🚀 DuckDB Data Query Tool")
    print("=" * 50)
    
    # List available databases
    list_available_databases()
    
    # Analyze main database
    main_db = "carrier_invoice_extraction.duckdb"
    if os.path.exists(main_db):
        get_database_info(main_db)
        query_invoice_date_distribution(main_db)
        query_tracking_numbers(main_db, limit=5)
    
    # Analyze latest export file
    output_dir = "data/output"
    if os.path.exists(output_dir):
        duckdb_files = [f for f in os.listdir(output_dir) if f.endswith('.duckdb')]
        if duckdb_files:
            latest_file = sorted(duckdb_files)[-1]  # Get latest file
            latest_path = os.path.join(output_dir, latest_file)
            
            print(f"🎯 Latest Export Analysis:")
            get_database_info(latest_path)
            query_invoice_date_distribution(latest_path)
            query_tracking_numbers(latest_path, limit=5)
    
    # Example custom queries
    print("💡 Example Custom Queries:")
    print("=" * 50)
    print("1. Count by invoice date:")
    print("   SELECT invoice_date, COUNT(*) FROM carrier_invoice_data GROUP BY invoice_date ORDER BY invoice_date")
    print()
    print("2. Top senders by volume:")
    print("   SELECT sender_company_name, COUNT(*) as shipments FROM carrier_invoice_data GROUP BY sender_company_name ORDER BY shipments DESC LIMIT 10")
    print()
    print("3. Search specific tracking number:")
    print("   SELECT * FROM carrier_invoice_data WHERE tracking_number = '1Z...'")
    print()


if __name__ == "__main__":
    main()
