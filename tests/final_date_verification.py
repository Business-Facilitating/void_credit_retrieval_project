#!/usr/bin/env python3
"""
Final verification of date standardization
"""

import pandas as pd
import os
import re

def final_date_verification():
    """Final verification of date formats in existing CSV"""
    
    print('🔍 Final Date Standardization Verification')
    print('=' * 50)
    
    # Find the latest carrier invoice CSV
    csv_files = [f for f in os.listdir("data/output") if f.endswith('.csv') and 'carrier_invoice' in f]
    
    if not csv_files:
        print("❌ No carrier invoice CSV files found")
        return
    
    latest_csv = sorted(csv_files)[-1]
    csv_path = os.path.join("data/output", latest_csv)
    
    print(f"📄 Analyzing: {latest_csv}")
    
    try:
        # Read a sample of the CSV
        print("📊 Loading CSV sample...")
        df_sample = pd.read_csv(csv_path, nrows=100, low_memory=False)
        print(f"✅ Loaded {len(df_sample):,} sample rows")
        
        # Check for date columns
        date_columns = [col for col in df_sample.columns if 'date' in col.lower()]
        print(f"📅 Date columns found: {date_columns}")
        
        # Focus on invoice_date and transaction_date
        target_columns = ['invoice_date', 'transaction_date']
        
        for date_col in target_columns:
            if date_col in df_sample.columns:
                print(f"\n🔍 Analyzing {date_col}:")
                
                # Get non-null values
                date_values = df_sample[date_col].dropna()
                print(f"   📊 Non-null values in sample: {len(date_values):,}")
                
                if len(date_values) > 0:
                    # Show sample values
                    print(f"   📋 Sample values:")
                    for i, val in enumerate(date_values.head(5)):
                        # Check if format is YYYY-MM-DD
                        is_valid = bool(re.match(r'^\d{4}-\d{2}-\d{2}$', str(val)))
                        status = "✅" if is_valid else "❌"
                        print(f"      {status} {val}")
                    
                    # Check all values in sample
                    valid_pattern = date_values.astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$')
                    valid_count = valid_pattern.sum()
                    total_count = len(date_values)
                    
                    print(f"   📊 Format validation: {valid_count:,}/{total_count:,} in YYYY-MM-DD format")
                    
                    if valid_count == total_count:
                        print(f"   ✅ ALL {date_col} values are properly standardized!")
                    else:
                        print(f"   ⚠️ {total_count - valid_count:,} values not in YYYY-MM-DD format")
                        
                        # Show non-standard values
                        non_standard = date_values[~valid_pattern]
                        if len(non_standard) > 0:
                            print(f"   📋 Non-standard formats:")
                            for val in non_standard.head(3):
                                print(f"      ❌ {val}")
                else:
                    print(f"   ⚠️ No non-null {date_col} values in sample")
            else:
                print(f"\n❌ {date_col} column not found in CSV")
        
        # Summary
        print(f"\n📋 Summary:")
        print(f"   📄 File: {latest_csv}")
        print(f"   📊 Sample size: {len(df_sample):,} rows")
        print(f"   📅 Date columns: {len(date_columns)} found")
        
        # Check if both target columns exist and are standardized
        both_standardized = True
        for col in target_columns:
            if col in df_sample.columns:
                date_values = df_sample[col].dropna()
                if len(date_values) > 0:
                    valid_count = date_values.astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$').sum()
                    if valid_count != len(date_values):
                        both_standardized = False
                        break
            else:
                both_standardized = False
                break
        
        if both_standardized:
            print(f"   ✅ VERIFICATION PASSED: Both invoice_date and transaction_date are standardized!")
        else:
            print(f"   ⚠️ VERIFICATION INCOMPLETE: Some date columns may need standardization")
        
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n✅ Final verification completed!")

if __name__ == "__main__":
    final_date_verification()
