#!/usr/bin/env python3
"""
Advanced ClickHouse connection test with multiple approaches
Specifically designed to handle Windows SSL issues
"""

import sys
import traceback
import ssl
import certifi
import urllib3
import os

import clickhouse_connect
from clickhouse_connect import get_client

def test_approach_1_default():
    """Test 1: Default connection"""
    print("\n" + "="*50)
    print("TEST 1: Default Connection")
    print("="*50)
    
    try:
        client = get_client(
            host="pgy8egpix3.us-east-1.aws.clickhouse.cloud",
            port=9440,
            username="gabriellapuz",
            password="PTN.776)RR3s",
            database="peerdb",
            secure=True
        )
        result = client.command('SELECT 1')
        print("✓ SUCCESS: Default connection works!")
        return client
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        return None

def test_approach_2_no_ssl_verify():
    """Test 2: Disable SSL verification"""
    print("\n" + "="*50)
    print("TEST 2: Disable SSL Verification")
    print("="*50)
    
    try:
        # Disable SSL warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        client = get_client(
            host="pgy8egpix3.us-east-1.aws.clickhouse.cloud",
            port=9440,
            username="gabriellapuz",
            password="PTN.776)RR3s",
            database="peerdb",
            secure=True,
            verify=False  # Disable SSL verification
        )
        result = client.command('SELECT 1')
        print("✓ SUCCESS: Connection with disabled SSL verification works!")
        return client
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        return None

def test_approach_3_custom_ca():
    """Test 3: Use custom CA bundle"""
    print("\n" + "="*50)
    print("TEST 3: Custom CA Bundle")
    print("="*50)
    
    try:
        ca_bundle = certifi.where()
        print(f"Using CA bundle: {ca_bundle}")
        
        client = get_client(
            host="pgy8egpix3.us-east-1.aws.clickhouse.cloud",
            port=9440,
            username="gabriellapuz",
            password="PTN.776)RR3s",
            database="peerdb",
            secure=True,
            ca_cert=ca_bundle
        )
        result = client.command('SELECT 1')
        print("✓ SUCCESS: Connection with custom CA bundle works!")
        return client
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        return None

def test_approach_4_http_only():
    """Test 4: HTTP only (no SSL)"""
    print("\n" + "="*50)
    print("TEST 4: HTTP Only (No SSL)")
    print("="*50)
    
    try:
        client = get_client(
            host="pgy8egpix3.us-east-1.aws.clickhouse.cloud",
            port=8123,  # HTTP port
            username="gabriellapuz",
            password="PTN.776)RR3s",
            database="peerdb",
            secure=False  # No SSL
        )
        result = client.command('SELECT 1')
        print("✓ SUCCESS: HTTP connection works!")
        return client
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        return None

def test_approach_5_environment_ssl():
    """Test 5: Set SSL environment variables"""
    print("\n" + "="*50)
    print("TEST 5: Environment SSL Settings")
    print("="*50)
    
    try:
        # Set SSL environment variables
        os.environ['SSL_CERT_FILE'] = certifi.where()
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
        
        client = get_client(
            host="pgy8egpix3.us-east-1.aws.clickhouse.cloud",
            port=9440,
            username="gabriellapuz",
            password="PTN.776)RR3s",
            database="peerdb",
            secure=True
        )
        result = client.command('SELECT 1')
        print("✓ SUCCESS: Connection with environment SSL settings works!")
        return client
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)}")
        return None

def main():
    """Run all connection tests"""
    print("ClickHouse Connection Test Suite")
    print("Designed to handle Windows SSL issues")
    print("="*60)
    
    print(f"Python version: {sys.version}")
    print(f"clickhouse-connect version: {clickhouse_connect.__version__ if hasattr(clickhouse_connect, '__version__') else 'unknown'}")
    print(f"SSL version: {ssl.OPENSSL_VERSION}")
    print(f"CA bundle location: {certifi.where()}")
    
    # Test all approaches
    approaches = [
        test_approach_1_default,
        test_approach_2_no_ssl_verify,
        test_approach_3_custom_ca,
        test_approach_4_http_only,
        test_approach_5_environment_ssl
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
        print("\n" + "="*60)
        print("✓ CONNECTION SUCCESSFUL!")
        print("You can use this approach in your notebook.")
        print("="*60)
        return True
    else:
        print("\n" + "="*60)
        print("❌ ALL TESTS FAILED")
        print("Please check:")
        print("1. ClickHouse Cloud instance is running")
        print("2. Credentials are correct")
        print("3. IP is whitelisted")
        print("4. Network connectivity")
        print("="*60)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
