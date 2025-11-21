#!/usr/bin/env python3
"""
ClickHouse Biannual Data Extraction (H2 2025)
==============================================

This script extracts ONLY second half of 2025 data (July 1 - December 31, 2025)
from the carrier_carrier_invoice_original_flat_ups table from ClickHouse.
Used for data analysis and verification.

Output:
    - DuckDB: full_carrier_invoice_extraction.duckdb

Usage:
    poetry run python src/src/full_extract_clickhouse.py

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

import dlt

# ClickHouse imports with fallback handling
try:
    import clickhouse_connect

    CLICKHOUSE_AVAILABLE = True
except ImportError:
    CLICKHOUSE_AVAILABLE = False
    print("⚠️ clickhouse_connect not available")

# DuckDB imports for querying
try:
    import duckdb

    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
    print("⚠️ duckdb not available")


class ClickHouseConnection:
    """Manages ClickHouse connections for carrier invoice data extraction"""

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
        """Establish connection to ClickHouse with error handling"""
        if not CLICKHOUSE_AVAILABLE:
            print("⚠️ ClickHouse library not available")
            return False

        try:
            # Disable SSL warnings for ClickHouse Cloud connections
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database,
                secure=self.secure,
                connect_timeout=60,
                send_receive_timeout=300,
                verify=False,  # Disable SSL verification for Windows compatibility
            )

            # Test connection
            result = self.client.command("SELECT 1")
            if result == 1:
                self.connected = True
                print(
                    f"✅ Connected to ClickHouse: {self.host}:{self.port}/{self.database}"
                )
                return True
            else:
                print(f"❌ ClickHouse connection test failed")
                return False

        except Exception as e:
            print(f"❌ ClickHouse connection failed: {type(e).__name__}: {str(e)}")
            self.connected = False
            return False

    def execute_query(self, query, parameters=None):
        """Execute query with error handling"""
        if not self.connected:
            raise ConnectionError("Not connected to ClickHouse")

        try:
            if parameters:
                result = self.client.query(query, parameters=parameters)
            else:
                result = self.client.query(query)
            return result.result_rows
        except Exception as e:
            print(f"❌ Query execution failed: {e}")
            raise

    def get_table_schema(self, table_name):
        """Get table schema information"""
        if not self.connected:
            return []

        try:
            schema_query = f"""
            SELECT
                name,
                type,
                default_kind,
                default_expression
            FROM system.columns
            WHERE database = '{self.database}' AND table = '{table_name}'
            ORDER BY position
            """
            return self.execute_query(schema_query)
        except Exception as e:
            print(f"❌ Failed to get schema for table {table_name}: {e}")
            return []


def clickhouse_full_extraction_source():
    """
    DLT source that extracts ONLY H2 2025 data (July 1 - December 31, 2025)
    FROM ClickHouse carrier_carrier_invoice_original_flat_ups table
    Filters by transaction_date to only include second half of 2025
    """
    from dotenv import load_dotenv

    load_dotenv()

    # Target table name
    table_name = "carrier_carrier_invoice_original_flat_ups"

    # Create connection with environment variables
    ch_conn = ClickHouseConnection(
        host=os.getenv("CLICKHOUSE_HOST"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8443")),
        username=os.getenv("CLICKHOUSE_USERNAME"),
        password=os.getenv("CLICKHOUSE_PASSWORD"),
        database=os.getenv("CLICKHOUSE_DATABASE"),
        secure=os.getenv("CLICKHOUSE_SECURE", "true").lower() == "true",
    )

    # Validate required environment variables
    required_vars = [
        "CLICKHOUSE_HOST",
        "CLICKHOUSE_USERNAME",
        "CLICKHOUSE_PASSWORD",
        "CLICKHOUSE_DATABASE",
    ]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}. Please check your .env file."
        )

    connection_success = ch_conn.connect()

    if not connection_success:
        raise ConnectionError(
            "Failed to connect to ClickHouse. Please check your connection settings and SSL configuration."
        )

    print(f"🎯 Extracting H2 2025 data (July 1 - December 31) from table: {table_name}")
    print(
        f"📅 Filtering: transaction_date from 2025-07-01 to 2025-12-31 (both M/D/YYYY and YYYY-MM-DD formats)"
    )

    # Create resource for the target table
    resource = create_full_extraction_resource(ch_conn, table_name)

    return [resource]


@dlt.source
def clickhouse_full_source():
    """DLT source wrapper for full carrier invoice extraction"""
    return clickhouse_full_extraction_source()


def create_full_extraction_resource(ch_conn, table_name):
    """Create a dlt resource for FULL table extraction without date filtering"""

    @dlt.resource(
        name="full_carrier_invoice_data",
        write_disposition="replace",  # Replace mode for full extraction
        primary_key="invoice_number",
    )
    def full_extraction_resource():
        """Extract ALL data from ClickHouse carrier_carrier_invoice_original_flat_ups table"""

        try:
            # Get table schema
            schema = ch_conn.get_table_schema(table_name)
            print(f"📋 Schema for {table_name}: {len(schema)} columns")

            # Configure batching for large dataset extraction
            BATCH_SIZE = int(os.getenv("DLT_CLICKHOUSE_BATCH_SIZE", "50000"))
            total_extracted = 0

            # Composite ordering for stable, keyset pagination
            order_time_col = "import_time"
            order_tie_col = "invoice_number"

            print(
                f"📥 Full load from {table_name} (H2 2025: July 1 - December 31, batching enabled)"
            )

            # Window configuration (seconds). Default: 1 hour
            WINDOW_SECONDS = int(os.getenv("DLT_CLICKHOUSE_WINDOW_SECONDS", "3600"))

            # Get min/max time bounds for H2 2025 data only (July 1 - December 31, 2025)
            # Handle both date formats: M/D/YYYY and YYYY-MM-DD
            date_filter_clause = """
                WHERE (
                    -- Match YYYY-MM-DD format (2025-07-01 to 2025-12-31)
                    (transaction_date >= '2025-07-01' AND transaction_date <= '2025-12-31')
                    OR
                    -- Match M/D/YYYY format by converting to date
                    (parseDateTimeBestEffortOrNull(transaction_date) >= toDate('2025-07-01')
                     AND parseDateTimeBestEffortOrNull(transaction_date) <= toDate('2025-12-31'))
                )
            """

            min_time_rows = ch_conn.execute_query(
                f"SELECT min({order_time_col}) FROM {table_name} {date_filter_clause}"
            )
            max_time_rows = ch_conn.execute_query(
                f"SELECT max({order_time_col}) FROM {table_name} {date_filter_clause}"
            )
            min_time = (
                min_time_rows[0][0] if min_time_rows and min_time_rows[0] else None
            )
            max_time = (
                max_time_rows[0][0] if max_time_rows and max_time_rows[0] else None
            )

            if not (min_time and max_time):
                print(f"ℹ️ No data found in {table_name}")
                yield []
            else:
                print(f"📅 Data range: {min_time} to {max_time}")
                start_time = min_time
                while start_time <= max_time:
                    end_time = start_time + timedelta(seconds=WINDOW_SECONDS)
                    cursor_id = ""

                    while True:
                        # Query WITH H2 2025 transaction_date filtering (July 1 - December 31)
                        query = f"""
                            SELECT * FROM {table_name}
                            WHERE (
                                -- Match YYYY-MM-DD format (2025-07-01 to 2025-12-31)
                                (transaction_date >= '2025-07-01' AND transaction_date <= '2025-12-31')
                                OR
                                -- Match M/D/YYYY format by converting to date
                                (parseDateTimeBestEffortOrNull(transaction_date) >= toDate('2025-07-01')
                                 AND parseDateTimeBestEffortOrNull(transaction_date) <= toDate('2025-12-31'))
                            )
                            AND {order_time_col} >= %(start_time)s
                            AND {order_time_col} < %(end_time)s
                            AND ( %(cursor_id)s = '' OR {order_tie_col} > %(cursor_id)s )
                            ORDER BY {order_tie_col}
                            LIMIT {BATCH_SIZE}
                        """
                        parameters = {
                            "start_time": start_time,
                            "end_time": end_time,
                            "cursor_id": cursor_id,
                        }
                        rows = ch_conn.execute_query(query, parameters)
                        if not rows:
                            break

                        column_names = (
                            [col[0] for col in schema]
                            if schema
                            else [f"col_{i}" for i in range(len(rows[0]))]
                        )

                        batch = []
                        for row in rows:
                            record = dict(zip(column_names, row))
                            record["_extracted_at"] = datetime.now()
                            record["_source_table"] = table_name
                            batch.append(record)

                        total_extracted += len(batch)
                        print(
                            f"✅ Extracted batch: {len(batch)} rows (total: {total_extracted:,})"
                        )
                        yield batch

                        cursor_id = batch[-1].get(order_tie_col, "")

                    start_time = end_time

                if total_extracted == 0:
                    print(f"ℹ️ No data found in {table_name}")
                    yield []

        except Exception as e:
            print(f"❌ Failed to extract from {table_name}: {e}")
            import traceback

            traceback.print_exc()
            raise

    return full_extraction_resource


def run_full_extraction(destination="duckdb"):
    """
    Run the biannual extraction pipeline that extracts H2 2025 (July 1 - December 31)
    carrier invoice data from ClickHouse

    Args:
        destination: Destination for the extracted data (default: "duckdb")

    Returns:
        dlt.Pipeline: The completed pipeline object
    """
    print("🚀 ClickHouse Biannual Data Extraction Pipeline (H2 2025)")
    print("=" * 60)
    print("📅 Extracting July 1 - December 31, 2025 records from source table")
    print("=" * 60)

    # Create pipeline with unique name to avoid conflicts
    pipeline_name = "full_carrier_invoice_extraction"
    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=destination,
        dataset_name="full_carrier_invoice_data",
    )

    # Run extraction
    print(f"📥 Extracting H2 2025 data (July 1 - December 31) from ClickHouse...")
    print(f"🎯 Target table: carrier_carrier_invoice_original_flat_ups")
    print(f"📅 Date filter: 2025-07-01 to 2025-12-31 (both date formats)")
    print(f"📍 Destination: {destination}")
    print(f"📁 Output file: full_carrier_invoice_extraction.duckdb")

    try:
        # Create and run the ClickHouse source
        source = clickhouse_full_source()
        info = pipeline.run(source)

        print(f"\n✅ Full extraction pipeline completed successfully!")
        print(f"📊 Load info: {info}")

        # Analyze extracted data
        with pipeline.sql_client() as client:
            # Show summary for carrier invoice data
            try:
                count = client.execute_sql(
                    "SELECT COUNT(*) FROM full_carrier_invoice_data LIMIT 1"
                )[0][0]
                print(f"\n📊 full_carrier_invoice_data: {count:,} rows extracted")

                if count > 0:
                    # Get column information
                    columns = client.execute_sql(
                        "SELECT * FROM full_carrier_invoice_data LIMIT 1"
                    )
                    if columns:
                        column_names = [desc[0] for desc in client._conn.description]
                        print(f"📋 Columns: {len(column_names)} total")
                        print(f"   - {column_names[0]}: {type(columns[0][0]).__name__}")
                        print(f"   - {column_names[1]}: {type(columns[0][1]).__name__}")
                        print(f"   - {column_names[2]}: {type(columns[0][2]).__name__}")
                        print(f"   - {column_names[3]}: {type(columns[0][3]).__name__}")
                        print(f"   - {column_names[4]}: {type(columns[0][4]).__name__}")
                        print(f"   ... and {len(column_names) - 5} more columns")

                    # Get distinct transaction dates
                    print(f"\n📅 Analyzing transaction_date distribution...")
                    date_stats = client.execute_sql(
                        """
                        SELECT
                            MIN(transaction_date) as min_date,
                            MAX(transaction_date) as max_date,
                            COUNT(DISTINCT transaction_date) as distinct_dates
                        FROM full_carrier_invoice_data
                        WHERE transaction_date IS NOT NULL AND transaction_date != ''
                        """
                    )
                    if date_stats and date_stats[0]:
                        min_date, max_date, distinct_dates = date_stats[0]
                        print(f"   📊 Min transaction_date: {min_date}")
                        print(f"   📊 Max transaction_date: {max_date}")
                        print(f"   📊 Distinct dates: {distinct_dates}")

                    # Show top 10 transaction dates by count
                    print(f"\n📊 Top 10 transaction dates by record count:")
                    top_dates = client.execute_sql(
                        """
                        SELECT
                            transaction_date,
                            COUNT(*) as record_count
                        FROM full_carrier_invoice_data
                        WHERE transaction_date IS NOT NULL AND transaction_date != ''
                        GROUP BY transaction_date
                        ORDER BY transaction_date DESC
                        LIMIT 10
                        """
                    )
                    if top_dates:
                        for date, count in top_dates:
                            print(f"   {date}: {count:,} records")

            except Exception as e:
                print(f"⚠️ Could not analyze data: {e}")

        return pipeline

    except Exception as e:
        print(f"❌ Pipeline execution failed: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    """Main entry point for the full extraction script"""
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Run the full extraction pipeline
    pipeline = run_full_extraction(destination="duckdb")

    print("\n✅ Full extraction completed!")
    print(f"📁 Output file: full_carrier_invoice_extraction.duckdb")
    print(f"📊 You can now analyze the data using DuckDB or the Jupyter notebook")
