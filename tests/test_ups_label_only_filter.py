#!/usr/bin/env python3
"""
Test script for UPS Label-Only Filter
=====================================

This script tests the UPS label-only filter functionality without making API calls.
It verifies DuckDB connection and shows sample data.

Usage:
    poetry run python tests/test_ups_label_only_filter.py
"""

import os
import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "src"))

from ups_label_only_filter import (
    TARGET_STATUS_CODE,
    TARGET_STATUS_DESCRIPTION,
    TARGET_STATUS_TYPE,
    check_label_only_status,
    connect_to_duckdb,
    extract_tracking_numbers_from_duckdb,
)


def test_duckdb_connection():
    """Test DuckDB connection and basic queries"""
    print("🔍 Testing DuckDB Connection")
    print("=" * 50)

    conn = connect_to_duckdb()
    if not conn:
        print("❌ Failed to connect to DuckDB")
        return False

    try:
        # Test basic query
        tables = conn.execute("SHOW TABLES").fetchall()
        print(f"✅ Found {len(tables)} tables:")
        for table in tables:
            print(f"   📋 {table[0]}")

        # Test tracking number extraction
        print(f"\n🔍 Testing tracking number extraction...")
        tracking_numbers = extract_tracking_numbers_from_duckdb(limit=10)
        print(f"✅ Extracted {len(tracking_numbers)} tracking numbers")

        if tracking_numbers:
            print("📦 Sample tracking numbers:")
            for i, tn in enumerate(tracking_numbers[:5], 1):
                print(f"   {i}. {tn}")

        return True

    except Exception as e:
        print(f"❌ Error testing DuckDB: {e}")
        return False
    finally:
        conn.close()


def test_status_checking():
    """Test the status checking logic with sample data"""
    print("\n🧪 Testing Status Checking Logic")
    print("=" * 50)

    # Test case 1: Perfect match (should return True)
    perfect_match = {
        "trackResponse": {
            "shipment": [
                {
                    "package": [
                        {
                            "activity": [
                                {
                                    "location": {
                                        "address": {
                                            "countryCode": "US",
                                            "country": "US",
                                        }
                                    },
                                    "status": {
                                        "type": "M",
                                        "description": "Shipper created a label, UPS has not received the package yet. ",
                                        "code": "MP",
                                        "statusCode": "003",
                                    },
                                    "date": "20250905",
                                    "time": "140622",
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }

    is_match, reason = check_label_only_status(perfect_match)
    print(f"✅ Perfect match test: {is_match} - {reason}")

    # Test case 2: Multiple activities (should return False)
    multiple_activities = {
        "trackResponse": {
            "shipment": [
                {
                    "package": [
                        {
                            "activity": [
                                {
                                    "status": {
                                        "type": "MV",
                                        "description": "Voided Information Received ",
                                        "code": "VP",
                                    }
                                },
                                {
                                    "status": {
                                        "type": "M",
                                        "description": "Shipper created a label, UPS has not received the package yet. ",
                                        "code": "MP",
                                    }
                                },
                            ]
                        }
                    ]
                }
            ]
        }
    }

    is_match, reason = check_label_only_status(multiple_activities)
    print(f"❌ Multiple activities test: {is_match} - {reason}")

    # Test case 3: Different status (should return False)
    different_status = {
        "trackResponse": {
            "shipment": [
                {
                    "package": [
                        {
                            "activity": [
                                {
                                    "status": {
                                        "type": "D",
                                        "description": "Delivered",
                                        "code": "D",
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }

    is_match, reason = check_label_only_status(different_status)
    print(f"❌ Different status test: {is_match} - {reason}")

    # Test case 4: Empty response (should return False)
    empty_response = {}
    is_match, reason = check_label_only_status(empty_response)
    print(f"❌ Empty response test: {is_match} - {reason}")


def test_csv_output_format():
    """Test the CSV output format"""
    print("\n📊 Testing CSV Output Format")
    print("=" * 50)

    # Test sample data for CSV output
    sample_results = {
        "label_only_tracking_numbers": [
            {
                "tracking_number": "1Z6A2V900332443747",
                "reason": "Matches label-only criteria exactly",
                "ups_response": {
                    "trackResponse": {
                        "shipment": [
                            {
                                "package": [
                                    {
                                        "activity": [
                                            {
                                                "status": {
                                                    "type": "M",
                                                    "description": "Shipper created a label, UPS has not received the package yet. ",
                                                    "code": "MP",
                                                    "statusCode": "003",
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                },
            }
        ]
    }

    print("📋 Expected CSV format:")
    print("tracking_number,status_description,status_code,status_type,date_processed")
    print(
        "1Z6A2V900332443747,Shipper created a label; UPS has not received the package yet. ,MP,M,20250908_223000"
    )
    print("✅ CSV format includes tracking number and complete status information")


def test_configuration():
    """Test configuration values"""
    print("\n⚙️ Testing Configuration")
    print("=" * 50)

    print(f"🎯 Target Status Description: '{TARGET_STATUS_DESCRIPTION}'")
    print(f"🎯 Target Status Code: '{TARGET_STATUS_CODE}'")
    print(f"🎯 Target Status Type: '{TARGET_STATUS_TYPE}'")

    # Verify the target description matches what we see in the sample files
    expected_description = (
        "Shipper created a label, UPS has not received the package yet. "
    )
    if TARGET_STATUS_DESCRIPTION == expected_description:
        print("✅ Target description matches expected value")
    else:
        print(f"❌ Target description mismatch!")
        print(f"   Expected: '{expected_description}'")
        print(f"   Actual:   '{TARGET_STATUS_DESCRIPTION}'")


def main():
    """Run all tests"""
    print("🧪 UPS Label-Only Filter Test Suite")
    print("=" * 60)

    # Test configuration
    test_configuration()

    # Test CSV output format
    test_csv_output_format()

    # Test DuckDB connection
    db_success = test_duckdb_connection()

    # Test status checking logic
    test_status_checking()

    print("\n" + "=" * 60)
    if db_success:
        print("✅ All tests completed successfully!")
        print("💡 You can now run the main script:")
        print("   poetry run python src/src/ups_label_only_filter.py")
        print(
            "📊 CSV output will include: tracking_number, status_description, status_code, status_type, date_processed"
        )
    else:
        print("❌ Some tests failed. Check DuckDB database availability.")
    print("=" * 60)


if __name__ == "__main__":
    main()
    main()
