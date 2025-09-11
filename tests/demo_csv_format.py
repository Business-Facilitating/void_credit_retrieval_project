#!/usr/bin/env python3
"""
Demo CSV Format for UPS Label-Only Filter
==========================================

This script demonstrates what the CSV output format looks like when tracking numbers
match the label-only criteria.

Usage:
    poetry run python tests/demo_csv_format.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "src"))

from ups_label_only_filter import save_results

def create_demo_csv():
    """Create a demo CSV file showing the expected format"""
    print("📊 Demo: UPS Label-Only Filter CSV Format")
    print("=" * 60)
    
    # Create mock results with sample data
    mock_results = {
        "label_only_tracking_numbers": [
            {
                "tracking_number": "1Z6A2V900332443747",
                "reason": "Matches label-only criteria exactly",
                "ups_response": {
                    "trackResponse": {
                        "shipment": [{
                            "package": [{
                                "activity": [{
                                    "location": {
                                        "address": {
                                            "countryCode": "US",
                                            "country": "US"
                                        }
                                    },
                                    "status": {
                                        "type": "M",
                                        "description": "Shipper created a label, UPS has not received the package yet. ",
                                        "code": "MP",
                                        "statusCode": "003"
                                    },
                                    "date": "20250905",
                                    "time": "140622",
                                    "gmtDate": "20250905",
                                    "gmtOffset": "-04:00",
                                    "gmtTime": "18:06:22"
                                }]
                            }]
                        }]
                    }
                }
            },
            {
                "tracking_number": "1Z1234567890123456",
                "reason": "Matches label-only criteria exactly",
                "ups_response": {
                    "trackResponse": {
                        "shipment": [{
                            "package": [{
                                "activity": [{
                                    "status": {
                                        "type": "M",
                                        "description": "Shipper created a label, UPS has not received the package yet. ",
                                        "code": "MP",
                                        "statusCode": "003"
                                    }
                                }]
                            }]
                        }]
                    }
                }
            },
            {
                "tracking_number": "1Z9876543210987654",
                "reason": "Matches label-only criteria exactly",
                "ups_response": {
                    "trackResponse": {
                        "shipment": [{
                            "package": [{
                                "activity": [{
                                    "status": {
                                        "type": "M",
                                        "description": "Shipper created a label, UPS has not received the package yet. ",
                                        "code": "MP",
                                        "statusCode": "003"
                                    }
                                }]
                            }]
                        }]
                    }
                }
            }
        ],
        "excluded_tracking_numbers": [],
        "api_errors": [],
        "total_processed": 3,
        "total_label_only": 3,
        "total_excluded": 0,
        "total_errors": 0
    }
    
    # Save the demo results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filepath, csv_filepath = save_results(mock_results, f"demo_{timestamp}")
    
    print(f"✅ Demo CSV file created: {csv_filepath}")
    
    # Display the CSV content
    print(f"\n📋 CSV Content:")
    print("-" * 60)
    with open(csv_filepath, "r") as f:
        content = f.read()
        print(content)
    
    print("-" * 60)
    print("\n🎯 CSV Format Explanation:")
    print("Column 1: tracking_number - The UPS tracking number")
    print("Column 2: status_description - The exact status description from UPS API")
    print("Column 3: status_code - The UPS status code (MP = Manifest Package)")
    print("Column 4: status_type - The UPS status type (M = Manifest)")
    print("Column 5: date_processed - Timestamp when the tracking number was processed")
    
    print(f"\n📁 Files created:")
    print(f"   JSON (detailed): {json_filepath}")
    print(f"   CSV (summary):   {csv_filepath}")
    
    print(f"\n💡 This CSV format provides:")
    print("   ✅ Tracking number for void processing")
    print("   ✅ Exact status description for verification")
    print("   ✅ Status codes for automated processing")
    print("   ✅ Processing timestamp for audit trail")

if __name__ == "__main__":
    create_demo_csv()
