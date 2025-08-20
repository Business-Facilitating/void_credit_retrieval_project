#!/usr/bin/env python3
"""
Verify that invoice_date and transaction_date are properly standardized in the extracted data
"""

import duckdb
import pandas as pd
import os
from datetime import datetime
import re

def verify_date_standardization():
    """Verify date standardization in DuckDB and CSV output"""
    
    print('🔍 Verifying date standardization in extracted data...')
    print('=' * 60)
    
    # Check DuckDB database first
    try:
        conn = duckdb.connect("carrier_invoice_extraction.duckdb")
        
        # Try to find tables using different approaches
        tables = []
        schemas_to_check = ['main', 'carrier_invoice_data']
        
        for schema in schemas_to_check:
            try:
                if schema == 'main':
                    schema_tables = conn.execute("SHOW TABLES").fetchall()
                else:
                    schema_tables = conn.execute(f"SHOW TABLES FROM {schema}").fetchall()
                
                if schema_tables:
                    print(f"📊 Found tables in {schema} schema: {[t[0] for t in schema_tables]}")
                    tables.extend([(schema, t[0]) for t in schema_tables])
                    
            except Exception as e:
                print(f"⚠️ Could not access {schema} schema: {e}")
        
        if tables:
            # Use the first table found
            schema, table_name = tables[0]
            full_table_name = f"{schema}.{table_name}" if schema != 'main' else table_name
            
            print(f"\n📋 Analyzing table: {full_table_name}")
            
            try:
                # Get row count
                count = conn.execute(f"SELECT COUNT(*) FROM {full_table_name}").fetchone()[0]
                print(f"📊 Total rows: {count:,}")
                
                # Check date columns
                for date_col in ['invoice_date', 'transaction_date']:
                    print(f"\n🔍 Analyzing {date_col} column:")
                    
                    # Get sample values and check format
                    sample_query = f"""
                    SELECT {date_col}, COUNT(*) as count
                    FROM {full_table_name} 
                    WHERE {date_col} IS NOT NULL 
                    GROUP BY {date_col}
                    ORDER BY count DESC 
                    LIMIT 10
                    """
                    
                    try:
                        results = conn.execute(sample_query).fetchall()
                        print(f"   📋 Sample {date_col} values:")
                        
                        valid_format_count = 0
                        total_checked = 0
                        
                        for row in results[:5]:  # Check first 5 samples
                            date_val = str(row[0])
                            count = row[1]
                            
                            # Check if format is YYYY-MM-DD
                            is_valid = bool(re.match(r'^\d{4}-\d{2}-\d{2}$', date_val))
                            status = "✅" if is_valid else "❌"
                            
                            print(f"      {status} {date_val} ({count:,} records)")
                            
                            if is_valid:
                                valid_format_count += count
                            total_checked += count
                        
                        # Get total non-null count for this column
                        total_non_null = conn.execute(f"SELECT COUNT(*) FROM {full_table_name} WHERE {date_col} IS NOT NULL").fetchone()[0]
                        
                        print(f"   📊 Format validation (sample): {valid_format_count:,}/{total_checked:,} records in YYYY-MM-DD format")
                        print(f"   📊 Total non-null {date_col} records: {total_non_null:,}")
                        
                    except Exception as e:
                        print(f"   ❌ Error analyzing {date_col}: {e}")
                
            except Exception as e:
                print(f"❌ Error analyzing table: {e}")
        else:
            print("❌ No tables found in DuckDB database")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error connecting to DuckDB: {e}")
    
    # Check CSV files
    print(f"\n📁 Checking CSV files...")
    print('=' * 40)
    
    csv_files = [f for f in os.listdir("data/output") if f.endswith('.csv') and 'carrier_invoice' in f]
    
    if csv_files:
        # Check the most recent CSV
        latest_csv = sorted(csv_files)[-1]
        csv_path = os.path.join("data/output", latest_csv)
        print(f"📄 Analyzing latest CSV: {latest_csv}")
        
        try:
            # Read sample of CSV
            df_sample = pd.read_csv(csv_path, nrows=1000)  # Read first 1000 rows
            print(f"📊 CSV sample loaded: {len(df_sample):,} rows")
            
            # Check date columns
            for date_col in ['invoice_date', 'transaction_date']:
                if date_col in df_sample.columns:
                    print(f"\n🔍 Analyzing {date_col} in CSV:")
                    
                    # Get non-null values
                    date_values = df_sample[date_col].dropna()
                    print(f"   📊 Non-null values in sample: {len(date_values):,}")
                    
                    if len(date_values) > 0:
                        # Check format consistency
                        valid_format_count = 0
                        
                        print(f"   📋 Sample values:")
                        for i, val in enumerate(date_values.head(5)):
                            is_valid = bool(re.match(r'^\d{4}-\d{2}-\d{2}$', str(val)))
                            status = "✅" if is_valid else "❌"
                            print(f"      {status} {val}")
                            
                            if is_valid:
                                valid_format_count += 1
                        
                        # Check all values in sample
                        all_valid = date_values.astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$').sum()
                        
                        print(f"   📊 Format validation: {all_valid:,}/{len(date_values):,} values in YYYY-MM-DD format")
                        
                        if all_valid == len(date_values):
                            print(f"   ✅ All {date_col} values follow YYYY-MM-DD format!")
                        else:
                            print(f"   ⚠️ Some {date_col} values may not follow YYYY-MM-DD format")
                    
                else:
                    print(f"   ❌ {date_col} column not found in CSV")
                    
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
    else:
        print("❌ No carrier invoice CSV files found")
    
    print(f"\n✅ Date standardization verification completed!")

if __name__ == "__main__":
    verify_date_standardization()
