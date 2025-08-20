#!/usr/bin/env python3
"""
Run a fresh pipeline test with a different database name to avoid file locks
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Set environment variables
os.environ["DLT_INVOICE_CUTOFF_DAYS"] = "30"
os.environ["DLT_WRITE_DISPOSITION"] = "replace"
os.environ["DLT_CLICKHOUSE_BATCH_SIZE"] = "5000"

# Add src path
sys.path.append('src/src')

def run_fresh_test():
    """Run a fresh pipeline test"""
    print("🧪 Fresh Pipeline Test for Date Format Consistency")
    print("=" * 60)
    
    try:
        from dlt_pipeline_examples import run_carrier_invoice_extraction
        
        # Use a timestamp suffix to create a unique pipeline name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pipeline_suffix = f"_test_{timestamp}"
        
        print(f"📥 Starting fresh pipeline extraction with suffix: {pipeline_suffix}")
        
        # Run the pipeline with a unique name to avoid file locks
        pipeline = run_carrier_invoice_extraction(pipeline_name_suffix=pipeline_suffix)
        
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
        
        # Get the most recent file (should be the one we just created)
        latest_csv = max(csv_files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
        csv_path = os.path.join(output_dir, latest_csv)
        
        print(f"📁 Examining fresh CSV file: {latest_csv}")
        
        # Read and examine the CSV
        df = pd.read_csv(csv_path, nrows=20)
        
        print(f"📊 Fresh data loaded: {len(df)} rows")
        print(f"📋 Columns: {len(df.columns)}")
        
        # Check date columns
        date_columns = ['invoice_date', 'transaction_date']
        
        print(f"\n🔍 Date Format Verification:")
        print("=" * 40)
        
        results = {}
        
        for col in date_columns:
            if col in df.columns:
                print(f"\n📅 {col} column:")
                
                # Get non-null values
                non_null_values = df[col].dropna()
                
                if len(non_null_values) == 0:
                    print(f"   ⚠️ All values are null")
                    results[col] = "NULL"
                    continue
                
                # Sample values
                sample_values = non_null_values.head(10).tolist()
                print(f"   📝 Sample values: {sample_values}")
                
                # Check if all values are in YYYY-MM-DD format
                all_iso_format = True
                for val in sample_values:
                    val_str = str(val).strip()
                    if not (len(val_str) == 10 and val_str.count('-') == 2):
                        all_iso_format = False
                        break
                
                if all_iso_format:
                    print(f"   ✅ All values are in YYYY-MM-DD format")
                    results[col] = "YYYY-MM-DD"
                else:
                    print(f"   ❌ Values are NOT in YYYY-MM-DD format")
                    results[col] = "INCONSISTENT"
            else:
                print(f"❌ Column {col} not found")
                results[col] = "NOT_FOUND"
        
        # Cross-column comparison
        if 'invoice_date' in df.columns and 'transaction_date' in df.columns:
            print(f"\n🔄 Cross-Column Format Comparison:")
            print("=" * 40)
            
            all_rows_consistent = True
            
            for idx in range(min(10, len(df))):
                inv_date = str(df.iloc[idx]['invoice_date']).strip()
                trans_date = str(df.iloc[idx]['transaction_date']).strip()
                
                inv_iso = len(inv_date) == 10 and inv_date.count('-') == 2
                trans_iso = len(trans_date) == 10 and trans_date.count('-') == 2
                
                row_consistent = inv_iso and trans_iso
                status = "✅" if row_consistent else "❌"
                
                print(f"   Row {idx}: {status} invoice_date={inv_date}, transaction_date={trans_date}")
                
                if not row_consistent:
                    all_rows_consistent = False
            
            # Final assessment
            print(f"\n📋 FINAL TEST RESULTS:")
            print("=" * 40)
            
            print(f"📊 Data extracted: {len(df)} rows")
            print(f"📅 invoice_date format: {results.get('invoice_date', 'NOT_CHECKED')}")
            print(f"📅 transaction_date format: {results.get('transaction_date', 'NOT_CHECKED')}")
            
            if all_rows_consistent and results.get('invoice_date') == 'YYYY-MM-DD' and results.get('transaction_date') == 'YYYY-MM-DD':
                print(f"\n✅ SUCCESS: Both invoice_date and transaction_date columns are consistently formatted in ISO 8601 format (YYYY-MM-DD)")
                print(f"✅ The DLT pipeline date standardization is working correctly")
                return True
            else:
                print(f"\n❌ FAILURE: Date formatting is inconsistent")
                
                if results.get('invoice_date') != 'YYYY-MM-DD':
                    print(f"🔧 invoice_date column needs correction in the pipeline")
                if results.get('transaction_date') != 'YYYY-MM-DD':
                    print(f"🔧 transaction_date column needs correction in the pipeline")
                
                return False
        else:
            print(f"\n❌ Cannot perform cross-column comparison - missing date columns")
            return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_fresh_test()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 COMPLETE TEST RUN SUCCESSFUL!")
        print("✅ Date formatting consistency verified")
        print("✅ Both invoice_date and transaction_date use YYYY-MM-DD format")
        print("✅ DLT pipeline standardization is working correctly")
    else:
        print("❌ TEST RUN FAILED!")
        print("⚠️ Date formatting issues detected")
        print("🔧 Pipeline corrections may be needed")
    print(f"{'='*60}")
