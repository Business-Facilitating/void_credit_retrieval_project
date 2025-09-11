#!/usr/bin/env python3
"""
Test script for void analysis functionality in tracking_17_demo.py

This script demonstrates how to use the new void analysis features:
1. Analyze existing tracking data for void candidates
2. Test the void detection logic with sample data
3. Export void candidates to CSV and JSON

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add src to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'src'))

from tracking_17_demo import (
    find_label_created_event,
    calculate_days_since_label_created,
    analyze_tracking_for_void_candidates,
    export_void_candidates_to_csv,
    export_void_candidates_to_json,
    analyze_existing_tracking_data_for_voids
)

def create_sample_tracking_data() -> List[Dict[str, Any]]:
    """
    Create sample tracking data for testing void analysis
    
    Returns:
        List of sample tracking result dictionaries
    """
    # Create sample data with different label creation dates
    current_date = datetime.now()
    
    # Package 1: Label created 18 days ago (should be flagged for voiding)
    label_date_18_days = current_date - timedelta(days=18)
    
    # Package 2: Label created 10 days ago (should NOT be flagged)
    label_date_10_days = current_date - timedelta(days=10)
    
    # Package 3: Label created 25 days ago (should NOT be flagged - too old)
    label_date_25_days = current_date - timedelta(days=25)
    
    sample_data = [
        {
            "batch_number": 1,
            "tracking_result": {
                "data": {
                    "accepted": [
                        {
                            "number": "1Z_TEST_VOID_CANDIDATE",
                            "carrier": 100002,
                            "track_info": {
                                "latest_status": {
                                    "status": "InfoReceived",
                                    "sub_status": "InfoReceived"
                                },
                                "tracking": {
                                    "providers": [
                                        {
                                            "events": [
                                                {
                                                    "time_iso": label_date_18_days.isoformat(),
                                                    "stage": "InfoReceived",
                                                    "sub_status": "InfoReceived",
                                                    "description": "Shipper created a label, UPS has not received the package yet."
                                                }
                                            ]
                                        }
                                    ]
                                },
                                "milestone": [
                                    {
                                        "key_stage": "InfoReceived",
                                        "time_iso": label_date_18_days.isoformat()
                                    }
                                ]
                            }
                        },
                        {
                            "number": "1Z_TEST_NOT_VOID_TOO_NEW",
                            "carrier": 100002,
                            "track_info": {
                                "latest_status": {
                                    "status": "InfoReceived",
                                    "sub_status": "InfoReceived"
                                },
                                "tracking": {
                                    "providers": [
                                        {
                                            "events": [
                                                {
                                                    "time_iso": label_date_10_days.isoformat(),
                                                    "stage": "InfoReceived",
                                                    "sub_status": "InfoReceived",
                                                    "description": "Shipper created a label, UPS has not received the package yet."
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        },
                        {
                            "number": "1Z_TEST_NOT_VOID_TOO_OLD",
                            "carrier": 100002,
                            "track_info": {
                                "latest_status": {
                                    "status": "InfoReceived",
                                    "sub_status": "InfoReceived"
                                },
                                "tracking": {
                                    "providers": [
                                        {
                                            "events": [
                                                {
                                                    "time_iso": label_date_25_days.isoformat(),
                                                    "stage": "InfoReceived",
                                                    "sub_status": "InfoReceived",
                                                    "description": "Shipper created a label, UPS has not received the package yet."
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            }
        }
    ]
    
    return sample_data


def test_void_analysis():
    """
    Test the void analysis functionality with sample data
    """
    print("🧪 Testing Void Analysis Functionality")
    print("=" * 50)
    
    # Create sample data
    sample_data = create_sample_tracking_data()
    print(f"📊 Created sample data with {len(sample_data)} batches")
    
    # Test void analysis
    void_candidates = analyze_tracking_for_void_candidates(
        sample_data, 
        min_days=15, 
        max_days=20
    )
    
    print(f"\n🎯 Analysis Results:")
    print(f"   • Found {len(void_candidates)} void candidates")
    
    if void_candidates:
        print(f"\n🚨 Void Candidates:")
        for candidate in void_candidates:
            print(f"   • {candidate['tracking_number']}: {candidate['days_since_label_created']} days old")
            print(f"     Status: {candidate['current_status']}")
            print(f"     Reason: {candidate['void_reason']}")
            print()
    
    # Test export functionality
    if void_candidates:
        print("📄 Testing export functionality...")
        
        # Export to CSV
        csv_path = export_void_candidates_to_csv(void_candidates, "test_void_candidates.csv")
        print(f"   • CSV exported to: {os.path.basename(csv_path)}")
        
        # Export to JSON
        json_path = export_void_candidates_to_json(void_candidates, "test_void_candidates.json")
        print(f"   • JSON exported to: {os.path.basename(json_path)}")
    
    return void_candidates


def test_existing_data_analysis():
    """
    Test analyzing existing tracking data from JSON file
    """
    print("\n🔍 Testing Analysis of Existing Data")
    print("=" * 50)
    
    # Check if we have existing tracking data to analyze
    data_dir = "data/output"
    if os.path.exists(data_dir):
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json') and 'tracking' in f]
        
        if json_files:
            # Use the most recent tracking file
            latest_file = max(json_files, key=lambda f: os.path.getctime(os.path.join(data_dir, f)))
            file_path = os.path.join(data_dir, latest_file)
            
            print(f"📂 Found existing tracking data: {latest_file}")
            
            # Analyze the existing data
            void_candidates = analyze_existing_tracking_data_for_voids(
                file_path,
                min_days=15,
                max_days=20,
                export_results=True
            )
            
            if void_candidates:
                print(f"🚨 Found {len(void_candidates)} void candidates in existing data")
            else:
                print("✅ No void candidates found in existing data")
                
            return void_candidates
        else:
            print("⚠️ No existing tracking JSON files found in data/output")
    else:
        print("⚠️ data/output directory not found")
    
    return None


def main():
    """
    Main test function
    """
    print("🎯 Void Analysis Test Suite")
    print("=" * 60)
    print("This test demonstrates the new void analysis features:")
    print("1. Detect packages with 'label created' status 15-20 days old")
    print("2. Export void candidates to CSV and JSON")
    print("3. Analyze existing tracking data")
    print("=" * 60)
    
    # Test 1: Basic void analysis with sample data
    void_candidates_test = test_void_analysis()
    
    # Test 2: Analyze existing data if available
    void_candidates_existing = test_existing_data_analysis()
    
    print("\n🎉 Test Suite Complete!")
    print(f"   • Sample data test: {len(void_candidates_test) if void_candidates_test else 0} void candidates")
    print(f"   • Existing data test: {len(void_candidates_existing) if void_candidates_existing else 0} void candidates")


if __name__ == "__main__":
    main()
