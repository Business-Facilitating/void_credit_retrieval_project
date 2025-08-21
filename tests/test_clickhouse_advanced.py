#!/usr/bin/env python3
"""
Advanced ClickHouse connection test with multiple approaches
Specifically designed to handle Windows SSL issues
"""

import os
import ssl
import sys
import traceback

import certifi
import clickhouse_connect
import urllib3
from clickhouse_connect import get_client


def test_approach_1_default():
    """Test 1: Default connection"""
    from dotenv import load_dotenv

    load_dotenv()

    print("\n" + "=" * 50)
    print("TEST 1: Default Connection")
    print("=" * 50)

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
        print(
            "💡 Please check your .env file and ensure all ClickHouse credentials are set."
        )
        return None

    try:
        client = get_client(
            host=os.getenv("CLICKHOUSE_HOST"),
            port=int(os.getenv("CLICKHOUSE_PORT", "9440")),
            username=os.getenv("CLICKHOUSE_USERNAME"),
            password=os.getenv("CLICKHOUSE_PASSWORD"),
            database=os.getenv("CLICKHOUSE_DATABASE"),
            secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true",
        )
        result = client.command("SELECT 1")
        print("✓ SUCCESS: Default connection works!")
        return client
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        return None


def test_approach_2_no_ssl_verify():
    """Test 2: Disable SSL verification"""
    from dotenv import load_dotenv

    load_dotenv()

    print("\n" + "=" * 50)
    print("TEST 2: Disable SSL Verification")
    print("=" * 50)

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
        return None

    try:
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        client = get_client(
            host=os.getenv("CLICKHOUSE_HOST"),
            port=int(os.getenv("CLICKHOUSE_PORT", "9440")),
            username=os.getenv("CLICKHOUSE_USERNAME"),
            password=os.getenv("CLICKHOUSE_PASSWORD"),
            database=os.getenv("CLICKHOUSE_DATABASE"),
            secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true",
            verify=False,  # Disable SSL verification
        )
        result = client.command("SELECT 1")
        print("✓ SUCCESS: Connection with disabled SSL verification works!")
        return client
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        return None


def test_approach_3_custom_ca():
    """Test 3: Use custom CA bundle"""
    print("\n" + "=" * 50)
    print("TEST 3: Custom CA Bundle")
    print("=" * 50)

    try:
        ca_bundle = certifi.where()
        print(f"Using CA bundle: {ca_bundle}")

        client = get_client(
            host=os.getenv("CLICKHOUSE_HOST"),
            port=int(os.getenv("CLICKHOUSE_PORT", "9440")),
            username=os.getenv("CLICKHOUSE_USERNAME"),
            password=os.getenv("CLICKHOUSE_PASSWORD"),
            database=os.getenv("CLICKHOUSE_DATABASE"),
            secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true",
            ca_cert=ca_bundle,
        )
        result = client.command("SELECT 1")
        print("✓ SUCCESS: Connection with custom CA bundle works!")
        return client
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        return None


def test_approach_4_http_only():
    """Test 4: HTTP only (no SSL)"""
    print("\n" + "=" * 50)
    print("TEST 4: HTTP Only (No SSL)")
    print("=" * 50)

    try:
        client = get_client(
            host=os.getenv("CLICKHOUSE_HOST"),
            port=8123,  # HTTP port
            username=os.getenv("CLICKHOUSE_USERNAME"),
            password=os.getenv("CLICKHOUSE_PASSWORD"),
            database=os.getenv("CLICKHOUSE_DATABASE"),
            secure=False,  # No SSL
        )
        result = client.command("SELECT 1")
        print("✓ SUCCESS: HTTP connection works!")
        return client
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        return None


def test_approach_5_environment_ssl():
    """Test 5: Set SSL environment variables"""
    print("\n" + "=" * 50)
    print("TEST 5: Environment SSL Settings")
    print("=" * 50)

    try:
        # Set SSL environment variables
        os.environ["SSL_CERT_FILE"] = certifi.where()
        os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

        client = get_client(
            host=os.getenv("CLICKHOUSE_HOST"),
            port=int(os.getenv("CLICKHOUSE_PORT", "9440")),
            username=os.getenv("CLICKHOUSE_USERNAME"),
            password=os.getenv("CLICKHOUSE_PASSWORD"),
            database=os.getenv("CLICKHOUSE_DATABASE"),
            secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true",
        )
        result = client.command("SELECT 1")
        print("✓ SUCCESS: Connection with environment SSL settings works!")
        return client
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        return None


def main():
    """Run all connection tests"""
    print("ClickHouse Connection Test Suite")
    print("Designed to handle Windows SSL issues")
    print("=" * 60)

    print(f"Python version: {sys.version}")
    print(
        f"clickhouse-connect version: {clickhouse_connect.__version__ if hasattr(clickhouse_connect, '__version__') else 'unknown'}"
    )
    print(f"SSL version: {ssl.OPENSSL_VERSION}")
    print(f"CA bundle location: {certifi.where()}")

    # Test all approaches
    approaches = [
        test_approach_1_default,
        test_approach_2_no_ssl_verify,
        test_approach_3_custom_ca,
        test_approach_4_http_only,
        test_approach_5_environment_ssl,
    ]

    successful_client = None

    for i, test_func in enumerate(approaches, 1):
        try:
            client = test_func()
            if client:
                successful_client = client
                print(f"\n🎉 SOLUTION FOUND: Approach {i} works!")
                break
        except Exception as e:
            print(f"Test {i} crashed: {e}")
            continue

    if successful_client:
        print("\n" + "=" * 60)
        print("✓ CONNECTION SUCCESSFUL!")
        print("You can use this approach in your notebook.")
        print("=" * 60)
        return True
    else:
        print("\n" + "=" * 60)
        print("❌ ALL TESTS FAILED")
        print("Please check:")
        print("1. ClickHouse Cloud instance is running")
        print("2. Credentials are correct")
        print("3. IP is whitelisted")
        print("4. Network connectivity")
        print("=" * 60)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
    sys.exit(0 if success else 1)
    sys.exit(0 if success else 1)
