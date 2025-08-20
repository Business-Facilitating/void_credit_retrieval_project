#!/usr/bin/env python3
"""
Test different SSL/TLS versions and configurations for ClickHouse
"""

import sys
import ssl
import urllib3
import requests
import socket
from urllib3.util.ssl_ import create_urllib3_context

import clickhouse_connect
from clickhouse_connect import get_client

def test_basic_connectivity():
    """Test basic network connectivity to the host"""
    print("\n" + "="*50)
    print("CONNECTIVITY TEST")
    print("="*50)
    
    host = "pgy8egpix3.us-east-1.aws.clickhouse.cloud"
    port = 9440
    
    try:
        # Test DNS resolution
        ip = socket.gethostbyname(host)
        print(f"✓ DNS resolution: {host} -> {ip}")
        
        # Test TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✓ TCP connection to {host}:{port} successful")
            return True
        else:
            print(f"❌ TCP connection failed with error code: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Connectivity test failed: {e}")
        return False

def test_ssl_handshake():
    """Test SSL handshake manually"""
    print("\n" + "="*50)
    print("SSL HANDSHAKE TEST")
    print("="*50)
    
    host = "pgy8egpix3.us-east-1.aws.clickhouse.cloud"
    port = 9440
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        
        # Test SSL connection
        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                print(f"✓ SSL handshake successful")
                print(f"  SSL version: {ssock.version()}")
                print(f"  Cipher: {ssock.cipher()}")
                return True
                
    except Exception as e:
        print(f"❌ SSL handshake failed: {e}")
        return False

def test_requests_library():
    """Test using requests library directly"""
    print("\n" + "="*50)
    print("REQUESTS LIBRARY TEST")
    print("="*50)
    
    url = "https://pgy8egpix3.us-east-1.aws.clickhouse.cloud:9440/"
    
    try:
        # Test with requests
        response = requests.get(
            url,
            auth=("gabriellapuz", "PTN.776)RR3s"),
            timeout=30,
            verify=True
        )
        print(f"✓ Requests library connection successful")
        print(f"  Status code: {response.status_code}")
        print(f"  Response headers: {dict(response.headers)}")
        return True
        
    except Exception as e:
        print(f"❌ Requests library failed: {e}")
        
        # Try without SSL verification
        try:
            response = requests.get(
                url,
                auth=("gabriellapuz", "PTN.776)RR3s"),
                timeout=30,
                verify=False
            )
            print(f"✓ Requests library (no SSL verify) successful")
            print(f"  Status code: {response.status_code}")
            return True
        except Exception as e2:
            print(f"❌ Requests library (no SSL verify) also failed: {e2}")
            return False

def test_clickhouse_with_custom_ssl():
    """Test ClickHouse with custom SSL settings"""
    print("\n" + "="*50)
    print("CLICKHOUSE CUSTOM SSL TEST")
    print("="*50)
    
    try:
        # Create custom SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Try to pass custom SSL context (if supported)
        client = get_client(
            host="pgy8egpix3.us-east-1.aws.clickhouse.cloud",
            port=9440,
            username="gabriellapuz",
            password="PTN.776)RR3s",
            database="peerdb",
            secure=True,
            verify=False,
            connect_timeout=60,
            send_receive_timeout=60
        )
        
        result = client.command('SELECT 1')
        print("✓ ClickHouse with custom SSL successful!")
        return client
        
    except Exception as e:
        print(f"❌ ClickHouse custom SSL failed: {e}")
        return None

def check_ip_whitelist():
    """Check current public IP"""
    print("\n" + "="*50)
    print("IP WHITELIST CHECK")
    print("="*50)
    
    try:
        # Get public IP
        response = requests.get('https://httpbin.org/ip', timeout=10)
        ip_info = response.json()
        public_ip = ip_info['origin']
        print(f"Your public IP: {public_ip}")
        print("Make sure this IP is whitelisted in ClickHouse Cloud!")
        
        # Also try ipify as backup
        try:
            response2 = requests.get('https://api.ipify.org', timeout=10)
            backup_ip = response2.text.strip()
            print(f"Backup IP check: {backup_ip}")
        except:
            pass
            
        return public_ip
        
    except Exception as e:
        print(f"❌ Could not determine public IP: {e}")
        return None

def main():
    """Run all diagnostic tests"""
    print("ClickHouse Connection Diagnostics")
    print("="*60)
    
    # Run diagnostic tests
    tests = [
        ("Basic Connectivity", test_basic_connectivity),
        ("SSL Handshake", test_ssl_handshake),
        ("Requests Library", test_requests_library),
        ("IP Whitelist Check", check_ip_whitelist),
        ("ClickHouse Custom SSL", test_clickhouse_with_custom_ssl)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    # Recommendations
    print("\n" + "="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    
    if not results.get("Basic Connectivity"):
        print("1. Check your internet connection")
        print("2. Check if you're behind a corporate firewall")
        print("3. Try using a VPN or different network")
    
    if not results.get("SSL Handshake"):
        print("1. Your system may have SSL/TLS configuration issues")
        print("2. Try updating your Python SSL certificates")
        print("3. Check Windows certificate store")
    
    if not results.get("IP Whitelist Check"):
        print("1. Could not determine your IP - check manually")
        print("2. Ensure your IP is whitelisted in ClickHouse Cloud")
    
    if results.get("Requests Library") and not results.get("ClickHouse Custom SSL"):
        print("1. The issue is specific to clickhouse-connect library")
        print("2. Try using a different version of clickhouse-connect")
        print("3. Consider using HTTP interface directly")

if __name__ == "__main__":
    main()
