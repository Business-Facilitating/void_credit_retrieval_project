#!/usr/bin/env python3
"""
ClickHouse to DuckDB Data Pipeline
=================================

Simplified pipeline for extracting carrier invoice data from ClickHouse
and loading it into DuckDB for local analysis.

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List

import dlt
import pandas as pd
from dateutil import parser

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


def standardize_date_format(record, date_column):
    """
    Standardize date format to YYYY-MM-DD for a specific column in a record

    Args:
        record (dict): The data record
        date_column (str): The name of the date column to standardize
    """
    if date_column in record and record[date_column]:
        try:
            # Handle various date formats and convert to YYYY-MM-DD
            date_val = record[date_column]
            if isinstance(date_val, str):
                # Parse string dates and standardize
                from dateutil import parser

                parsed_date = parser.parse(date_val)
                record[date_column] = parsed_date.strftime("%Y-%m-%d")
            elif hasattr(date_val, "strftime"):
                # Handle datetime/date objects
                record[date_column] = date_val.strftime("%Y-%m-%d")
        except Exception as e:
            print(
                f"⚠️ Date formatting warning for {date_column} '{record[date_column]}': {e}"
            )
            # Keep original value if parsing fails


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
            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database,
                secure=self.secure,
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


def clickhouse_carrier_invoice_source():
    """
    DLT source that extracts data FROM ClickHouse carrier_carrier_invoice_original_flat_ups table

    Note: Using hardcoded credentials to avoid DLT configuration injection issues
    """

    # Target table name
    table_name = "carrier_carrier_invoice_original_flat_ups"

    # Create connection with hardcoded working credentials
    ch_conn = ClickHouseConnection(
        host="pgy8egpix3.us-east-1.aws.clickhouse.cloud",
        port=8443,
        username="gabriellapuz",
        password="PTN.776)RR3s",
        database="peerdb",
        secure=True,
    )

    connection_success = ch_conn.connect()

    if not connection_success:
        raise ConnectionError(
            "Failed to connect to ClickHouse. Please check your connection settings and SSL configuration."
        )

    print(f"🎯 Extracting data from table: {table_name}")

    # Create resource for the target table
    resource = create_carrier_invoice_resource(ch_conn, table_name)

    return [resource]


@dlt.source
def clickhouse_source():
    """DLT source wrapper for carrier invoice extraction"""
    return clickhouse_carrier_invoice_source()


def create_carrier_invoice_resource(ch_conn, table_name):
    """Create a dlt resource for the carrier_carrier_invoice_original_flat_ups table with incremental loading"""

    @dlt.resource(
        name="carrier_invoice_data",
        write_disposition=os.getenv("DLT_WRITE_DISPOSITION", "append"),
        primary_key="invoice_number",  # Using invoice_number as primary key
    )
    def carrier_invoice_resource(
        updated_at=dlt.sources.incremental(
            "import_time", initial_value=datetime(2020, 1, 1)
        )
    ):
        """Extract data from ClickHouse carrier_carrier_invoice_original_flat_ups table"""

        try:
            # Get table schema
            schema = ch_conn.get_table_schema(table_name)
            print(f"📋 Schema for {table_name}: {len(schema)} columns")

            # Check if table has timestamp column for incremental loading
            timestamp_columns = [
                col[0]
                for col in schema
                if "date" in col[1].lower()
                or "time" in col[1].lower()
                or "created" in col[1].lower()
                or "updated" in col[1].lower()
            ]

            # Configure batching for large dataset extraction
            BATCH_SIZE = int(
                os.getenv("DLT_CLICKHOUSE_BATCH_SIZE", "50000")
            )  # e.g., 50000 or 100000
            total_extracted = 0

            # Composite ordering for stable, keyset pagination
            order_time_col = "import_time"
            order_tie_col = "invoice_number"

            # Allow forcing full-load via env var
            FORCE_FULL = os.getenv("DLT_FORCE_FULL_LOAD", "false").lower() in (
                "1",
                "true",
                "yes",
            )
            if FORCE_FULL:
                print(
                    "♻️ Force full-load mode enabled. Incremental cursor will be bypassed."
                )

            if (not FORCE_FULL) and timestamp_columns and updated_at.last_value:
                # Incremental load using time-windowed, keyset pagination to avoid large sorts
                timestamp_col = timestamp_columns[0]
                print(
                    f"🔄 Incremental load from {table_name} since {updated_at.last_value}"
                )
                print(f"📅 Using timestamp column: {timestamp_col}")

                # Window configuration (seconds). Default: 1 hour
                WINDOW_SECONDS = int(os.getenv("DLT_CLICKHOUSE_WINDOW_SECONDS", "3600"))
                # Date cutoff for invoice_date (days). Default: 30 days
                CUTOFF_DAYS = int(os.getenv("DLT_INVOICE_CUTOFF_DAYS", "30"))
                cutoff_date = (datetime.utcnow() - timedelta(days=CUTOFF_DAYS)).date()
                cutoff_time = datetime.utcnow() - timedelta(days=CUTOFF_DAYS)

                # Get upper bound for this run (respecting invoice_date cutoff)
                max_time_rows = ch_conn.execute_query(
                    f"SELECT max({order_time_col}) FROM {table_name} WHERE invoice_date >= %(cutoff_date)s",
                    {"cutoff_date": cutoff_date},
                )
                max_time = (
                    max_time_rows[0][0] if max_time_rows and max_time_rows[0] else None
                )

                # Start no earlier than the cutoff window to avoid scanning old ranges
                start_time = updated_at.last_value
                if start_time < cutoff_time:
                    start_time = cutoff_time
                while max_time and start_time <= max_time:
                    end_time = start_time + timedelta(seconds=WINDOW_SECONDS)
                    cursor_id = ""

                    while True:
                        query = (
                            f"SELECT * FROM {table_name} "
                            f"WHERE invoice_date >= %(cutoff_date)s "
                            f"  AND {order_time_col} >= %(start_time)s "
                            f"  AND {order_time_col} < %(end_time)s "
                            f"  AND ( %(cursor_id)s = '' OR {order_tie_col} > %(cursor_id)s ) "
                            f"ORDER BY {order_tie_col} "
                            f"LIMIT {BATCH_SIZE}"
                        )
                        parameters = {
                            "cutoff_date": cutoff_date,
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

                            # Standardize date formats to YYYY-MM-DD
                            # Key date columns: invoice_date, transaction_date
                            standardize_date_format(record, "invoice_date")
                            standardize_date_format(record, "transaction_date")

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
                    print(f"ℹ️ No new data in {table_name}")
                    yield []
            else:
                # Full load: time-windowed, keyset pagination across the entire table
                print(f"📥 Full load from {table_name} (no LIMIT; batching enabled)")

                WINDOW_SECONDS = int(os.getenv("DLT_CLICKHOUSE_WINDOW_SECONDS", "3600"))

                # Determine bounds limited by invoice_date cutoff
                CUTOFF_DAYS = int(os.getenv("DLT_INVOICE_CUTOFF_DAYS", "30"))
                cutoff_date = (datetime.utcnow() - timedelta(days=CUTOFF_DAYS)).date()

                min_time_rows = ch_conn.execute_query(
                    f"SELECT min({order_time_col}) FROM {table_name} WHERE invoice_date >= %(cutoff_date)s",
                    {"cutoff_date": cutoff_date},
                )
                max_time_rows = ch_conn.execute_query(
                    f"SELECT max({order_time_col}) FROM {table_name} WHERE invoice_date >= %(cutoff_date)s",
                    {"cutoff_date": cutoff_date},
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
                    start_time = min_time
                    while start_time <= max_time:
                        end_time = start_time + timedelta(seconds=WINDOW_SECONDS)
                        cursor_id = ""

                        while True:
                            query = (
                                f"SELECT * FROM {table_name} "
                                f"WHERE invoice_date >= %(cutoff_date)s "
                                f"  AND {order_time_col} >= %(start_time)s "
                                f"  AND {order_time_col} < %(end_time)s "
                                f"  AND ( %(cursor_id)s = '' OR {order_tie_col} > %(cursor_id)s ) "
                                f"ORDER BY {order_tie_col} "
                                f"LIMIT {BATCH_SIZE}"
                            )
                            parameters = {
                                "cutoff_date": cutoff_date,
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

                                # Standardize date formats to YYYY-MM-DD
                                # Key date columns: invoice_date, transaction_date
                                standardize_date_format(record, "invoice_date")
                                standardize_date_format(record, "transaction_date")

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
            raise  # Re-raise the exception instead of yielding empty data

    return carrier_invoice_resource


def run_carrier_invoice_extraction(destination="duckdb", pipeline_name_suffix=""):
    """
    Run the main pipeline that extracts carrier invoice data from ClickHouse to DuckDB

    Args:
        destination: Destination for the extracted data (default: "duckdb")
        pipeline_name_suffix: Optional suffix for pipeline name to avoid conflicts

    Returns:
        dlt.Pipeline: The completed pipeline object
    """
    print("🚀 ClickHouse Carrier Invoice Data Extraction Pipeline")
    print("=" * 60)

    # Create pipeline with optional suffix to avoid file locks
    pipeline_name = "carrier_invoice_extraction" + pipeline_name_suffix
    pipeline = dlt.pipeline(
        pipeline_name=pipeline_name,
        destination=destination,
        dataset_name="carrier_invoice_data",
    )

    # Run extraction
    print(f"📥 Extracting data from ClickHouse...")
    print(f"🎯 Target table: carrier_carrier_invoice_original_flat_ups")
    print(f"📍 Destination: {destination}")

    try:
        # Create and run the ClickHouse source
        source = clickhouse_source()
        info = pipeline.run(source)

        print(f"\n✅ Extraction pipeline completed successfully!")
        print(f"📊 Load info: {info}")

        # Analyze extracted data
        with pipeline.sql_client() as client:
            # Show summary for carrier invoice data
            try:
                count = client.execute_sql(
                    "SELECT COUNT(*) FROM carrier_invoice_data LIMIT 20"
                )[0][0]
                print(f"\n📊 carrier_invoice_data: {count} rows extracted")

                if count > 0:
                    # Show column information
                    columns = client.execute_sql("DESCRIBE carrier_invoice_data")
                    print(f"📋 Columns: {len(columns)} total")
                    for col in columns[:5]:  # Show first 5 columns
                        print(f"   - {col[0]}: {col[1]}")
                    if len(columns) > 5:
                        print(f"   ... and {len(columns) - 5} more columns")

                    # Show sample data
                    sample = client.execute_sql(
                        "SELECT * FROM carrier_invoice_data LIMIT 2"
                    )
                    if sample:
                        print(f"\n📋 Sample data (first 2 rows):")
                        for i, row in enumerate(sample):
                            print(f"   Row {i+1}: {str(row)[:150]}...")
                else:
                    print(
                        "ℹ️ No data was extracted - table may be empty or connection issues occurred"
                    )

            except Exception as e:
                print(f"❌ Error analyzing carrier_invoice_data: {e}")

        # Export to CSV if data was extracted successfully
        try:
            export_to_csv(pipeline)
        except Exception as e:
            print(f"⚠️ CSV export failed: {e}")

        return pipeline

    except Exception as e:
        print(f"❌ Extraction pipeline failed: {e}")
        print("\n💡 Next steps to resolve:")
        print("   1. Check your ClickHouse connection settings")
        print("   2. Verify SSL configuration")
        print("   3. Confirm table 'carrier_carrier_invoice_original_flat_ups' exists")
        print("   4. Check database permissions")
        return None


def export_to_csv(pipeline):
    """
    Export the extracted carrier invoice data to CSV with timestamp-based filename

    Args:
        pipeline: The DLT pipeline object
    """
    import os
    from datetime import datetime

    import pandas as pd

    print(f"\n📤 Exporting data to CSV...")

    try:
        # Create output directory if it doesn't exist
        output_dir = "data/output"
        os.makedirs(output_dir, exist_ok=True)

        # Generate timestamp-based filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"carrier_invoice_data_30days_{timestamp}.csv"
        csv_path = os.path.join(output_dir, csv_filename)

        # Query all data from DuckDB
        with pipeline.sql_client() as client:
            # Get row count first
            count_result = client.execute_sql(
                "SELECT COUNT(*) FROM carrier_invoice_data"
            )
            total_rows = count_result[0][0] if count_result else 0

            if total_rows == 0:
                print("ℹ️ No data to export - table is empty")
                return

            print(f"📊 Exporting {total_rows:,} rows to CSV...")

            # Export all data to CSV
            # Use pandas for better CSV handling
            query = "SELECT * FROM carrier_invoice_data ORDER BY invoice_date DESC, invoice_number"

            # Execute query and get results
            rows = client.execute_sql(query)
            columns = client.execute_sql("DESCRIBE carrier_invoice_data")
            column_names = [col[0] for col in columns]

            # Create DataFrame
            df = pd.DataFrame(rows, columns=column_names)

            # Export to CSV
            df.to_csv(csv_path, index=False, encoding="utf-8")

            print(f"✅ CSV export completed successfully!")
            print(f"📁 File saved: {csv_path}")
            print(f"📊 Exported {len(df):,} rows with {len(df.columns)} columns")

            # Show date range in exported data
            if "invoice_date" in df.columns:
                min_date = df["invoice_date"].min()
                max_date = df["invoice_date"].max()
                print(f"📅 Date range: {min_date} to {max_date}")

    except Exception as e:
        print(f"❌ CSV export failed: {e}")
        import traceback

        traceback.print_exc()


def query_duckdb_data(pipeline_name="carrier_invoice_extraction", limit=10):
    """
    Query the DuckDB file created by the pipeline

    Args:
        pipeline_name: Name of the pipeline (used to find the DuckDB file)
        limit: Number of rows to return (default: 10)

    Returns:
        List of rows from the query
    """
    if not DUCKDB_AVAILABLE:
        print("❌ DuckDB not available for querying")
        return None

    try:
        # Connect to the DuckDB file created by the pipeline
        db_path = f"{pipeline_name}.duckdb"
        conn = duckdb.connect(db_path)

        print(f"🔍 Querying DuckDB file: {db_path}")

        # Execute query (DuckDB uses schema.table format)
        query = f"SELECT * FROM carrier_invoice_data.carrier_invoice_data LIMIT {limit}"
        result = conn.execute(query).fetchall()

        # Get column names
        columns = [desc[0] for desc in conn.description]

        print(f"✅ Query completed: {len(result)} rows returned")
        print(f"📋 Columns: {columns}")

        # Display results
        if result:
            print(f"\n📊 Data preview (first {min(len(result), limit)} rows):")
            for i, row in enumerate(result):
                print(f"   Row {i+1}: {dict(zip(columns, row))}")
        else:
            print("ℹ️ No data found in carrier_invoice_data table")

        conn.close()
        return result

    except Exception as e:
        print(f"❌ Failed to query DuckDB: {e}")
        print("💡 Make sure the pipeline has run successfully first")
        return None


if __name__ == "__main__":
    print("🚀 ClickHouse to DuckDB Pipeline")
    print("=" * 40)

    # Run the extraction pipeline
    print("\n1. Running carrier invoice extraction...")
    pipeline = run_carrier_invoice_extraction()

    if pipeline:
        print("\n2. Querying extracted data...")
        query_duckdb_data(limit=5)

    print("\n✅ Pipeline execution completed!")
    print("\n✅ Pipeline execution completed!")
    print("\n✅ Pipeline execution completed!")
