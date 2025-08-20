#!/usr/bin/env python3
"""
Export existing data from DuckDB to CSV and examine date formats
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add src path
sys.path.append('src/src')

def export_and_examine():
    """Export existing DuckDB data to CSV and examine date formats"""
    print("📤 Exporting existing DuckDB data to CSV...")
    
    try:
        import dlt
        from dlt_pipeline_examples import export_to_csv
        
        # Create a pipeline object to use for export
        pipeline = dlt.pipeline(
            pipeline_name="carrier_invoice_extraction",
            destination="duckdb",
            dataset_name="carrier_invoice_data",
        )
        
        # Try to export existing data
        export_to_csv(pipeline)
        
        # Find the newest CSV file
        output_dir = "data/output"
        csv_files = []
        
        for file in os.listdir(output_dir):
            if file.startswith("carrier_invoice_data_30days_") and file.endswith(".csv"):
                csv_files.append(file)
        
        if not csv_files:
            print("❌ No CSV files found after export")
            return False
        
        # Get the most recent file
        latest_csv = max(csv_files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
        csv_path = os.path.join(output_dir, latest_csv)
        
        print(f"📁 Examining file: {latest_csv}")
        
        # Read and examine the CSV
        df = pd.read_csv(csv_path, nrows=10)
        
        print(f"📊 Sample data loaded: {len(df)} rows")
        
        # Check date columns
        date_columns = ['invoice_date', 'transaction_date']
        
        print(f"\n🔍 Date Format Analysis:")
        print("=" * 40)
        
        for col in date_columns:
            if col in df.columns:
                print(f"\n📅 {col} column:")
                sample_values = df[col].dropna().head(5).tolist()
                print(f"   Sample values: {sample_values}")
                
                # Check format consistency
                if sample_values:
                    all_iso_format = True
                    for val in sample_values:
                        val_str = str(val)
                        if not (len(val_str) == 10 and val_str.count('-') == 2):
                            all_iso_format = False
                            break
                    
                    if all_iso_format:
                        print(f"   ✅ All values are in YYYY-MM-DD format")
                    else:
                        print(f"   ❌ Values are NOT in YYYY-MM-DD format")
            else:
                print(f"❌ Column {col} not found")
        
        # Compare the two date columns if both exist
        if 'invoice_date' in df.columns and 'transaction_date' in df.columns:
            print(f"\n🔄 Cross-Column Format Comparison:")
            print("=" * 40)
            
            consistent = True
            for idx in range(min(5, len(df))):
                inv_date = str(df.iloc[idx]['invoice_date'])
                trans_date = str(df.iloc[idx]['transaction_date'])
                
                inv_iso = len(inv_date) == 10 and inv_date.count('-') == 2
                trans_iso = len(trans_date) == 10 and trans_date.count('-') == 2
                
                status = "✅" if (inv_iso and trans_iso) else "❌"
                print(f"   Row {idx}: {status} invoice_date={inv_date}, transaction_date={trans_date}")
                
                if not (inv_iso and trans_iso):
                    consistent = False
            
            print(f"\n📋 FINAL RESULT:")
            if consistent:
                print("✅ Both invoice_date and transaction_date columns are consistently formatted in YYYY-MM-DD format")
            else:
                print("❌ Date columns have inconsistent formatting - correction needed")
                
                # Identify which column needs correction
                inv_sample = str(df['invoice_date'].dropna().iloc[0]) if len(df['invoice_date'].dropna()) > 0 else ""
                trans_sample = str(df['transaction_date'].dropna().iloc[0]) if len(df['transaction_date'].dropna()) > 0 else ""
                
                inv_iso = len(inv_sample) == 10 and inv_sample.count('-') == 2
                trans_iso = len(trans_sample) == 10 and trans_sample.count('-') == 2
                
                if not inv_iso:
                    print("🔧 invoice_date column needs to be corrected in the pipeline")
                if not trans_iso:
                    print("🔧 transaction_date column needs to be corrected in the pipeline")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = export_and_examine()
    
    if success:
        print("\n✅ Analysis completed successfully!")
    else:
        print("\n❌ Analysis failed!")
