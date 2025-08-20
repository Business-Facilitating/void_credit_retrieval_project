#!/usr/bin/env python3
"""
Examine transaction_date formats in CSV files
"""

import pandas as pd
import os
from collections import Counter

def examine_transaction_dates():
    """Examine transaction_date formats in CSV files"""
    
    print('🔍 Examining transaction_date formats...')
    
    # Find carrier invoice CSV files
    csv_files = [f for f in os.listdir("data/output") if f.endswith('.csv') and 'carrier_invoice' in f]
    
    if not csv_files:
        print("❌ No carrier invoice CSV files found")
        return
    
    # Check the most recent CSV
    latest_csv = sorted(csv_files)[-1]
    csv_path = os.path.join("data/output", latest_csv)
    print(f"📄 Examining: {latest_csv}")
    
    try:
        # Read the CSV file
        print("📊 Loading CSV file...")
        df = pd.read_csv(csv_path)
        print(f"✅ Loaded {len(df):,} rows with {len(df.columns)} columns")
        
        # Check transaction_date column
        if 'transaction_date' not in df.columns:
            print("❌ transaction_date column not found")
            print(f"Available columns: {list(df.columns)}")
            return
        
        print(f"\n📅 Analyzing transaction_date column...")
        
        # Get non-null transaction_date values
        transaction_dates = df['transaction_date'].dropna()
        print(f"📊 Non-null transaction_date values: {len(transaction_dates):,}")
        
        if len(transaction_dates) == 0:
            print("❌ No non-null transaction_date values found")
            return
        
        # Sample values
        print(f"\n📋 Sample transaction_date values:")
        sample_values = transaction_dates.head(10).tolist()
        for i, val in enumerate(sample_values, 1):
            print(f"   {i:2d}. {val} (type: {type(val).__name__})")
        
        # Check for different formats
        print(f"\n🔍 Analyzing date formats...")
        
        # Convert to string and analyze patterns
        date_strings = transaction_dates.astype(str)
        
        # Count different patterns
        patterns = Counter()
        for date_str in date_strings.head(1000):  # Sample first 1000
            if '-' in date_str:
                parts = date_str.split('-')
                if len(parts) == 3:
                    if len(parts[0]) == 4:
                        patterns['YYYY-MM-DD'] += 1
                    elif len(parts[2]) == 4:
                        patterns['MM-DD-YYYY'] += 1
                    else:
                        patterns['Other dash format'] += 1
            elif '/' in date_str:
                parts = date_str.split('/')
                if len(parts) == 3:
                    if len(parts[2]) == 4:
                        patterns['MM/DD/YYYY'] += 1
                    elif len(parts[0]) == 4:
                        patterns['YYYY/MM/DD'] += 1
                    else:
                        patterns['Other slash format'] += 1
            else:
                patterns['Other format'] += 1
        
        print(f"📊 Date format patterns found:")
        for pattern, count in patterns.most_common():
            print(f"   {pattern}: {count:,} occurrences")
        
        # Compare with invoice_date format
        if 'invoice_date' in df.columns:
            print(f"\n📅 Comparing with invoice_date format...")
            invoice_dates = df['invoice_date'].dropna()
            if len(invoice_dates) > 0:
                print(f"📋 Sample invoice_date values:")
                sample_invoice = invoice_dates.head(5).tolist()
                for i, val in enumerate(sample_invoice, 1):
                    print(f"   {i}. {val}")
        
        # Check for any inconsistencies
        print(f"\n🔍 Checking for format consistency...")
        
        # Check if all dates follow YYYY-MM-DD pattern
        consistent_format = True
        inconsistent_examples = []
        
        for date_str in date_strings.head(100):  # Check first 100
            if not (len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-'):
                consistent_format = False
                inconsistent_examples.append(date_str)
                if len(inconsistent_examples) >= 5:
                    break
        
        if consistent_format:
            print("✅ All sampled transaction_date values follow YYYY-MM-DD format")
        else:
            print("❌ Found inconsistent transaction_date formats:")
            for example in inconsistent_examples:
                print(f"   {example}")
        
    except Exception as e:
        print(f"❌ Error examining CSV: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    examine_transaction_dates()
