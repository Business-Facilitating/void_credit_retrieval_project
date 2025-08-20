#!/usr/bin/env python3
"""
Examine existing data without running the pipeline
"""

import os
import pandas as pd
from datetime import datetime

def examine_csv_files():
    """Examine existing CSV files for date format consistency"""
    print("🔍 Examining existing CSV files for date format consistency")
    print("=" * 60)
    
    output_dir = "data/output"
    
    # Find all carrier invoice CSV files
    csv_files = []
    for file in os.listdir(output_dir):
        if file.startswith("carrier_invoice_data_30days_") and file.endswith(".csv"):
            csv_files.append(file)
    
    if not csv_files:
        print("❌ No carrier invoice CSV files found")
        return
    
    # Sort by modification time (newest first)
    csv_files.sort(key=lambda x: os.path.getmtime(os.path.join(output_dir, x)), reverse=True)
    
    print(f"📁 Found {len(csv_files)} CSV files:")
    for i, file in enumerate(csv_files):
        file_path = os.path.join(output_dir, file)
        mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
        print(f"   {i+1}. {file} (modified: {mod_time})")
    
    # Examine the most recent file
    latest_file = csv_files[0]
    csv_path = os.path.join(output_dir, latest_file)
    
    print(f"\n📊 Examining most recent file: {latest_file}")
    
    try:
        # Read a sample of the data
        df = pd.read_csv(csv_path, nrows=20)
        
        print(f"✅ Loaded {len(df)} sample rows")
        print(f"📋 Total columns: {len(df.columns)}")
        
        # Check for date columns
        date_columns = ['invoice_date', 'transaction_date']
        found_date_columns = [col for col in date_columns if col in df.columns]
        
        if not found_date_columns:
            print("❌ No target date columns found")
            print(f"📋 Available columns: {list(df.columns)}")
            return
        
        print(f"📅 Found date columns: {found_date_columns}")
        
        # Analyze each date column
        for col in found_date_columns:
            print(f"\n🔍 Analyzing {col}:")
            
            # Get non-null values
            non_null_values = df[col].dropna()
            
            if len(non_null_values) == 0:
                print(f"   ⚠️ All values are null")
                continue
            
            print(f"   📊 Non-null values: {len(non_null_values)}")
            
            # Sample values
            sample_values = non_null_values.head(10).tolist()
            print(f"   📝 Sample values: {sample_values}")
            
            # Analyze formats
            formats = {}
            for val in sample_values:
                val_str = str(val).strip()
                
                if val_str == 'nan' or val_str == '':
                    continue
                
                # Check for YYYY-MM-DD format
                if len(val_str) == 10 and val_str.count('-') == 2:
                    parts = val_str.split('-')
                    if len(parts[0]) == 4 and len(parts[1]) == 2 and len(parts[2]) == 2:
                        formats['YYYY-MM-DD'] = formats.get('YYYY-MM-DD', 0) + 1
                    else:
                        formats['Other dash format'] = formats.get('Other dash format', 0) + 1
                
                # Check for MM/DD/YYYY format
                elif len(val_str) == 10 and val_str.count('/') == 2:
                    formats['MM/DD/YYYY or similar'] = formats.get('MM/DD/YYYY or similar', 0) + 1
                
                # Other formats
                else:
                    formats[f'Other ({val_str})'] = formats.get(f'Other ({val_str})', 0) + 1
            
            print(f"   🎯 Format analysis: {formats}")
            
            # Determine if properly formatted
            if len(formats) == 1 and 'YYYY-MM-DD' in formats:
                print(f"   ✅ {col} is consistently formatted as YYYY-MM-DD")
            elif 'YYYY-MM-DD' in formats and len(formats) > 1:
                print(f"   ⚠️ {col} has mixed formats (mostly YYYY-MM-DD)")
            else:
                print(f"   ❌ {col} is not in YYYY-MM-DD format")
        
        # Compare formats between columns if both exist
        if len(found_date_columns) >= 2:
            print(f"\n🔄 Comparing date formats between columns:")
            
            comparison_data = []
            for idx in range(min(10, len(df))):
                row_data = {}
                for col in found_date_columns:
                    val = df.iloc[idx][col]
                    val_str = str(val).strip()
                    
                    if val_str == 'nan' or val_str == '':
                        format_type = 'NULL'
                    elif len(val_str) == 10 and val_str.count('-') == 2:
                        format_type = 'YYYY-MM-DD'
                    elif len(val_str) == 10 and val_str.count('/') == 2:
                        format_type = 'MM/DD/YYYY'
                    else:
                        format_type = 'Other'
                    
                    row_data[col] = {'value': val, 'format': format_type}
                
                comparison_data.append(row_data)
            
            # Display comparison
            for idx, row_data in enumerate(comparison_data):
                print(f"   Row {idx}:")
                for col in found_date_columns:
                    val = row_data[col]['value']
                    fmt = row_data[col]['format']
                    print(f"     {col}: {val} ({fmt})")
                
                # Check consistency
                formats_in_row = [row_data[col]['format'] for col in found_date_columns]
                if len(set(formats_in_row)) == 1:
                    print(f"     ✅ Consistent formatting")
                else:
                    print(f"     ⚠️ Inconsistent formatting: {formats_in_row}")
        
        # Summary
        print(f"\n📋 SUMMARY:")
        print(f"   File: {latest_file}")
        print(f"   Rows examined: {len(df)}")
        
        for col in found_date_columns:
            non_null = df[col].dropna()
            if len(non_null) > 0:
                sample_val = str(non_null.iloc[0]).strip()
                if len(sample_val) == 10 and sample_val.count('-') == 2:
                    print(f"   {col}: ✅ YYYY-MM-DD format")
                else:
                    print(f"   {col}: ❌ Non-standard format ({sample_val})")
            else:
                print(f"   {col}: ⚠️ All null values")
        
        # Check if both columns have consistent formatting
        if len(found_date_columns) >= 2:
            all_consistent = True
            for idx in range(min(5, len(df))):
                formats_in_row = []
                for col in found_date_columns:
                    val = str(df.iloc[idx][col]).strip()
                    if len(val) == 10 and val.count('-') == 2:
                        formats_in_row.append('YYYY-MM-DD')
                    else:
                        formats_in_row.append('Other')
                
                if len(set(formats_in_row)) > 1:
                    all_consistent = False
                    break
            
            if all_consistent:
                print(f"   Cross-column consistency: ✅ Both columns use same format")
            else:
                print(f"   Cross-column consistency: ❌ Columns use different formats")
        
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    examine_csv_files()
