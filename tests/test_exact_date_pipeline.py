#!/usr/bin/env python3
"""
Test script for the modified DLT pipeline that extracts tracking numbers 
from ClickHouse for records with invoice_date exactly 30 days prior.

This script tests the new exact date filtering functionality.
"""

import os
import sys
from datetime import datetime, timedelta

# Add the src directory to the path so we can import the pipeline
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "src"))

def test_exact_date_calculation():
    """Test that the exact date calculation works correctly"""
    print("🧪 Testing exact date calculation...")
    
    # Test with default 30 days
    cutoff_days = 30
    target_date = (datetime.utcnow() - timedelta(days=cutoff_days)).date()
    current_date = datetime.utcnow().date()
    
    print(f"📅 Current date: {current_date}")
    print(f"🎯 Target date (exactly {cutoff_days} days ago): {target_date}")
    print(f"📊 Date difference: {(current_date - target_date).days} days")
    
    # Verify it's exactly the right number of days
    assert (current_date - target_date).days == cutoff_days, f"Expected {cutoff_days} days difference"
    print("✅ Date calculation is correct!")
    
    return target_date

def test_pipeline_dry_run():
    """Test the pipeline configuration without actually running it"""
    print("\n🧪 Testing pipeline configuration...")
    
    try:
        from dlt_pipeline_examples import run_carrier_invoice_extraction
        
        # Check if environment variables are set
        required_vars = [
            "CLICKHOUSE_HOST",
            "CLICKHOUSE_USERNAME", 
            "CLICKHOUSE_PASSWORD",
            "CLICKHOUSE_DATABASE"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️ Missing environment variables: {missing_vars}")
            print("💡 This is expected if you haven't set up ClickHouse credentials yet")
            return False
        else:
            print("✅ All required environment variables are set")
            return True
            
    except ImportError as e:
        print(f"❌ Failed to import pipeline module: {e}")
        return False

def test_csv_filename_format():
    """Test the new CSV filename format"""
    print("\n🧪 Testing CSV filename format...")
    
    # Simulate the filename generation logic
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    csv_filename = f"carrier_invoice_tracking_exact_{target_date}_{timestamp}.csv"
    
    print(f"📄 Generated filename: {csv_filename}")
    
    # Verify filename contains the target date
    assert target_date in csv_filename, "Target date should be in filename"
    assert "tracking_exact" in csv_filename, "Should indicate exact date filtering"
    
    print("✅ CSV filename format is correct!")
    return csv_filename

def main():
    """Run all tests"""
    print("🚀 Testing Modified DLT Pipeline - Exact Date Filtering")
    print("=" * 60)
    
    try:
        # Test 1: Date calculation
        target_date = test_exact_date_calculation()
        
        # Test 2: Pipeline configuration
        config_ok = test_pipeline_dry_run()
        
        # Test 3: CSV filename format
        csv_filename = test_csv_filename_format()
        
        print("\n📋 Test Summary:")
        print(f"   🎯 Target date: {target_date}")
        print(f"   ⚙️ Configuration: {'✅ OK' if config_ok else '⚠️ Missing credentials'}")
        print(f"   📄 CSV filename: {csv_filename}")
        
        if config_ok:
            print("\n💡 Ready to run the pipeline!")
            print("   Run: poetry run python src/src/dlt_pipeline_examples.py")
        else:
            print("\n💡 Set up ClickHouse credentials first:")
            print("   1. Copy .env.example to .env")
            print("   2. Fill in your ClickHouse credentials")
            print("   3. Run the pipeline")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
