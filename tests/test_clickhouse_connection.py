#!/usr/bin/env python3
"""
Simple ClickHouse Connection Test
"""

import os
import ssl

import certifi
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import clickhouse_connect

    print("✅ clickhouse_connect library available")
except ImportError:
    print("❌ clickhouse_connect library not available")
    exit(1)


# Test basic HTTPS connectivity first
def test_https_connectivity():
    print("\n🌐 Testing basic HTTPS connectivity...")
    host = os.getenv("CLICKHOUSE_HOST")
    port = int(os.getenv("CLICKHOUSE_PORT", "8443"))

    try:
        url = f"https://{host}:{port}/"
        response = requests.get(url, timeout=10, verify=False)
        print(f"✅ HTTPS connection successful (status: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ HTTPS connection failed: {e}")
        return False


# Get connection parameters from environment
host = os.getenv("CLICKHOUSE_HOST")
port = int(os.getenv("CLICKHOUSE_PORT", "8443"))
username = os.getenv("CLICKHOUSE_USERNAME")
password = os.getenv("CLICKHOUSE_PASSWORD")
database = os.getenv("CLICKHOUSE_DATABASE")
secure = os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true"

print(f"🔗 Attempting to connect to ClickHouse:")
print(f"   Host: {host}")
print(f"   Port: {port}")
print(f"   Username: {username}")
print(f"   Database: {database}")
print(f"   Secure: {secure}")

# Test basic connectivity first
test_https_connectivity()

# Try different connection configurations
connection_configs = [
    {
        "name": "Standard SSL connection",
        "params": {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "database": database,
            "secure": secure,
        },
    },
    {
        "name": "SSL with extended timeouts",
        "params": {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "database": database,
            "secure": secure,
            "connect_timeout": 60,
            "send_receive_timeout": 300,
        },
    },
    {
        "name": "SSL with verification disabled",
        "params": {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "database": database,
            "secure": secure,
            "verify": False,
            "connect_timeout": 60,
            "send_receive_timeout": 300,
        },
    },
    {
        "name": "HTTP interface",
        "params": {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "database": database,
            "secure": secure,
            "interface": "http",
            "verify": False,
        },
    },
    {
        "name": "HTTPS with custom CA bundle",
        "params": {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "database": database,
            "secure": secure,
            "ca_certs": "system",
            "verify": True,
        },
    },
    {
        "name": "SSL with certifi CA bundle",
        "params": {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "database": database,
            "secure": secure,
            "verify": certifi.where(),
            "connect_timeout": 60,
        },
    },
    {
        "name": "SSL context with system certs",
        "params": {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "database": database,
            "secure": secure,
            "verify": True,
            "connect_timeout": 60,
        },
    },
]

for config in connection_configs:
    print(f"\n🧪 Testing: {config['name']}")
    try:
        client = clickhouse_connect.get_client(**config["params"])
        result = client.command("SELECT 1")
        if result == 1:
            print(f"✅ Connection successful!")

            # Test a simple query
            try:
                tables = client.command("SHOW TABLES")
                print(f"📊 Available tables: {tables}")

                # Check if our target table exists
                target_table = "carrier_carrier_invoice_original_flat_ups"
                table_exists = client.command(f"EXISTS TABLE {target_table}")
                print(f"🎯 Target table '{target_table}' exists: {table_exists}")

                if table_exists:
                    # Get table info
                    count = client.command(f"SELECT COUNT(*) FROM {target_table}")
                    print(f"📈 Table row count: {count}")

                break

            except Exception as e:
                print(f"⚠️ Connection works but query failed: {e}")
                break
        else:
            print(f"❌ Connection test failed")

    except Exception as e:
        print(f"❌ Connection failed: {type(e).__name__}: {str(e)}")

print("\n🏁 Connection test completed")
print("\n🏁 Connection test completed")
