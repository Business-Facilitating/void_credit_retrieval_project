#!/usr/bin/env python3
"""
Demo CSV Output for UPS Label-Only Filter
==========================================

This script demonstrates the CSV output format by processing a known tracking number
that has the label-only status.

Usage:
    poetry run python tests/demo_csv_output.py
"""

import sys
import os
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "src"))

from ups_label_only_filter import (
    get_ups_access_token,
    query_ups_tracking,
    check_label_only_status,
    save_results
)
from datetime import datetime

def demo_csv_output():
    """Demonstrate CSV output with a known label-only tracking number"""
    print("📊 Demo: UPS Label-Only Filter CSV Output")
    print("=" * 60)
    
    # Known tracking number with label-only status
    test_tracking_number = "1Z6A2V900332443747"
    
    print(f"🔍 Testing with tracking number: {test_tracking_number}")
    
    # Get UPS access token
    print("🔑 Getting UPS API access token...")
    access_token = get_ups_access_token()
    
    if not access_token:
        print("❌ Failed to get UPS access token")
        return
    
    # Query the tracking number
    print(f"📦 Querying UPS API for {test_tracking_number}...")
    ups_response = query_ups_tracking(test_tracking_number, access_token)
    
    if not ups_response:
        print("❌ Failed to get UPS response")
        return
    
    # Check if it matches our criteria
    is_label_only, reason = check_label_only_status(ups_response)
    
    print(f"🎯 Label-only check: {is_label_only}")
    print(f"📝 Reason: {reason}")
    
    if is_label_only:
        # Create sample results structure
        results = {
            "label_only_tracking_numbers": [
                {
                    "tracking_number": test_tracking_number,
                    "reason": reason,
                    "ups_response": ups_response
                }
            ],
            "excluded_tracking_numbers": [],
            "api_errors": [],
            "total_processed": 1,
            "total_label_only": 1,
            "total_excluded": 0,
            "total_errors": 0
        }
        
        # Save results to demonstrate CSV format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filepath, csv_filepath = save_results(results, f"demo_{timestamp}")
        
        print(f"\n✅ Demo results saved!")
        print(f"📁 CSV file: {csv_filepath}")
        
        # Show CSV content
        print(f"\n📋 CSV Content:")
        with open(csv_filepath, "r") as f:
            content = f.read()
            print(content)
        
        print("🎯 CSV Format Explanation:")
        print("- tracking_number: The UPS tracking number")
        print("- status_description: The exact status description from UPS")
        print("- status_code: The UPS status code (MP for label-only)")
        print("- status_type: The UPS status type (M for label-only)")
        print("- date_processed: When the tracking number was processed")
        
    else:
        print(f"❌ This tracking number doesn't match label-only criteria: {reason}")

if __name__ == "__main__":
    demo_csv_output()
