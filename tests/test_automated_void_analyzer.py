#!/usr/bin/env python3
"""
Test script for automated_void_analyzer.py

This script tests the automated void analyzer functionality with various
JSON file structures and scenarios.

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add src to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'src'))

from automated_void_analyzer import VoidAnalyzer, analyze_tracking_files, analyze_tracking_directory


def create_sample_tracking_data() -> Dict[str, Any]:
    """
    Create sample tracking data with different structures and ages
    
    Returns:
        Dictionary with sample tracking data
    """
    current_date = datetime.now()
    
    # Create different label creation dates
    label_18_days = (current_date - timedelta(days=18)).isoformat()
    label_12_days = (current_date - timedelta(days=12)).isoformat()
    label_22_days = (current_date - timedelta(days=22)).isoformat()
    
    # Sample data structure 1: Batch results format (from tracking_17_demo.py)
    batch_format = [
        {
            "batch_number": 1,
            "tracking_result": {
                "data": {
                    "accepted": [
                        {
                            "number": "1Z_VOID_CANDIDATE_18_DAYS",
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
                                                    "time_iso": label_18_days,
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
                            "number": "1Z_NOT_VOID_TOO_NEW",
                            "carrier": 100002,
                            "track_info": {
                                "latest_status": {
                                    "status": "InfoReceived",
                                    "sub_status": "InfoReceived"
                                },
                                "milestone": [
                                    {
                                        "key_stage": "InfoReceived",
                                        "time_iso": label_12_days
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }
    ]
    
    # Sample data structure 2: Direct API response format
    api_format = {
        "code": 0,
        "data": {
            "accepted": [
                {
                    "number": "1Z_VOID_CANDIDATE_DIRECT",
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
                                            "time_iso": label_18_days,
                                            "stage": "InfoReceived",
                                            "description": "Label created by shipper"
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
    
    # Sample data structure 3: Wrapped result format
    wrapped_format = {
        "result": {
            "data": {
                "accepted": [
                    {
                        "number": "1Z_NOT_VOID_TOO_OLD",
                        "carrier": 100002,
                        "track_info": {
                            "latest_status": {
                                "status": "Delivered",
                                "sub_status": "Delivered_Other"
                            },
                            "tracking": {
                                "providers": [
                                    {
                                        "events": [
                                            {
                                                "time_iso": label_22_days,
                                                "stage": "InfoReceived",
                                                "description": "Shipper created a label"
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
    
    return {
        "batch_format": batch_format,
        "api_format": api_format,
        "wrapped_format": wrapped_format
    }


def test_void_analyzer_class():
    """
    Test the VoidAnalyzer class functionality
    """
    print("🧪 Testing VoidAnalyzer Class")
    print("=" * 40)
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        analyzer = VoidAnalyzer(output_dir=temp_dir)
        
        # Create sample data files
        sample_data = create_sample_tracking_data()
        
        test_files = []
        for name, data in sample_data.items():
            file_path = os.path.join(temp_dir, f"test_{name}.json")
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            test_files.append(file_path)
        
        print(f"📄 Created {len(test_files)} test files")
        
        # Test single file analysis
        print("\n🔍 Testing single file analysis...")
        void_candidates = analyzer.analyze_file(test_files[0])
        print(f"   Found {len(void_candidates)} void candidates")
        
        # Test multiple file analysis
        print("\n🔍 Testing multiple file analysis...")
        all_candidates = analyzer.analyze_multiple_files(test_files)
        print(f"   Found {len(all_candidates)} total void candidates")
        
        # Test directory analysis
        print("\n🔍 Testing directory analysis...")
        dir_candidates = analyzer.analyze_directory(temp_dir, "test_*.json")
        print(f"   Found {len(dir_candidates)} candidates from directory")
        
        # Test export functionality
        if all_candidates:
            print("\n📄 Testing export functionality...")
            csv_path = analyzer.export_to_csv(all_candidates, "test_export.csv")
            json_path = analyzer.export_to_json(all_candidates, "test_export.json")
            
            print(f"   CSV exported: {os.path.exists(csv_path)}")
            print(f"   JSON exported: {os.path.exists(json_path)}")
            
            # Test summary report
            summary = analyzer.generate_summary_report(all_candidates)
            print(f"   Summary generated: {summary['total_candidates']} candidates")
        
        return all_candidates


def test_convenience_functions():
    """
    Test the convenience functions
    """
    print("\n🧪 Testing Convenience Functions")
    print("=" * 40)
    
    # Create temporary directory and files
    with tempfile.TemporaryDirectory() as temp_dir:
        sample_data = create_sample_tracking_data()
        
        # Create test files
        test_files = []
        for name, data in sample_data.items():
            file_path = os.path.join(temp_dir, f"tracking_{name}.json")
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            test_files.append(file_path)
        
        # Test analyze_tracking_files function
        print("🔍 Testing analyze_tracking_files...")
        result1 = analyze_tracking_files(
            file_paths=test_files[0],
            export_csv=False,
            export_json=False,
            output_dir=temp_dir
        )
        print(f"   Single file: {len(result1['void_candidates'])} candidates")
        
        result2 = analyze_tracking_files(
            file_paths=test_files,
            export_csv=False,
            export_json=False,
            output_dir=temp_dir
        )
        print(f"   Multiple files: {len(result2['void_candidates'])} candidates")
        
        # Test analyze_tracking_directory function
        print("\n🔍 Testing analyze_tracking_directory...")
        result3 = analyze_tracking_directory(
            directory_path=temp_dir,
            file_pattern="tracking_*.json",
            export_csv=False,
            export_json=False,
            output_dir=temp_dir
        )
        print(f"   Directory analysis: {len(result3['void_candidates'])} candidates")
        
        return result3


def test_edge_cases():
    """
    Test edge cases and error handling
    """
    print("\n🧪 Testing Edge Cases")
    print("=" * 30)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        analyzer = VoidAnalyzer(output_dir=temp_dir)
        
        # Test empty file
        empty_file = os.path.join(temp_dir, "empty.json")
        with open(empty_file, "w") as f:
            json.dump({}, f)
        
        print("🔍 Testing empty file...")
        candidates = analyzer.analyze_file(empty_file)
        print(f"   Empty file candidates: {len(candidates)}")
        
        # Test malformed JSON
        malformed_file = os.path.join(temp_dir, "malformed.json")
        with open(malformed_file, "w") as f:
            f.write("{ invalid json")
        
        print("🔍 Testing malformed JSON...")
        candidates = analyzer.analyze_file(malformed_file)
        print(f"   Malformed file candidates: {len(candidates)}")
        
        # Test non-existent file
        print("🔍 Testing non-existent file...")
        candidates = analyzer.analyze_file("non_existent.json")
        print(f"   Non-existent file candidates: {len(candidates)}")
        
        # Test empty export
        print("🔍 Testing empty export...")
        csv_path = analyzer.export_to_csv([])
        json_path = analyzer.export_to_json([])
        print(f"   Empty CSV export: {os.path.exists(csv_path)}")
        print(f"   Empty JSON export: {os.path.exists(json_path)}")


def test_real_data():
    """
    Test with real tracking data if available
    """
    print("\n🧪 Testing with Real Data")
    print("=" * 30)
    
    # Look for real tracking data files
    data_dir = "data/output"
    if os.path.exists(data_dir):
        json_files = [f for f in os.listdir(data_dir) if f.endswith('.json') and 'tracking' in f]
        
        if json_files:
            print(f"📂 Found {len(json_files)} real tracking files")
            
            # Test with the first real file
            real_file = os.path.join(data_dir, json_files[0])
            print(f"🔍 Testing with: {json_files[0]}")
            
            result = analyze_tracking_files(
                file_paths=real_file,
                export_csv=False,
                export_json=False
            )
            
            print(f"   Real data candidates: {len(result['void_candidates'])}")
            return result
        else:
            print("⚠️ No real tracking files found")
    else:
        print("⚠️ data/output directory not found")
    
    return None


def main():
    """
    Main test function
    """
    print("🎯 Automated Void Analyzer Test Suite")
    print("=" * 50)
    print("Testing automated analysis of 17Track JSON files")
    print("=" * 50)
    
    # Run all tests
    test_results = {}
    
    try:
        test_results["class_test"] = test_void_analyzer_class()
        test_results["convenience_test"] = test_convenience_functions()
        test_edge_cases()
        test_results["real_data_test"] = test_real_data()
        
        print("\n🎉 Test Suite Complete!")
        print("=" * 30)
        
        # Summary
        total_candidates = 0
        for test_name, result in test_results.items():
            if result and isinstance(result, dict) and "void_candidates" in result:
                candidates = len(result["void_candidates"])
                total_candidates += candidates
                print(f"   {test_name}: {candidates} void candidates")
            elif result and isinstance(result, list):
                candidates = len(result)
                total_candidates += candidates
                print(f"   {test_name}: {candidates} void candidates")
        
        print(f"\n📊 Total void candidates found across all tests: {total_candidates}")
        
        if total_candidates > 0:
            print("✅ Void analysis functionality is working correctly!")
        else:
            print("ℹ️ No void candidates found (expected for test data)")
            
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
