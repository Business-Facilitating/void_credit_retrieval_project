#!/usr/bin/env python3
"""
PeerDB Industry Index Logins Data Pipeline
==========================================

DLT pipeline to extract data from PeerDB database, specifically the industry_index_logins table.

This pipeline:
1. Connects to PeerDB (ClickHouse) database
2. Extracts data from peerdb.industry_index_logins table
3. Exports to DuckDB and CSV formats
4. Supports incremental loading and batch processing

Usage:
    poetry run python src/src/peerdb_pipeline.py

Configuration:
    Set in .env file:
    - CLICKHOUSE_HOST: PeerDB ClickHouse host
    - CLICKHOUSE_PORT: PeerDB ClickHouse port (default: 8443)
    - CLICKHOUSE_USERNAME: PeerDB username
    - CLICKHOUSE_PASSWORD: PeerDB password
    - CLICKHOUSE_DATABASE: Database name (should be 'peerdb')
    - CLICKHOUSE_SECURE: Use SSL (default: true)

Output:
    - DuckDB: peerdb_industry_index_logins.duckdb
    - CSV: data/output/peerdb_industry_index_logins_YYYYMMDD_HHMMSS.csv

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import logging
import os
from datetime import datetime, timedelta
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
                print(
                    f"✅ Connected to PeerDB: {self.host}:{self.port}/{self.database}"
                )
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


def create_peerdb_table_resource(peerdb_conn, table_name, resource_name=None):
    """Create a DLT resource for any PeerDB table"""

    if resource_name is None:
        resource_name = table_name.replace("_", "_")  # Clean up name for DLT

    @dlt.resource(
        name=resource_name,
        write_disposition=os.getenv("DLT_WRITE_DISPOSITION", "replace"),
        primary_key=None,  # Will be determined dynamically
    )
    def peerdb_table_resource():
        """Extract data from PeerDB industry_index_logins table"""

        if not peerdb_conn.connected:
            print("❌ PeerDB connection not available")
            return

        try:
            # Get table schema first
            schema_query = f"DESCRIBE TABLE {table_name}"
            schema_result = peerdb_conn.query(schema_query)

            if schema_result:
                print(f"📋 Table schema for {table_name}:")
                for row in schema_result.result_rows:
                    print(f"   {row[0]}: {row[1]}")

            # Get total count
            count_query = f"SELECT COUNT(*) FROM {table_name}"
            count_result = peerdb_conn.query(count_query)
            total_count = count_result.result_rows[0][0] if count_result else 0

            print(f"📊 Total records in {table_name}: {total_count:,}")

            if total_count == 0:
                print("ℹ️ No data found in table")
                return

            # Configure batch processing
            batch_size = int(os.getenv("DLT_CLICKHOUSE_BATCH_SIZE", "50000"))
            total_batches = (total_count + batch_size - 1) // batch_size

            print(
                f"🔄 Processing {total_batches} batches of {batch_size:,} records each"
            )

            # Extract data in batches
            for batch_num in range(total_batches):
                offset = batch_num * batch_size

                # Query with LIMIT and OFFSET for pagination
                data_query = f"""
                SELECT * FROM {table_name}
                ORDER BY primary_key_for_updating  -- Using the actual primary key column
                LIMIT {batch_size} OFFSET {offset}
                """

                print(
                    f"📥 Extracting batch {batch_num + 1}/{total_batches} (offset: {offset:,})"
                )

                result = peerdb_conn.query(data_query)

                if result and result.result_rows:
                    # Convert to list of dictionaries
                    # Get column names from the result metadata
                    columns = result.column_names
                    batch_data = []

                    for row in result.result_rows:
                        record = dict(zip(columns, row))
                        batch_data.append(record)

                    print(
                        f"✅ Batch {batch_num + 1}: {len(batch_data):,} records extracted"
                    )

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


def peerdb_industry_index_source():
    """
    DLT source that extracts data FROM PeerDB industry_index_logins table

    Note: Using direct connection credentials like dlt_pipeline_examples.py
    """

    # Target table name (using the view in peerdb schema)
    table_name = "industry_index_logins"

    # Create connection with direct credentials (same as dlt_pipeline_examples.py)
    peerdb_conn = PeerDBConnection(
        host="pgy8egpix3.us-east-1.aws.clickhouse.cloud",
        port=8443,
        username="gabriellapuz",
        password="PTN.776)RR3s",
        database="peerdb",
        secure=True,
    )

    # Test connection
    if not peerdb_conn.connect():
        print("❌ Failed to connect to PeerDB")
        return None

    print(f"🎯 Target table: {table_name}")

    # Create and return the resource
    return create_peerdb_table_resource(
        peerdb_conn, table_name, "industry_index_logins"
    )


@dlt.source
def peerdb_source():
    """DLT source wrapper for PeerDB industry index logins extraction"""
    return peerdb_industry_index_source()


def run_peerdb_extraction(destination="duckdb", pipeline_name_suffix=""):
    """
    Run the main pipeline that extracts industry index logins data from PeerDB to DuckDB

    Args:
        destination: Destination for the extracted data (default: "duckdb")
        pipeline_name_suffix: Optional suffix for pipeline name to avoid conflicts

    Returns:
        dlt.Pipeline: The completed pipeline object
    """
    print("🚀 PeerDB Industry Index Logins Data Extraction Pipeline")
    print("=" * 60)

    # Create pipeline with optional suffix to avoid file locks
    pipeline_name = "peerdb_industry_index_logins" + pipeline_name_suffix
    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=destination,
        dataset_name="peerdb_data",
    )

    # Run extraction
    print(f"📥 Extracting data from PeerDB...")
    print(f"🎯 Target table: industry_index_logins")
    print(f"📍 Destination: {destination}")

    try:
        # Create and run the PeerDB source
        source = peerdb_source()
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


def export_to_csv(pipeline):
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
        query = "SELECT * FROM peerdb_data.industry_index_logins"
        result = conn.execute(query).fetchdf()

        if result.empty:
            print("ℹ️ No data found to export")
            conn.close()
            return

        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"peerdb_industry_index_logins_{timestamp}.csv"
        csv_path = os.path.join(output_dir, csv_filename)

        # Export to CSV
        result.to_csv(csv_path, index=False)

        print(f"📄 CSV exported: {csv_path}")
        print(f"📊 Records exported: {len(result):,}")
        print(f"📋 Columns: {len(result.columns)}")

        # Show column names
        print(f"📝 Column names: {list(result.columns)}")

        conn.close()

    except Exception as e:
        print(f"❌ Failed to export CSV: {e}")


if __name__ == "__main__":
    print("🚀 PeerDB Industry Index Logins Pipeline")
    print("=" * 50)

    # Run the extraction pipeline
    print("\n1. Running PeerDB extraction...")
    pipeline = run_peerdb_extraction()

    if pipeline:
        print("\n2. Exporting to CSV...")
        export_to_csv(pipeline)

    print("\n✅ Pipeline execution completed!")
