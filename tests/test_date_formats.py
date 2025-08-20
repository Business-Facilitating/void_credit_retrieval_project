#!/usr/bin/env python3
"""
Test script to examine date formats in the existing CSV file and run a fresh pipeline extraction
"""

import pandas as pd
import os
from datetime import datetime
import sys

# Add src path for imports
sys.path.append('src/src')

def examine_existing_csv():
    """Examine the existing CSV file for date format consistency"""
    print("🔍 Examining existing CSV file for date formats...")
    
    # Find the most recent CSV file
    output_dir = "data/output"
    csv_files = [f for f in os.listdir(output_dir) if f.startswith("carrier_invoice_data_30days_") and f.endswith(".csv")]
    
    if not csv_files:
        print("❌ No existing CSV files found")
        return None
    
    # Get the most recent file
    latest_csv = max(csv_files, key=lambda x: os.path.getctime(os.path.join(output_dir, x)))
    csv_path = os.path.join(output_dir, latest_csv)
    
    print(f"📁 Examining file: {latest_csv}")
    
    try:
        # Read the CSV file
        df = pd.read_csv(csv_path)
        print(f"📊 Total rows: {len(df):,}")
        
        # Check if date columns exist
        date_columns = ['invoice_date', 'transaction_date']
        existing_date_cols = [col for col in date_columns if col in df.columns]
        
        if not existing_date_cols:
            print("❌ No date columns found in CSV")
            return None
        
        print(f"📅 Found date columns: {existing_date_cols}")
        
        # Examine date formats
        for col in existing_date_cols:
            print(f"\n🔍 Analyzing {col}:")
            
            # Get non-null values
            non_null_dates = df[col].dropna()
            if len(non_null_dates) == 0:
                print(f"   ⚠️ All values are null")
                continue
            
            print(f"   📊 Non-null values: {len(non_null_dates):,}")
            
            # Sample some values
            sample_values = non_null_dates.head(10).tolist()
            print(f"   📝 Sample values: {sample_values}")
            
            # Check format consistency
            formats_found = set()
            for date_val in sample_values:
                if isinstance(date_val, str):
                    if len(date_val) == 10 and date_val.count('-') == 2:
                        formats_found.add("YYYY-MM-DD")
                    elif len(date_val) == 10 and date_val.count('/') == 2:
                        formats_found.add("MM/DD/YYYY or DD/MM/YYYY")
                    else:
                        formats_found.add(f"Other: {date_val}")
            
            print(f"   🎯 Formats detected: {list(formats_found)}")
        
        # Compare formats between columns
        if len(existing_date_cols) >= 2:
            print(f"\n🔄 Comparing date formats between columns...")
            
            # Sample comparison
            sample_df = df[existing_date_cols].head(10)
            print("📋 Sample comparison:")
            for idx, row in sample_df.iterrows():
                print(f"   Row {idx}: ", end="")
                for col in existing_date_cols:
                    print(f"{col}={row[col]} ", end="")
                print()
        
        return df
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return None

def run_fresh_pipeline():
    """Run a fresh pipeline extraction"""
    print("\n🚀 Running fresh pipeline extraction...")
    
    try:
        from dlt_pipeline_examples import run_carrier_invoice_extraction
        
        # Set environment variables for the test
        os.environ["DLT_INVOICE_CUTOFF_DAYS"] = "30"
        os.environ["DLT_WRITE_DISPOSITION"] = "replace"
        os.environ["DLT_CLICKHOUSE_BATCH_SIZE"] = "10000"  # Smaller batch for testing
        
        # Run the pipeline
        pipeline = run_carrier_invoice_extraction()
        
        if pipeline:
            print("✅ Pipeline completed successfully")
            return True
        else:
            print("❌ Pipeline failed")
            return False
            
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🧪 Date Format Consistency Test")
    print("=" * 50)
    
    # Step 1: Examine existing CSV
    print("\n📋 Step 1: Examining existing CSV file")
    existing_df = examine_existing_csv()
    
    # Step 2: Run fresh pipeline
    print("\n📋 Step 2: Running fresh pipeline extraction")
    pipeline_success = run_fresh_pipeline()
    
    if pipeline_success:
        print("\n📋 Step 3: Examining new CSV file")
        new_df = examine_existing_csv()
        
        if new_df is not None:
            print("\n✅ Test completed successfully!")
            print("\n📊 Summary:")
            print(f"   - New data extracted: {len(new_df):,} rows")
            
            # Check for date columns
            date_cols = ['invoice_date', 'transaction_date']
            for col in date_cols:
                if col in new_df.columns:
                    sample_val = new_df[col].dropna().iloc[0] if len(new_df[col].dropna()) > 0 else "N/A"
                    print(f"   - {col} format: {sample_val}")
        else:
            print("❌ Failed to examine new CSV file")
    else:
        print("❌ Pipeline failed - cannot examine new data")

if __name__ == "__main__":
    main()
