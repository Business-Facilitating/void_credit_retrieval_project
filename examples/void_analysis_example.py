#!/usr/bin/env python3
"""
Example script demonstrating void analysis functionality

This script shows how to use the new void analysis features in tracking_17_demo.py
to identify tracking numbers that need voiding (label created 15-20 days ago).

Usage Examples:
1. Run full tracking pipeline with void analysis:
   python void_analysis_example.py --mode pipeline

2. Analyze existing tracking data:
   python void_analysis_example.py --mode analyze --file data/output/tracking_results.json

3. Test with sample data:
   python void_analysis_example.py --mode test

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import argparse
import os
import sys
from typing import List, Optional

# Add src to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'src'))

from tracking_17_demo import (
    demo_tracking_pipeline,
    analyze_existing_tracking_data_for_voids,
    DEMO_TRACKING_NUMBERS,
    API_TOKEN,
    DEFAULT_CARRIER_CODE
)


def run_pipeline_with_void_analysis(
    tracking_numbers: Optional[List[str]] = None,
    min_days: int = 15,
    max_days: int = 20
):
    """
    Run the complete tracking pipeline with void analysis
    
    Args:
        tracking_numbers: List of tracking numbers to process (uses demo numbers if None)
        min_days: Minimum days since label creation for void candidates
        max_days: Maximum days since label creation for void candidates
    """
    print("🚀 Running Complete Pipeline with Void Analysis")
    print("=" * 60)
    
    if tracking_numbers is None:
        tracking_numbers = DEMO_TRACKING_NUMBERS
        print(f"📦 Using demo tracking numbers: {len(tracking_numbers)} packages")
    else:
        print(f"📦 Processing {len(tracking_numbers)} tracking numbers")
    
    print(f"🔍 Void analysis range: {min_days}-{max_days} days since label creation")
    print("⏳ This will take approximately 5+ minutes due to API processing time...")
    print()
    
    # Run the pipeline
    result = demo_tracking_pipeline(
        tracking_numbers=tracking_numbers,
        api_token=API_TOKEN,
        carrier_code=DEFAULT_CARRIER_CODE,
        export_json=True,
        export_csv=True,
        analyze_void_candidates=True,
        void_min_days=min_days,
        void_max_days=max_days,
    )
    
    if result:
        print("\n🎉 Pipeline completed successfully!")
        print("📄 Files exported:")
        for file_type, file_path in result.items():
            if "void" in file_type:
                print(f"   • {file_type.upper()}: {os.path.basename(file_path)} 🚨")
            else:
                print(f"   • {file_type.upper()}: {os.path.basename(file_path)}")
        
        # Check if void candidates were found
        void_files = [k for k in result.keys() if "void" in k]
        if void_files:
            print("\n🚨 ATTENTION: Void candidates found!")
            print("   Review the void_candidates files for packages that need voiding.")
        else:
            print("\n✅ No packages found that need voiding.")
    else:
        print("\n❌ Pipeline failed or no results")


def analyze_existing_data(
    file_path: str,
    min_days: int = 15,
    max_days: int = 20
):
    """
    Analyze existing tracking data for void candidates
    
    Args:
        file_path: Path to existing tracking results JSON file
        min_days: Minimum days since label creation for void candidates
        max_days: Maximum days since label creation for void candidates
    """
    print("🔍 Analyzing Existing Tracking Data")
    print("=" * 50)
    print(f"📂 File: {file_path}")
    print(f"🔍 Void analysis range: {min_days}-{max_days} days since label creation")
    print()
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    # Analyze the data
    void_candidates = analyze_existing_tracking_data_for_voids(
        file_path,
        min_days=min_days,
        max_days=max_days,
        export_results=True
    )
    
    if void_candidates:
        print(f"\n🚨 Found {len(void_candidates)} packages that need voiding!")
        print("\nVoid Candidates:")
        for candidate in void_candidates:
            print(f"   • {candidate['tracking_number']}: {candidate['days_since_label_created']} days old")
            print(f"     Status: {candidate['current_status']}")
            print(f"     Created: {candidate['label_created_date']}")
            print()
    else:
        print("\n✅ No packages found that need voiding")


def run_test_mode():
    """
    Run test mode with sample data
    """
    print("🧪 Running Test Mode")
    print("=" * 30)
    print("This mode demonstrates void analysis with sample data")
    print("(No API calls will be made)")
    print()
    
    # Import test function
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'tests'))
        from test_void_analysis import test_void_analysis
        
        # Run the test
        void_candidates = test_void_analysis()
        
        if void_candidates:
            print(f"\n✅ Test completed successfully!")
            print(f"   Found {len(void_candidates)} void candidates in test data")
        else:
            print(f"\n⚠️ Test completed but no void candidates found")
            
    except ImportError as e:
        print(f"❌ Could not import test module: {e}")
        print("Make sure test_void_analysis.py exists in the tests directory")


def main():
    """
    Main function with command line argument parsing
    """
    parser = argparse.ArgumentParser(
        description="Void Analysis Example for 17Track Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mode pipeline                    # Run full pipeline with demo data
  %(prog)s --mode analyze --file results.json # Analyze existing data
  %(prog)s --mode test                        # Run test with sample data
  %(prog)s --mode pipeline --min-days 10 --max-days 25  # Custom void range
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["pipeline", "analyze", "test"],
        required=True,
        help="Operation mode: pipeline (full API workflow), analyze (existing data), or test (sample data)"
    )
    
    parser.add_argument(
        "--file",
        help="Path to existing tracking results JSON file (required for analyze mode)"
    )
    
    parser.add_argument(
        "--min-days",
        type=int,
        default=15,
        help="Minimum days since label creation for void candidates (default: 15)"
    )
    
    parser.add_argument(
        "--max-days",
        type=int,
        default=20,
        help="Maximum days since label creation for void candidates (default: 20)"
    )
    
    parser.add_argument(
        "--tracking-numbers",
        nargs="+",
        help="Custom tracking numbers to process (for pipeline mode)"
    )
    
    args = parser.parse_args()
    
    print("🎯 17Track Void Analysis Example")
    print("=" * 40)
    
    if args.mode == "pipeline":
        run_pipeline_with_void_analysis(
            tracking_numbers=args.tracking_numbers,
            min_days=args.min_days,
            max_days=args.max_days
        )
    elif args.mode == "analyze":
        if not args.file:
            print("❌ --file argument is required for analyze mode")
            parser.print_help()
            return
        analyze_existing_data(
            file_path=args.file,
            min_days=args.min_days,
            max_days=args.max_days
        )
    elif args.mode == "test":
        run_test_mode()


if __name__ == "__main__":
    main()
