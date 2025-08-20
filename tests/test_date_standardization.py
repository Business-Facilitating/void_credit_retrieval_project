#!/usr/bin/env python3
"""
Test the date standardization function
"""

import sys
import os
sys.path.append('src/src')

from dlt_pipeline_examples import standardize_date_format

def test_date_standardization():
    """Test the date standardization function with various formats"""
    
    print('🧪 Testing date standardization function...')
    
    # Test cases with different date formats
    test_cases = [
        # Already standardized
        {"invoice_date": "2025-08-18", "transaction_date": "2025-08-17"},
        
        # Different string formats
        {"invoice_date": "08/18/2025", "transaction_date": "08-17-2025"},
        {"invoice_date": "2025/08/18", "transaction_date": "17-08-2025"},
        {"invoice_date": "Aug 18, 2025", "transaction_date": "17 Aug 2025"},
        
        # Edge cases
        {"invoice_date": None, "transaction_date": ""},
        {"invoice_date": "2025-02-29", "transaction_date": "2025-12-31"},  # Invalid leap year
        
        # Mixed types (would come from database)
        {"invoice_date": "2025-08-18", "transaction_date": "2025-08-17"},
    ]
    
    print(f"\n📊 Testing {len(test_cases)} test cases:")
    
    for i, test_record in enumerate(test_cases, 1):
        print(f"\n🔍 Test Case {i}:")
        print(f"   Before: {test_record}")
        
        # Create a copy to avoid modifying original
        record = test_record.copy()
        
        try:
            # Apply standardization
            standardize_date_format(record, "invoice_date")
            standardize_date_format(record, "transaction_date")
            
            print(f"   After:  {record}")
            
            # Validate format
            for date_col in ["invoice_date", "transaction_date"]:
                if record.get(date_col):
                    date_val = record[date_col]
                    if isinstance(date_val, str) and len(date_val) == 10 and date_val[4] == '-' and date_val[7] == '-':
                        print(f"   ✅ {date_col}: Valid YYYY-MM-DD format")
                    else:
                        print(f"   ❌ {date_col}: Invalid format: {date_val}")
                else:
                    print(f"   ℹ️ {date_col}: Empty/None value")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n✅ Date standardization testing completed!")

if __name__ == "__main__":
    test_date_standardization()
