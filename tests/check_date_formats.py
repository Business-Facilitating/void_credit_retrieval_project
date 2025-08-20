#!/usr/bin/env python3
"""
Check date formats in DuckDB database and CSV files
"""

import duckdb
import pandas as pd
import os
from datetime import datetime

def check_date_formats():
    """Check date formats in DuckDB and CSV files"""
    
    print('🔍 Checking date formats in data...')
    
    # Check DuckDB database
    try:
        conn = duckdb.connect("carrier_invoice_extraction.duckdb")
        
        # Try to find tables
        try:
            # Try different approaches to list tables
            tables = []
            try:
                tables = conn.execute("SHOW TABLES").fetchall()
            except:
                try:
                    tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()
                except:
                    # Try DLT specific schema
                    tables = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'carrier_invoice_data'").fetchall()
            
            if tables:
                table_name = tables[0][0]
                print(f"📊 Found table: {table_name}")
                
                # Check if we need schema prefix
                full_table_name = table_name
                try:
                    # Test query
                    conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
                except:
                    # Try with schema prefix
                    full_table_name = f"carrier_invoice_data.{table_name}"
                
                # Get column information
                try:
                    columns = conn.execute(f"DESCRIBE {full_table_name}").fetchall()
                    print(f"📋 Total columns: {len(columns)}")
                    
                    # Look for date columns
                    date_columns = []
                    for col in columns:
                        col_name = col[0].lower()
                        if 'date' in col_name or 'time' in col_name:
                            date_columns.append(col)
                    
                    print(f"📅 Date-related columns found: {len(date_columns)}")
                    for col in date_columns:
                        print(f"   - {col[0]}: {col[1]}")
                    
                    # Check specific columns: invoice_date and transaction_date
                    for date_col in ['invoice_date', 'transaction_date']:
                        try:
                            sample_query = f"""
                            SELECT {date_col}, 
                                   typeof({date_col}) as data_type,
                                   COUNT(*) as count
                            FROM {full_table_name} 
                            WHERE {date_col} IS NOT NULL 
                            GROUP BY {date_col}, typeof({date_col})
                            ORDER BY count DESC 
                            LIMIT 10
                            """
                            
                            results = conn.execute(sample_query).fetchall()
                            print(f"\n📊 Sample {date_col} values and types:")
                            for row in results:
                                print(f"   {row[0]} ({row[1]}) - {row[2]:,} records")
                                
                        except Exception as e:
                            print(f"❌ Error checking {date_col}: {e}")
                    
                    # Check total row count
                    count = conn.execute(f"SELECT COUNT(*) FROM {full_table_name}").fetchone()[0]
                    print(f"\n📊 Total rows in database: {count:,}")
                    
                except Exception as e:
                    print(f"❌ Error analyzing table structure: {e}")
                    
            else:
                print("❌ No tables found in DuckDB database")
                
        except Exception as e:
            print(f"❌ Error accessing DuckDB: {e}")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Error connecting to DuckDB: {e}")
    
    # Check CSV files
    print(f"\n📁 Checking CSV files in data/output...")
    csv_files = [f for f in os.listdir("data/output") if f.endswith('.csv') and 'carrier_invoice' in f]
    
    if csv_files:
        # Check the most recent carrier invoice CSV
        latest_csv = sorted(csv_files)[-1]
        csv_path = os.path.join("data/output", latest_csv)
        print(f"📄 Checking latest CSV: {latest_csv}")
        
        try:
            # Read just the first few rows to check format
            df = pd.read_csv(csv_path, nrows=5)
            print(f"📊 CSV columns: {len(df.columns)}")
            
            # Check for date columns
            date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
            print(f"📅 Date columns in CSV: {date_cols}")
            
            for col in ['invoice_date', 'transaction_date']:
                if col in df.columns:
                    print(f"\n📊 Sample {col} values from CSV:")
                    sample_values = df[col].dropna().head(5).tolist()
                    for val in sample_values:
                        print(f"   {val}")
                else:
                    print(f"❌ Column {col} not found in CSV")
                    
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
    else:
        print("❌ No carrier invoice CSV files found")

if __name__ == "__main__":
    check_date_formats()
