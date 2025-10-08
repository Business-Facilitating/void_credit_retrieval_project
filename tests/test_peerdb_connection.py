#!/usr/bin/env python3
"""
PeerDB Connection Test
=====================

Test script to verify PeerDB connection and explore the industry_index_logins table structure.

Usage:
    poetry run python tests/test_peerdb_connection.py

This script will:
1. Test connection to PeerDB ClickHouse database
2. Show table schema for industry_index_logins
3. Display sample data
4. Show record counts and basic statistics

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import os
from datetime import datetime
from dotenv import load_dotenv

# ClickHouse imports with fallback handling
try:
    import clickhouse_connect
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False
    print("❌ clickhouse_connect not available. Install with: pip install clickhouse-connect")

# Load environment variables
load_dotenv()


def test_peerdb_connection():
    """Test connection to PeerDB and explore the industry_index_logins table"""
    
    if not CLICKHOUSE_AVAILABLE:
        print("❌ ClickHouse library not available")
        return False
    
    print("🧪 Testing PeerDB Connection")
    print("=" * 40)
    
    # Get connection details from environment
    host = os.getenv("CLICKHOUSE_HOST")
    port = int(os.getenv("CLICKHOUSE_PORT", "8443"))
    username = os.getenv("CLICKHOUSE_USERNAME")
    password = os.getenv("CLICKHOUSE_PASSWORD")
    database = os.getenv("CLICKHOUSE_DATABASE", "peerdb")
    secure = os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true"
    
    if not all([host, username, password]):
        print("❌ Missing required environment variables:")
        print("   - CLICKHOUSE_HOST")
        print("   - CLICKHOUSE_USERNAME") 
        print("   - CLICKHOUSE_PASSWORD")
        print("\n💡 Make sure your .env file is configured correctly")
        return False
    
    print(f"📡 Connecting to PeerDB...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Database: {database}")
    print(f"   Username: {username}")
    print(f"   Secure: {secure}")
    
    try:
        # Create ClickHouse client
        client = clickhouse_connect.get_client(
            host=host,
            port=port,
            username=username,
            password=password,
            database=database,
            secure=secure,
            connect_timeout=60,
            send_receive_timeout=300,
            verify=False,  # Disable SSL verification for cloud connections
        )
        
        # Test basic connection
        result = client.command("SELECT 1 as test")
        print(f"✅ Connection successful! Test result: {result}")
        
        # Show ClickHouse version
        version = client.command("SELECT version()")
        print(f"🗄️ ClickHouse version: {version}")
        
        # Show current database
        current_db = client.command("SELECT currentDatabase()")
        print(f"📂 Current database: {current_db}")
        
        return test_industry_index_logins_table(client)
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def test_industry_index_logins_table(client):
    """Test the industry_index_logins table specifically"""
    
    table_name = "industry_index_logins"
    
    print(f"\n🔍 Exploring table: {table_name}")
    print("=" * 40)
    
    try:
        # Check if table exists
        tables_query = "SHOW TABLES"
        tables_result = client.query(tables_query)
        table_names = [row[0] for row in tables_result.result_rows]
        
        print(f"📋 Available tables in database:")
        for table in sorted(table_names):
            print(f"   - {table}")
        
        if table_name not in table_names:
            print(f"\n❌ Table '{table_name}' not found in database")
            print(f"💡 Available tables: {', '.join(table_names)}")
            return False
        
        print(f"\n✅ Table '{table_name}' found!")
        
        # Get table schema
        print(f"\n📋 Table schema for {table_name}:")
        schema_query = f"DESCRIBE TABLE {table_name}"
        schema_result = client.query(schema_query)
        
        columns = []
        for row in schema_result.result_rows:
            column_name = row[0]
            column_type = row[1]
            columns.append(column_name)
            print(f"   {column_name}: {column_type}")
        
        # Get record count
        count_query = f"SELECT COUNT(*) FROM {table_name}"
        count_result = client.query(count_query)
        total_count = count_result.result_rows[0][0]
        
        print(f"\n📊 Total records: {total_count:,}")
        
        if total_count == 0:
            print("ℹ️ Table is empty")
            return True
        
        # Show sample data (first 5 records)
        print(f"\n📄 Sample data (first 5 records):")
        sample_query = f"SELECT * FROM {table_name} LIMIT 5"
        sample_result = client.query(sample_query)
        
        if sample_result.result_rows:
            for i, row in enumerate(sample_result.result_rows, 1):
                print(f"\n   Record {i}:")
                for col_name, value in zip(columns, row):
                    # Truncate long values for display
                    display_value = str(value)
                    if len(display_value) > 50:
                        display_value = display_value[:47] + "..."
                    print(f"     {col_name}: {display_value}")
        
        # Show date range if there are date columns
        date_columns = []
        for row in schema_result.result_rows:
            column_name = row[0]
            column_type = row[1].lower()
            if any(date_type in column_type for date_type in ['date', 'datetime', 'timestamp']):
                date_columns.append(column_name)
        
        if date_columns:
            print(f"\n📅 Date range analysis:")
            for date_col in date_columns:
                try:
                    date_range_query = f"""
                    SELECT 
                        MIN({date_col}) as min_date,
                        MAX({date_col}) as max_date,
                        COUNT(DISTINCT {date_col}) as unique_dates
                    FROM {table_name}
                    WHERE {date_col} IS NOT NULL
                    """
                    date_result = client.query(date_range_query)
                    if date_result.result_rows:
                        min_date, max_date, unique_dates = date_result.result_rows[0]
                        print(f"   {date_col}: {min_date} to {max_date} ({unique_dates:,} unique dates)")
                except Exception as e:
                    print(f"   {date_col}: Error analyzing - {e}")
        
        print(f"\n✅ Table exploration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to explore table: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_environment_status():
    """Show current environment configuration status"""
    
    print("\n🔧 Environment Configuration Status")
    print("=" * 40)
    
    required_vars = [
        "CLICKHOUSE_HOST",
        "CLICKHOUSE_PORT", 
        "CLICKHOUSE_USERNAME",
        "CLICKHOUSE_PASSWORD",
        "CLICKHOUSE_DATABASE"
    ]
    
    optional_vars = [
        "CLICKHOUSE_SECURE",
        "DLT_WRITE_DISPOSITION",
        "DLT_CLICKHOUSE_BATCH_SIZE",
        "OUTPUT_DIR"
    ]
    
    print("📋 Required variables:")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask password
            if "PASSWORD" in var:
                display_value = "*" * len(value)
            else:
                display_value = value
            print(f"   ✅ {var}: {display_value}")
        else:
            print(f"   ❌ {var}: Not set")
    
    print("\n📋 Optional variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: {value}")
        else:
            print(f"   ⚪ {var}: Using default")


if __name__ == "__main__":
    print("🧪 PeerDB Connection Test")
    print("=" * 50)
    
    # Show environment status
    show_environment_status()
    
    # Test connection and table
    success = test_peerdb_connection()
    
    if success:
        print("\n🎉 All tests passed! Ready to run the PeerDB pipeline.")
        print("\n🚀 Next step: Run the pipeline with:")
        print("   poetry run python src/src/peerdb_pipeline.py")
    else:
        print("\n❌ Tests failed. Please check your configuration.")
        print("\n💡 Troubleshooting:")
        print("   1. Verify your .env file has correct PeerDB credentials")
        print("   2. Check network connectivity to PeerDB")
        print("   3. Verify the table name 'industry_index_logins' exists")
