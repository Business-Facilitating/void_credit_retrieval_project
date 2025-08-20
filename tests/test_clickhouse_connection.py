#!/usr/bin/env python3
"""
Test script for ClickHouse connection
Run this to debug connection issues outside of Jupyter notebook
"""

import ssl
import sys
import traceback

import certifi
import clickhouse_connect
import urllib3
from clickhouse_connect import get_client


def test_clickhouse_connection():
    """Test ClickHouse connection with detailed error reporting"""

    print("=" * 60)
    print("ClickHouse Connection Test")
    print("=" * 60)

    # Connection parameters
    connection_params = {
        "host": "pgy8egpix3.us-east-1.aws.clickhouse.cloud",
        "port": 9440,
        "username": "gabriellapuz",
        "password": "PTN.776)RR3s",
        "database": "peerdb",
        "secure": True,
        "verify": False,  # Disable SSL verification (for Windows SSL issues)
        "connect_timeout": 30,
        "send_receive_timeout": 30,
    }

    print(f"Connection parameters:")
    for key, value in connection_params.items():
        if key == "password":
            print(f"  {key}: {'*' * len(str(value))}")
        else:
            print(f"  {key}: {value}")
    print()

    try:
        print("Attempting to connect...")
        client = get_client(**connection_params)
        print("✓ Client created successfully")

        print("Testing connection with simple query...")
        result = client.command("SELECT 1 as test")
        print(f"✓ Connection test successful! Result: {result}")

        print("Testing database access...")
        result = client.command("SELECT version()")
        print(f"✓ ClickHouse version: {result}")

        print("Testing database list...")
        result = client.command("SHOW DATABASES")
        print(f"✓ Available databases: {result}")

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - Connection is working!")
        print("=" * 60)

        return client

    except Exception as e:
        print(f"\n❌ Connection failed!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()

        print("\n" + "=" * 60)
        print("TROUBLESHOOTING SUGGESTIONS:")
        print("=" * 60)
        print("1. Check if your password is correct (no extra spaces)")
        print("2. Verify your username and host are correct")
        print("3. Ensure your ClickHouse Cloud instance is running")
        print("4. Check if your IP is whitelisted in ClickHouse Cloud")
        print("5. Verify network connectivity (firewall, VPN, etc.)")
        print("6. Try connecting from ClickHouse Cloud console first")
        print("=" * 60)

        return None


if __name__ == "__main__":
    client = test_clickhouse_connection()
    if client:
        print("\nYou can now use this connection in your notebook!")
    else:
        print("\nPlease fix the connection issues before proceeding.")
        sys.exit(1)
        print("\nPlease fix the connection issues before proceeding.")
        sys.exit(1)
