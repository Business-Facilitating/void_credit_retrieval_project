#!/usr/bin/env python3
"""
Export data from DuckDB and verify date formats
"""

import duckdb
import pandas as pd
import os
from datetime import datetime
import re

def export_and_verify_dates():
    """Export data from DuckDB and verify date formats"""
    
    print('🔍 Exporting data and verifying date formats...')
    
    try:
        conn = duckdb.connect("carrier_invoice_extraction.duckdb")
        
        # Try to find any table with data
        print("📊 Searching for tables...")
        
        # Try different approaches to find tables
        table_found = False
        full_table_name = None
        
        # Method 1: Direct SHOW TABLES
        try:
            tables = conn.execute("SHOW TABLES").fetchall()
            if tables:
                table_name = tables[0][0]
                full_table_name = table_name
                table_found = True
                print(f"✅ Found table: {table_name}")
        except:
            pass
        
        # Method 2: Try with schema prefix
        if not table_found:
            try:
                # Try carrier_invoice_data schema
                tables = conn.execute("SHOW TABLES FROM carrier_invoice_data").fetchall()
                if tables:
                    table_name = tables[0][0]
                    full_table_name = f"carrier_invoice_data.{table_name}"
                    table_found = True
                    print(f"✅ Found table: {full_table_name}")
            except:
                pass
        
        # Method 3: Try information_schema
        if not table_found:
            try:
                tables = conn.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema != 'information_schema'").fetchall()
                if tables:
                    schema, table_name = tables[0]
                    full_table_name = f"{schema}.{table_name}" if schema != 'main' else table_name
                    table_found = True
                    print(f"✅ Found table: {full_table_name}")
            except:
                pass
        
        if not table_found:
            print("❌ No tables found in DuckDB database")
            conn.close()
            return
        
        # Get basic info about the table
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM {full_table_name}").fetchone()[0]
            print(f"📊 Total rows in table: {count:,}")
            
            # Get column info
            columns = conn.execute(f"DESCRIBE {full_table_name}").fetchall()
            date_columns = [col[0] for col in columns if 'date' in col[0].lower()]
            print(f"📋 Date-related columns: {date_columns}")
            
        except Exception as e:
            print(f"❌ Error getting table info: {e}")
            conn.close()
            return
        
        # Export a sample to CSV for verification
        print(f"\n📤 Exporting sample data to CSV...")
        
        try:
            # Create output directory
            os.makedirs("data/output", exist_ok=True)
            
            # Export sample data (first 1000 rows)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"date_verification_sample_{timestamp}.csv"
            csv_path = os.path.join("data/output", csv_filename)
            
            # Query with focus on date columns
            if 'invoice_date' in date_columns and 'transaction_date' in date_columns:
                query = f"""
                SELECT invoice_date, transaction_date, invoice_number, 
                       import_time, _extracted_at
                FROM {full_table_name} 
                WHERE invoice_date IS NOT NULL 
                  AND transaction_date IS NOT NULL
                LIMIT 1000
                """
            else:
                # Fallback to all columns
                query = f"SELECT * FROM {full_table_name} LIMIT 1000"
            
            df = conn.execute(query).df()
            df.to_csv(csv_path, index=False)
            
            print(f"✅ Sample exported: {csv_path}")
            print(f"📊 Sample size: {len(df):,} rows, {len(df.columns)} columns")
            
            # Verify date formats in the exported sample
            print(f"\n🔍 Verifying date formats in exported sample...")
            
            for date_col in ['invoice_date', 'transaction_date']:
                if date_col in df.columns:
                    print(f"\n📅 Checking {date_col}:")
                    
                    # Get non-null values
                    date_values = df[date_col].dropna()
                    print(f"   📊 Non-null values: {len(date_values):,}")
                    
                    if len(date_values) > 0:
                        # Show sample values
                        print(f"   📋 Sample values:")
                        for i, val in enumerate(date_values.head(5)):
                            is_valid = bool(re.match(r'^\d{4}-\d{2}-\d{2}$', str(val)))
                            status = "✅" if is_valid else "❌"
                            print(f"      {status} {val}")
                        
                        # Check all values
                        all_valid = date_values.astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$').sum()
                        total = len(date_values)
                        
                        print(f"   📊 Format validation: {all_valid:,}/{total:,} in YYYY-MM-DD format")
                        
                        if all_valid == total:
                            print(f"   ✅ All {date_col} values are properly standardized!")
                        else:
                            print(f"   ⚠️ {total - all_valid:,} values may not be in YYYY-MM-DD format")
                            
                            # Show non-standard formats
                            non_standard = date_values[~date_values.astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$')]
                            if len(non_standard) > 0:
                                print(f"   📋 Non-standard formats found:")
                                for val in non_standard.head(3):
                                    print(f"      ❌ {val}")
                else:
                    print(f"   ❌ {date_col} column not found")
            
        except Exception as e:
            print(f"❌ Error exporting/verifying data: {e}")
            import traceback
            traceback.print_exc()
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error connecting to DuckDB: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n✅ Export and verification completed!")

if __name__ == "__main__":
    export_and_verify_dates()
