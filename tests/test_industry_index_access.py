#!/usr/bin/env python3
"""
Test Industry Index Logins Access
=================================

Quick test to verify access to the industry_index_logins table.

Usage:
    poetry run python tests/test_industry_index_access.py

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import os
from dotenv import load_dotenv

# ClickHouse imports
try:
    import clickhouse_connect
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False
    print("❌ clickhouse_connect not available")

# Load environment variables
load_dotenv()


def test_industry_index_access():
    """Test access to industry_index_logins table with different approaches"""
    
    if not CLICKHOUSE_AVAILABLE:
        print("❌ ClickHouse library not available")
        return False
    
    print("🧪 Testing Industry Index Logins Access")
    print("=" * 50)
    
    try:
        # Create ClickHouse client with direct credentials
        client = clickhouse_connect.get_client(
            host="pgy8egpix3.us-east-1.aws.clickhouse.cloud",
            port=8443,
            username="gabriellapuz",
            password="PTN.776)RR3s",
            database="peerdb",
            secure=True,
            connect_timeout=60,
            send_receive_timeout=300,
            verify=False,
        )
        
        print(f"✅ Connected to PeerDB")
        
        # Test 1: Check current database
        current_db = client.command("SELECT currentDatabase()")
        print(f"📂 Current database: {current_db}")
        
        # Test 2: List all databases
        print(f"\n📂 Available databases:")
        try:
            databases = client.query("SHOW DATABASES")
            for db in databases.result_rows:
                print(f"   - {db[0]}")
        except Exception as e:
            print(f"   ❌ Error listing databases: {e}")
        
        # Test 3: List tables in current database
        print(f"\n📋 Tables in current database:")
        try:
            tables = client.query("SHOW TABLES")
            for table in tables.result_rows:
                print(f"   - {table[0]}")
        except Exception as e:
            print(f"   ❌ Error listing tables: {e}")
        
        # Test 4: Try to access industry_index_logins in different ways
        table_variations = [
            "industry_index_logins",
            "default.industry_index_logins", 
            "peerdb.industry_index_logins"
        ]
        
        for table_name in table_variations:
            print(f"\n🔍 Testing table: {table_name}")
            
            # Test DESCRIBE
            try:
                schema = client.query(f"DESCRIBE TABLE {table_name}")
                print(f"   ✅ DESCRIBE successful - {len(schema.result_rows)} columns")
                for row in schema.result_rows[:3]:  # Show first 3 columns
                    print(f"      {row[0]}: {row[1]}")
                if len(schema.result_rows) > 3:
                    print(f"      ... and {len(schema.result_rows) - 3} more columns")
            except Exception as e:
                print(f"   ❌ DESCRIBE failed: {e}")
            
            # Test COUNT
            try:
                count = client.query(f"SELECT COUNT(*) FROM {table_name}")
                record_count = count.result_rows[0][0]
                print(f"   ✅ COUNT successful: {record_count:,} records")
            except Exception as e:
                print(f"   ❌ COUNT failed: {e}")
            
            # Test SELECT with LIMIT
            try:
                sample = client.query(f"SELECT * FROM {table_name} LIMIT 1")
                print(f"   ✅ SELECT successful: {len(sample.result_rows)} rows returned")
                if sample.result_rows:
                    print(f"   📄 Sample data available")
            except Exception as e:
                print(f"   ❌ SELECT failed: {e}")
        
        # Test 5: Check user privileges
        print(f"\n🔐 Checking user privileges:")
        try:
            privileges = client.query("SHOW GRANTS")
            print(f"   ✅ Grants query successful:")
            for grant in privileges.result_rows:
                print(f"      {grant[0]}")
        except Exception as e:
            print(f"   ❌ SHOW GRANTS failed: {e}")
        
        # Test 6: Try switching to default database
        print(f"\n🔄 Testing database switch:")
        try:
            client.command("USE default")
            current_db = client.command("SELECT currentDatabase()")
            print(f"   ✅ Switched to database: {current_db}")
            
            # Try listing tables in default
            tables = client.query("SHOW TABLES")
            print(f"   📋 Tables in default database:")
            for table in tables.result_rows:
                print(f"      - {table[0]}")
                
        except Exception as e:
            print(f"   ❌ Database switch failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Industry Index Logins Access Test")
    print("=" * 50)
    
    success = test_industry_index_access()
    
    if success:
        print(f"\n✅ Access test completed!")
    else:
        print(f"\n❌ Access test failed!")
