#!/usr/bin/env python3
"""
Simple script to check date formats in existing CSV file
"""

import pandas as pd
import os

def main():
    print("🔍 Checking date formats in existing CSV...")
    
    # Find the existing CSV file
    csv_path = "data/output/carrier_invoice_data_30days_20250811_232301.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ File not found: {csv_path}")
        return
    
    try:
        # Read just the first few rows to check formats
        df = pd.read_csv(csv_path, nrows=20)
        print(f"✅ Loaded {len(df)} sample rows")
        
        # Check columns
        print(f"📊 Columns: {list(df.columns)}")
        
        # Focus on date columns
        date_columns = ['invoice_date', 'transaction_date']
        
        for col in date_columns:
            if col in df.columns:
                print(f"\n🔍 {col} column:")
                sample_values = df[col].dropna().head(10).tolist()
                print(f"   Sample values: {sample_values}")
                
                # Check format
                if sample_values:
                    first_val = str(sample_values[0])
                    if '-' in first_val and len(first_val) == 10:
                        print(f"   ✅ Format appears to be YYYY-MM-DD")
                    elif '/' in first_val:
                        print(f"   ⚠️ Format appears to be MM/DD/YYYY or similar")
                    else:
                        print(f"   ❓ Unknown format: {first_val}")
            else:
                print(f"❌ Column {col} not found")
        
        # Show a few complete rows
        print(f"\n📋 Sample data:")
        relevant_cols = [col for col in date_columns if col in df.columns]
        if relevant_cols:
            print(df[relevant_cols].head().to_string())
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
