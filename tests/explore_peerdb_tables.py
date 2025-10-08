#!/usr/bin/env python3
"""
PeerDB Database Explorer
=======================

Comprehensive exploration of PeerDB database to find all tables and schemas.

Usage:
    poetry run python tests/explore_peerdb_tables.py

This script will:
1. List all databases
2. List all tables in each database
3. Search for tables containing 'login' or 'index'
4. Show table schemas for potential matches

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import os
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


def explore_peerdb_database():
    """Comprehensive exploration of PeerDB database structure"""
    
    if not CLICKHOUSE_AVAILABLE:
        print("❌ ClickHouse library not available")
        return False
    
    print("🔍 PeerDB Database Explorer")
    print("=" * 50)
    
    # Get connection details from environment
    host = os.getenv("CLICKHOUSE_HOST")
    port = int(os.getenv("CLICKHOUSE_PORT", "8443"))
    username = os.getenv("CLICKHOUSE_USERNAME")
    password = os.getenv("CLICKHOUSE_PASSWORD")
    database = os.getenv("CLICKHOUSE_DATABASE", "peerdb")
    secure = os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true"
    
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
            verify=False,
        )
        
        print(f"✅ Connected to PeerDB: {host}:{port}/{database}")
        
        # 1. List all databases
        print(f"\n📂 Available databases:")
        try:
            databases_result = client.query("SHOW DATABASES")
            databases = [row[0] for row in databases_result.result_rows]
            for db in sorted(databases):
                print(f"   - {db}")
        except Exception as e:
            print(f"   ❌ Error listing databases: {e}")
        
        # 2. List all tables in current database
        print(f"\n📋 Tables in '{database}' database:")
        try:
            tables_result = client.query("SHOW TABLES")
            tables = [row[0] for row in tables_result.result_rows]
            for table in sorted(tables):
                print(f"   - {table}")
        except Exception as e:
            print(f"   ❌ Error listing tables: {e}")
            return False
        
        # 3. Search for tables with 'login' or 'index' in name
        print(f"\n🔍 Searching for tables containing 'login' or 'index':")
        matching_tables = []
        for table in tables:
            if any(keyword in table.lower() for keyword in ['login', 'index', 'industry']):
                matching_tables.append(table)
                print(f"   ✅ Found: {table}")
        
        if not matching_tables:
            print("   ❌ No tables found containing 'login', 'index', or 'industry'")
        
        # 4. Check if there are other databases we should explore
        print(f"\n🔍 Exploring other databases for industry_index_logins table:")
        for db_name in databases:
            if db_name != database and db_name not in ['system', 'information_schema', 'INFORMATION_SCHEMA']:
                try:
                    print(f"\n   📂 Checking database: {db_name}")
                    
                    # Switch to the database
                    client.command(f"USE {db_name}")
                    
                    # List tables in this database
                    db_tables_result = client.query("SHOW TABLES")
                    db_tables = [row[0] for row in db_tables_result.result_rows]
                    
                    print(f"      Tables in {db_name}: {len(db_tables)}")
                    
                    # Look for our target table
                    target_found = False
                    for table in db_tables:
                        if 'industry_index_logins' in table.lower():
                            print(f"      ✅ FOUND TARGET: {table}")
                            target_found = True
                        elif any(keyword in table.lower() for keyword in ['login', 'index', 'industry']):
                            print(f"      🔍 Related: {table}")
                    
                    if target_found:
                        return explore_target_table(client, db_name, 'industry_index_logins')
                    
                except Exception as e:
                    print(f"      ❌ Error exploring {db_name}: {e}")
        
        # 5. If not found, show detailed info about existing tables
        print(f"\n📊 Detailed analysis of existing tables:")
        client.command(f"USE {database}")  # Switch back to original database
        
        for table in tables[:5]:  # Limit to first 5 tables to avoid too much output
            try:
                print(f"\n   📋 Table: {table}")
                
                # Get record count
                count_result = client.query(f"SELECT COUNT(*) FROM {table}")
                count = count_result.result_rows[0][0]
                print(f"      Records: {count:,}")
                
                # Get schema (first few columns)
                schema_result = client.query(f"DESCRIBE TABLE {table}")
                print(f"      Columns ({len(schema_result.result_rows)}):")
                for i, row in enumerate(schema_result.result_rows[:5]):
                    print(f"        {row[0]}: {row[1]}")
                if len(schema_result.result_rows) > 5:
                    print(f"        ... and {len(schema_result.result_rows) - 5} more columns")
                
            except Exception as e:
                print(f"      ❌ Error analyzing {table}: {e}")
        
        # 6. Final recommendation
        print(f"\n💡 Recommendations:")
        print(f"   1. The table 'industry_index_logins' was not found in any database")
        print(f"   2. Available tables are carrier invoice related")
        print(f"   3. You may need to:")
        print(f"      - Verify the correct table name with your data team")
        print(f"      - Check if the table exists in a different ClickHouse instance")
        print(f"      - Confirm if the table has been created yet")
        
        return False
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def explore_target_table(client, database, table_name):
    """Explore the target table if found"""
    
    print(f"\n🎯 Found target table: {database}.{table_name}")
    print("=" * 50)
    
    try:
        # Get table schema
        schema_result = client.query(f"DESCRIBE TABLE {table_name}")
        print(f"📋 Table schema:")
        columns = []
        for row in schema_result.result_rows:
            column_name = row[0]
            column_type = row[1]
            columns.append(column_name)
            print(f"   {column_name}: {column_type}")
        
        # Get record count
        count_result = client.query(f"SELECT COUNT(*) FROM {table_name}")
        total_count = count_result.result_rows[0][0]
        print(f"\n📊 Total records: {total_count:,}")
        
        if total_count > 0:
            # Show sample data
            print(f"\n📄 Sample data (first 3 records):")
            sample_result = client.query(f"SELECT * FROM {table_name} LIMIT 3")
            
            for i, row in enumerate(sample_result.result_rows, 1):
                print(f"\n   Record {i}:")
                for col_name, value in zip(columns, row):
                    display_value = str(value)
                    if len(display_value) > 50:
                        display_value = display_value[:47] + "..."
                    print(f"     {col_name}: {display_value}")
        
        print(f"\n✅ Target table found and analyzed!")
        print(f"📍 Full table path: {database}.{table_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error exploring target table: {e}")
        return False


if __name__ == "__main__":
    print("🔍 PeerDB Database Explorer")
    print("=" * 50)
    
    success = explore_peerdb_database()
    
    if not success:
        print(f"\n❌ Target table 'industry_index_logins' not found")
        print(f"\n🤔 Possible next steps:")
        print(f"   1. Contact your data team to verify the table name")
        print(f"   2. Check if the table exists in a different database/schema")
        print(f"   3. Verify if the table has been created in PeerDB yet")
        print(f"   4. Consider using one of the existing carrier tables for testing")
