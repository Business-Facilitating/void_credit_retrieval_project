#!/usr/bin/env python3
"""
Run the DLT pipeline with proper environment setup and examine results
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Set environment variables
os.environ["DLT_INVOICE_CUTOFF_DAYS"] = "30"
os.environ["DLT_WRITE_DISPOSITION"] = "replace"
os.environ["DLT_CLICKHOUSE_BATCH_SIZE"] = "5000"  # Smaller batch for testing

# Add src path
sys.path.append('src/src')

def run_pipeline_and_check():
    """Run pipeline and check date formats"""
    print("🚀 Running DLT Pipeline Test")
    print("=" * 40)
    
    try:
        # Import and run pipeline
        from dlt_pipeline_examples import run_carrier_invoice_extraction
        
        print("📥 Starting pipeline extraction...")
        pipeline = run_carrier_invoice_extraction()
        
        if not pipeline:
            print("❌ Pipeline failed")
            return False
        
        print("✅ Pipeline completed successfully")
        
        # Find the newest CSV file
        output_dir = "data/output"
        csv_files = []
        
        for file in os.listdir(output_dir):
            if file.startswith("carrier_invoice_data_30days_") and file.endswith(".csv"):
                csv_files.append(file)
        
        if not csv_files:
            print("❌ No CSV files found")
            return False
        
        # Get the most recent file
        latest_csv = max(csv_files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
        csv_path = os.path.join(output_dir, latest_csv)
        
        print(f"📁 Examining file: {latest_csv}")
        
        # Read and examine the CSV
        df = pd.read_csv(csv_path, nrows=10)  # Just first 10 rows for testing
        
        print(f"📊 Sample data loaded: {len(df)} rows")
        print(f"📋 Columns: {list(df.columns)}")
        
        # Check date columns
        date_columns = ['invoice_date', 'transaction_date']
        
        for col in date_columns:
            if col in df.columns:
                print(f"\n🔍 {col} column:")
                sample_values = df[col].dropna().head(5).tolist()
                print(f"   Sample values: {sample_values}")
                
                # Check format consistency
                if sample_values:
                    formats = set()
                    for val in sample_values:
                        val_str = str(val)
                        if '-' in val_str and len(val_str) == 10:
                            formats.add("YYYY-MM-DD")
                        elif '/' in val_str:
                            formats.add("MM/DD/YYYY or similar")
                        else:
                            formats.add(f"Other: {val_str}")
                    
                    print(f"   📊 Formats detected: {list(formats)}")
                    
                    if len(formats) == 1 and "YYYY-MM-DD" in formats:
                        print(f"   ✅ {col} is properly formatted")
                    else:
                        print(f"   ⚠️ {col} has inconsistent formatting")
            else:
                print(f"❌ Column {col} not found")
        
        # Compare the two date columns if both exist
        if 'invoice_date' in df.columns and 'transaction_date' in df.columns:
            print(f"\n🔄 Comparing date column formats:")
            
            for idx in range(min(5, len(df))):
                inv_date = df.iloc[idx]['invoice_date']
                trans_date = df.iloc[idx]['transaction_date']
                print(f"   Row {idx}: invoice_date={inv_date}, transaction_date={trans_date}")
                
                # Check if formats match
                inv_format = "YYYY-MM-DD" if (str(inv_date).count('-') == 2 and len(str(inv_date)) == 10) else "Other"
                trans_format = "YYYY-MM-DD" if (str(trans_date).count('-') == 2 and len(str(trans_date)) == 10) else "Other"
                
                if inv_format == trans_format == "YYYY-MM-DD":
                    print(f"   ✅ Row {idx}: Both dates properly formatted")
                else:
                    print(f"   ⚠️ Row {idx}: Format mismatch - invoice: {inv_format}, transaction: {trans_format}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_pipeline_and_check()
    
    if success:
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed!")
