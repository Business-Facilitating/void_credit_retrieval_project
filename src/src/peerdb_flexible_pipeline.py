#!/usr/bin/env python3
"""
PeerDB Flexible Data Pipeline
=============================

DLT pipeline to extract data from any table in PeerDB database.

This pipeline:
1. Connects to PeerDB (ClickHouse) database
2. Extracts data from any specified table
3. Exports to DuckDB and CSV formats
4. Supports incremental loading and batch processing

Usage:
    # Extract from a specific table
    poetry run python src/src/peerdb_flexible_pipeline.py --table carrier_carrier_invoice_original_flat_ups
    
    # Extract with custom batch size
    poetry run python src/src/peerdb_flexible_pipeline.py --table carrier_carrier_invoice_original_flat_ups --batch-size 5000
    
    # Extract limited records for testing
    poetry run python src/src/peerdb_flexible_pipeline.py --table carrier_carrier_invoice_original_flat_ups --limit 1000

Configuration:
    Set in .env file:
    - CLICKHOUSE_HOST: PeerDB ClickHouse host
    - CLICKHOUSE_PORT: PeerDB ClickHouse port (default: 8443)
    - CLICKHOUSE_USERNAME: PeerDB username
    - CLICKHOUSE_PASSWORD: PeerDB password
    - CLICKHOUSE_DATABASE: Database name (should be 'peerdb')
    - CLICKHOUSE_SECURE: Use SSL (default: true)

Output:
    - DuckDB: peerdb_{table_name}.duckdb
    - CSV: data/output/peerdb_{table_name}_YYYYMMDD_HHMMSS.csv

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import argparse
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import dlt
from dotenv import load_dotenv

# ClickHouse imports with fallback handling
try:
    import clickhouse_connect
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False
    print("⚠️ clickhouse_connect not available")

# DuckDB imports with fallback handling
try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
    print("⚠️ duckdb not available")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure output directory exists
output_dir = os.getenv("OUTPUT_DIR", "data/output")
os.makedirs(output_dir, exist_ok=True)


class PeerDBConnection:
    """Manages PeerDB ClickHouse connections with error handling"""
    
    def __init__(self, host, port, username, password, database, secure=True):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.secure = secure
        self.client = None
        self.connected = False
        
    def connect(self):
        """Establish connection to PeerDB ClickHouse with error handling"""
        if not CLICKHOUSE_AVAILABLE:
            print("⚠️ ClickHouse library not available")
            return False

        try:
            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database,
                secure=self.secure,
                connect_timeout=60,
                send_receive_timeout=300,
                verify=False,  # Disable SSL verification for cloud connections
            )

            # Test connection
            result = self.client.command("SELECT 1")
            if result == 1:
                self.connected = True
                print(f"✅ Connected to PeerDB: {self.host}:{self.port}/{self.database}")
                return True
            else:
                print(f"❌ PeerDB connection test failed")
                return False

        except Exception as e:
            print(f"❌ Failed to connect to PeerDB: {e}")
            return False

    def query(self, sql, parameters=None):
        """Execute query with error handling"""
        if not self.connected:
            print("❌ Not connected to PeerDB")
            return None

        try:
            if parameters:
                return self.client.query(sql, parameters=parameters)
            else:
                return self.client.query(sql)
        except Exception as e:
            print(f"❌ Query failed: {e}")
            return None

    def close(self):
        """Close the connection"""
        if self.client:
            self.client.close()
            self.connected = False


def create_peerdb_table_resource(peerdb_conn, table_name, batch_size=10000, limit=None):
    """Create a DLT resource for any PeerDB table"""
    
    resource_name = table_name.replace("_", "_")  # Clean up name for DLT

    @dlt.resource(
        name=resource_name,
        write_disposition=os.getenv("DLT_WRITE_DISPOSITION", "replace"),
        primary_key=None,  # Will be determined dynamically
    )
    def peerdb_table_resource():
        """Extract data from any PeerDB table"""
        
        if not peerdb_conn.connected:
            print("❌ PeerDB connection not available")
            return

        try:
            # Get table schema first
            schema_query = f"DESCRIBE TABLE {table_name}"
            schema_result = peerdb_conn.query(schema_query)
            
            columns = []
            primary_key_candidates = []
            
            if schema_result:
                print(f"📋 Table schema for {table_name}:")
                for row in schema_result.result_rows:
                    column_name = row[0]
                    column_type = row[1]
                    columns.append(column_name)
                    print(f"   {column_name}: {column_type}")
                    
                    # Look for potential primary key columns
                    if any(pk_hint in column_name.lower() for pk_hint in ['id', 'key', 'number']):
                        primary_key_candidates.append(column_name)
            
            # Choose ordering column (prefer primary key candidates, fallback to first column)
            order_column = primary_key_candidates[0] if primary_key_candidates else columns[0] if columns else None
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            count_result = peerdb_conn.query(count_query)
            total_count = count_result.result_rows[0][0] if count_result else 0
            
            print(f"📊 Total records in {table_name}: {total_count:,}")
            print(f"🔑 Using '{order_column}' for ordering")
            
            if total_count == 0:
                print("ℹ️ No data found in table")
                return

            # Apply limit if specified
            records_to_extract = min(total_count, limit) if limit else total_count
            total_batches = (records_to_extract + batch_size - 1) // batch_size
            
            print(f"🎯 Extracting {records_to_extract:,} records")
            print(f"🔄 Processing {total_batches} batches of {batch_size:,} records each")

            # Extract data in batches
            for batch_num in range(total_batches):
                offset = batch_num * batch_size
                current_batch_size = min(batch_size, records_to_extract - offset)
                
                # Query with LIMIT and OFFSET for pagination
                if order_column:
                    data_query = f"""
                    SELECT * FROM {table_name}
                    ORDER BY {order_column}
                    LIMIT {current_batch_size} OFFSET {offset}
                    """
                else:
                    data_query = f"""
                    SELECT * FROM {table_name}
                    LIMIT {current_batch_size} OFFSET {offset}
                    """
                
                print(f"📥 Extracting batch {batch_num + 1}/{total_batches} (offset: {offset:,}, size: {current_batch_size:,})")
                
                result = peerdb_conn.query(data_query)
                
                if result and result.result_rows:
                    # Convert to list of dictionaries
                    batch_data = []
                    
                    for row in result.result_rows:
                        record = dict(zip(columns, row))
                        batch_data.append(record)
                    
                    print(f"✅ Batch {batch_num + 1}: {len(batch_data):,} records extracted")
                    
                    # Yield the batch data
                    yield batch_data
                else:
                    print(f"⚠️ Batch {batch_num + 1}: No data returned")

        except Exception as e:
            print(f"❌ Failed to extract from {table_name}: {e}")
            import traceback
            traceback.print_exc()
            raise

    return peerdb_table_resource


def peerdb_table_source(table_name, batch_size=10000, limit=None):
    """
    DLT source that extracts data FROM any PeerDB table
    
    Note: Using environment variables for secure credential management
    """
    
    # Create connection with environment variables
    peerdb_conn = PeerDBConnection(
        host=os.getenv("CLICKHOUSE_HOST"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
        username=os.getenv("CLICKHOUSE_USERNAME"),
        password=os.getenv("CLICKHOUSE_PASSWORD"),
        database=os.getenv("CLICKHOUSE_DATABASE", "peerdb"),
        secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true",
    )
    
    # Test connection
    if not peerdb_conn.connect():
        print("❌ Failed to connect to PeerDB")
        return None
    
    print(f"🎯 Target table: {table_name}")
    
    # Create and return the resource
    return create_peerdb_table_resource(peerdb_conn, table_name, batch_size, limit)


@dlt.source
def peerdb_source(table_name, batch_size=10000, limit=None):
    """DLT source wrapper for PeerDB table extraction"""
    return peerdb_table_source(table_name, batch_size, limit)


def run_peerdb_extraction(table_name, batch_size=10000, limit=None, destination="duckdb"):
    """
    Run the main pipeline that extracts data from any PeerDB table to DuckDB
    
    Args:
        table_name: Name of the table to extract
        batch_size: Number of records per batch
        limit: Maximum number of records to extract (None for all)
        destination: Destination for the extracted data (default: "duckdb")
    
    Returns:
        dlt.Pipeline: The completed pipeline object
    """
    print("🚀 PeerDB Flexible Data Extraction Pipeline")
    print("=" * 60)
    
    # Create pipeline with table-specific name
    pipeline_name = f"peerdb_{table_name}"
    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=destination,
        dataset_name="peerdb_data",
    )
    
    # Run extraction
    print(f"📥 Extracting data from PeerDB...")
    print(f"🎯 Target table: {table_name}")
    print(f"📍 Destination: {destination}")
    print(f"📦 Batch size: {batch_size:,}")
    if limit:
        print(f"🎯 Record limit: {limit:,}")
    
    try:
        # Create and run the PeerDB source
        source = peerdb_source(table_name, batch_size, limit)
        if source is None:
            print("❌ Failed to create PeerDB source")
            return None
            
        info = pipeline.run(source)
        
        print(f"\n✅ Extraction pipeline completed successfully!")
        print(f"📊 Load info: {info}")
        
        return pipeline
        
    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def export_to_csv(pipeline, table_name):
    """Export the extracted data to CSV format"""
    if not DUCKDB_AVAILABLE:
        print("⚠️ DuckDB not available - skipping CSV export")
        return
    
    try:
        # Connect to the DuckDB file created by the pipeline
        db_path = f"{pipeline.pipeline_name}.duckdb"
        
        if not os.path.exists(db_path):
            print(f"❌ DuckDB file not found: {db_path}")
            return
        
        conn = duckdb.connect(db_path)
        
        # Query all data
        resource_name = table_name.replace("_", "_")
        query = f"SELECT * FROM peerdb_data.{resource_name}"
        result = conn.execute(query).fetchdf()
        
        if result.empty:
            print("ℹ️ No data found to export")
            conn.close()
            return
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"peerdb_{table_name}_{timestamp}.csv"
        csv_path = os.path.join(output_dir, csv_filename)
        
        # Export to CSV
        result.to_csv(csv_path, index=False)
        
        print(f"📄 CSV exported: {csv_path}")
        print(f"📊 Records exported: {len(result):,}")
        print(f"📋 Columns: {len(result.columns)}")
        
        # Show first few column names
        column_preview = list(result.columns)[:10]
        if len(result.columns) > 10:
            column_preview.append(f"... and {len(result.columns) - 10} more")
        print(f"📝 Columns: {', '.join(column_preview)}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Failed to export CSV: {e}")


def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(description="Extract data from PeerDB tables")
    parser.add_argument("--table", required=True, help="Table name to extract")
    parser.add_argument("--batch-size", type=int, default=10000, help="Batch size for extraction")
    parser.add_argument("--limit", type=int, help="Maximum number of records to extract")
    parser.add_argument("--destination", default="duckdb", help="Destination for extracted data")
    
    args = parser.parse_args()
    
    print("🚀 PeerDB Flexible Pipeline")
    print("=" * 50)
    print(f"📋 Table: {args.table}")
    print(f"📦 Batch size: {args.batch_size:,}")
    if args.limit:
        print(f"🎯 Limit: {args.limit:,}")
    print(f"📍 Destination: {args.destination}")
    
    # Run the extraction pipeline
    print("\n1. Running PeerDB extraction...")
    pipeline = run_peerdb_extraction(args.table, args.batch_size, args.limit, args.destination)
    
    if pipeline:
        print("\n2. Exporting to CSV...")
        export_to_csv(pipeline, args.table)
    
    print("\n✅ Pipeline execution completed!")


if __name__ == "__main__":
    main()
