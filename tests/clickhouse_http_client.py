#!/usr/bin/env python3
"""
Alternative ClickHouse client using direct HTTP requests
Bypasses SSL issues in clickhouse-connect library
"""

import requests
import json
import pandas as pd
from urllib3.exceptions import InsecureRequestWarning
import urllib3

# Disable SSL warnings for this workaround
urllib3.disable_warnings(InsecureRequestWarning)

class ClickHouseHTTPClient:
    """Simple ClickHouse HTTP client that bypasses SSL issues"""
    
    def __init__(self, host, port=9440, username=None, password=None, database=None, secure=True, verify_ssl=False):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.secure = secure
        self.verify_ssl = verify_ssl
        
        # Build base URL
        protocol = "https" if secure else "http"
        self.base_url = f"{protocol}://{host}:{port}"
        
        # Setup session
        self.session = requests.Session()
        if username and password:
            self.session.auth = (username, password)
        
        # SSL verification
        self.session.verify = verify_ssl
        
        print(f"ClickHouse HTTP Client initialized:")
        print(f"  URL: {self.base_url}")
        print(f"  Database: {database}")
        print(f"  SSL Verify: {verify_ssl}")
    
    def execute_query(self, query, format="JSONEachRow"):
        """Execute a query and return results"""
        try:
            params = {}
            if self.database:
                params['database'] = self.database
            if format:
                params['default_format'] = format
            
            # Add query
            params['query'] = query
            
            print(f"Executing query: {query[:100]}...")
            
            response = self.session.post(
                self.base_url,
                params=params,
                timeout=30
            )
            
            response.raise_for_status()
            
            print(f"✓ Query executed successfully (Status: {response.status_code})")
            
            if format == "JSONEachRow":
                # Parse JSON lines
                lines = response.text.strip().split('\n')
                if lines and lines[0]:
                    data = [json.loads(line) for line in lines if line.strip()]
                    return pd.DataFrame(data) if data else pd.DataFrame()
                else:
                    return pd.DataFrame()
            else:
                return response.text
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Query failed: {e}")
            raise
    
    def test_connection(self):
        """Test the connection"""
        try:
            result = self.execute_query("SELECT 1 as test", format="JSONEachRow")
            print("✓ Connection test successful!")
            return result
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            raise
    
    def show_databases(self):
        """Show available databases"""
        return self.execute_query("SHOW DATABASES", format="JSONEachRow")
    
    def show_tables(self):
        """Show tables in current database"""
        return self.execute_query("SHOW TABLES", format="JSONEachRow")
    
    def get_version(self):
        """Get ClickHouse version"""
        return self.execute_query("SELECT version() as version", format="JSONEachRow")

def test_http_client():
    """Test the HTTP client"""
    print("="*60)
    print("ClickHouse HTTP Client Test")
    print("="*60)
    
    try:
        # Create client
        client = ClickHouseHTTPClient(
            host="pgy8egpix3.us-east-1.aws.clickhouse.cloud",
            port=9440,
            username="gabriellapuz",
            password="PTN.776)RR3s",
            database="peerdb",
            secure=True,
            verify_ssl=False  # Disable SSL verification to bypass Windows SSL issues
        )
        
        # Test connection
        print("\n1. Testing connection...")
        test_result = client.test_connection()
        print(f"Test result: {test_result}")
        
        # Get version
        print("\n2. Getting ClickHouse version...")
        version = client.get_version()
        print(f"Version: {version}")
        
        # Show databases
        print("\n3. Showing databases...")
        databases = client.show_databases()
        print(f"Databases: {databases}")
        
        # Show tables
        print("\n4. Showing tables...")
        tables = client.show_tables()
        print(f"Tables: {tables}")
        
        print("\n" + "="*60)
        print("✅ HTTP CLIENT SUCCESS!")
        print("You can use this client as an alternative to clickhouse-connect")
        print("="*60)
        
        return client
        
    except Exception as e:
        print(f"\n❌ HTTP client failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_notebook_example():
    """Create example code for notebook"""
    example_code = '''
# Alternative ClickHouse connection for Windows SSL issues
from clickhouse_http_client import ClickHouseHTTPClient

# Create client
client = ClickHouseHTTPClient(
    host="pgy8egpix3.us-east-1.aws.clickhouse.cloud",
    port=9440,
    username="gabriellapuz",
    password="PTN.776)RR3s",
    database="peerdb",
    secure=True,
    verify_ssl=False  # Bypass SSL verification
)

# Test connection
result = client.test_connection()
print(result)

# Execute custom queries
df = client.execute_query("SELECT * FROM your_table LIMIT 10")
print(df)
'''
    
    print("\n" + "="*60)
    print("NOTEBOOK EXAMPLE CODE:")
    print("="*60)
    print(example_code)

if __name__ == "__main__":
    client = test_http_client()
    if client:
        create_notebook_example()
    else:
        print("HTTP client test failed. Please check your connection settings.")
