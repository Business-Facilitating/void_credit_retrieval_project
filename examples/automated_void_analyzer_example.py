#!/usr/bin/env python3
"""
Example script for using the Automated Void Analyzer

This script demonstrates various ways to use the automated void analyzer
to process existing 17Track JSON files and identify packages needing voiding.

Usage Examples:
1. Analyze a single file:
   python automated_void_analyzer_example.py single --file tracking_results.json

2. Analyze multiple files:
   python automated_void_analyzer_example.py multiple --files file1.json file2.json

3. Analyze entire directory:
   python automated_void_analyzer_example.py directory --path data/output

4. Batch analysis with custom settings:
   python automated_void_analyzer_example.py batch --directory data/output --min-days 10 --max-days 25

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import argparse
import os
import sys
from typing import List, Optional

# Add src to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'src'))

from automated_void_analyzer import (
    VoidAnalyzer,
    analyze_tracking_files,
    analyze_tracking_directory
)


def example_single_file_analysis(file_path: str, min_days: int = 15, max_days: int = 20):
    """
    Example: Analyze a single tracking results file
    
    Args:
        file_path: Path to the JSON file
        min_days: Minimum days since label creation
        max_days: Maximum days since label creation
    """
    print("📄 Single File Analysis Example")
    print("=" * 40)
    print(f"File: {file_path}")
    print(f"Void range: {min_days}-{max_days} days")
    print()
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    # Use the convenience function
    result = analyze_tracking_files(
        file_paths=file_path,
        min_days=min_days,
        max_days=max_days,
        export_csv=True,
        export_json=True
    )
    
    # Display detailed results
    if result["void_candidates"]:
        print("🚨 Detailed Void Candidates:")
        for candidate in result["void_candidates"]:
            print(f"   📦 {candidate['tracking_number']}")
            print(f"      Days old: {candidate['days_since_label_created']}")
            print(f"      Created: {candidate['label_created_date']}")
            print(f"      Status: {candidate['current_status']}")
            print(f"      Reason: {candidate['void_reason']}")
            print()


def example_multiple_files_analysis(file_paths: List[str], min_days: int = 15, max_days: int = 20):
    """
    Example: Analyze multiple tracking results files
    
    Args:
        file_paths: List of paths to JSON files
        min_days: Minimum days since label creation
        max_days: Maximum days since label creation
    """
    print("📄 Multiple Files Analysis Example")
    print("=" * 40)
    print(f"Files: {len(file_paths)} files")
    print(f"Void range: {min_days}-{max_days} days")
    print()
    
    # Filter existing files
    existing_files = [f for f in file_paths if os.path.exists(f)]
    missing_files = [f for f in file_paths if not os.path.exists(f)]
    
    if missing_files:
        print(f"⚠️ Missing files: {missing_files}")
    
    if not existing_files:
        print("❌ No valid files found")
        return
    
    # Analyze files
    result = analyze_tracking_files(
        file_paths=existing_files,
        min_days=min_days,
        max_days=max_days,
        export_csv=True,
        export_json=True
    )
    
    # Show breakdown by source file
    if result["void_candidates"]:
        print("📊 Breakdown by Source File:")
        file_breakdown = {}
        for candidate in result["void_candidates"]:
            source = candidate["source_file"]
            if source not in file_breakdown:
                file_breakdown[source] = []
            file_breakdown[source].append(candidate)
        
        for source_file, candidates in file_breakdown.items():
            print(f"   📄 {source_file}: {len(candidates)} void candidates")
            for candidate in candidates:
                print(f"      • {candidate['tracking_number']} ({candidate['days_since_label_created']} days)")


def example_directory_analysis(directory_path: str, pattern: str = "*tracking*.json", 
                              min_days: int = 15, max_days: int = 20):
    """
    Example: Analyze all tracking files in a directory
    
    Args:
        directory_path: Path to directory containing JSON files
        pattern: File pattern to match
        min_days: Minimum days since label creation
        max_days: Maximum days since label creation
    """
    print("📁 Directory Analysis Example")
    print("=" * 40)
    print(f"Directory: {directory_path}")
    print(f"Pattern: {pattern}")
    print(f"Void range: {min_days}-{max_days} days")
    print()
    
    if not os.path.exists(directory_path):
        print(f"❌ Directory not found: {directory_path}")
        return
    
    # Analyze directory
    result = analyze_tracking_directory(
        directory_path=directory_path,
        file_pattern=pattern,
        min_days=min_days,
        max_days=max_days,
        export_csv=True,
        export_json=True
    )
    
    # Show summary statistics
    summary = result["summary"]
    print("📈 Analysis Summary:")
    print(f"   Files analyzed: {summary['files_analyzed']}")
    print(f"   Total candidates: {summary['total_candidates']}")
    
    if summary["status_breakdown"]:
        print("   Status breakdown:")
        for status, count in summary["status_breakdown"].items():
            print(f"      {status}: {count}")
    
    if summary["days_distribution"]:
        print("   Days distribution:")
        for days, count in summary["days_distribution"].items():
            print(f"      {days} days: {count} packages")


def example_batch_analysis_with_custom_settings():
    """
    Example: Batch analysis with custom settings and detailed reporting
    """
    print("🔄 Batch Analysis Example")
    print("=" * 40)
    
    # Initialize analyzer with custom output directory
    output_dir = "data/void_analysis_results"
    analyzer = VoidAnalyzer(output_dir=output_dir)
    
    # Define multiple analysis scenarios
    scenarios = [
        {"name": "Standard (15-20 days)", "min_days": 15, "max_days": 20},
        {"name": "Extended (10-25 days)", "min_days": 10, "max_days": 25},
        {"name": "Critical (20-30 days)", "min_days": 20, "max_days": 30}
    ]
    
    data_directory = "data/output"
    if not os.path.exists(data_directory):
        print(f"❌ Data directory not found: {data_directory}")
        return
    
    print(f"📁 Analyzing directory: {data_directory}")
    print(f"🎯 Running {len(scenarios)} analysis scenarios")
    print()
    
    all_results = {}
    
    for scenario in scenarios:
        print(f"🔍 Scenario: {scenario['name']}")
        
        # Run analysis
        void_candidates = analyzer.analyze_directory(
            directory_path=data_directory,
            file_pattern="*tracking*.json",
            min_days=scenario["min_days"],
            max_days=scenario["max_days"]
        )
        
        # Export with scenario-specific filename
        if void_candidates:
            scenario_name = scenario["name"].lower().replace(" ", "_").replace("(", "").replace(")", "")
            csv_file = f"void_analysis_{scenario_name}.csv"
            json_file = f"void_analysis_{scenario_name}.json"
            
            analyzer.export_to_csv(void_candidates, csv_file)
            analyzer.export_to_json(void_candidates, json_file)
        
        all_results[scenario["name"]] = void_candidates
        print(f"   Found: {len(void_candidates)} void candidates")
        print()
    
    # Generate comparison report
    print("📊 Scenario Comparison:")
    for scenario_name, candidates in all_results.items():
        print(f"   {scenario_name}: {len(candidates)} candidates")
    
    return all_results


def example_programmatic_usage():
    """
    Example: Using the analyzer programmatically in your own code
    """
    print("💻 Programmatic Usage Example")
    print("=" * 40)
    
    # Example of how to integrate the analyzer into your own application
    try:
        # Initialize analyzer
        analyzer = VoidAnalyzer()
        
        # Find tracking files
        data_dir = "data/output"
        if os.path.exists(data_dir):
            import glob
            tracking_files = glob.glob(os.path.join(data_dir, "*tracking*.json"))
            
            if tracking_files:
                print(f"📄 Found {len(tracking_files)} tracking files")
                
                # Analyze files
                void_candidates = analyzer.analyze_multiple_files(tracking_files)
                
                # Process results in your application
                if void_candidates:
                    print("🚨 Processing void candidates in application:")
                    
                    # Example: Group by days since creation
                    by_days = {}
                    for candidate in void_candidates:
                        days = candidate["days_since_label_created"]
                        if days not in by_days:
                            by_days[days] = []
                        by_days[days].append(candidate["tracking_number"])
                    
                    for days, tracking_numbers in sorted(by_days.items()):
                        print(f"   {days} days old: {len(tracking_numbers)} packages")
                        # Here you could integrate with your void processing system
                        # void_processing_system.queue_for_voiding(tracking_numbers)
                
                else:
                    print("✅ No void candidates found")
            else:
                print("⚠️ No tracking files found")
        else:
            print("⚠️ Data directory not found")
            
    except Exception as e:
        print(f"❌ Error in programmatic usage: {e}")


def main():
    """
    Main function with command line interface
    """
    parser = argparse.ArgumentParser(
        description="Automated Void Analyzer Examples",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Analysis mode")
    
    # Single file analysis
    single_parser = subparsers.add_parser("single", help="Analyze single file")
    single_parser.add_argument("--file", required=True, help="JSON file to analyze")
    single_parser.add_argument("--min-days", type=int, default=15, help="Minimum days")
    single_parser.add_argument("--max-days", type=int, default=20, help="Maximum days")
    
    # Multiple files analysis
    multi_parser = subparsers.add_parser("multiple", help="Analyze multiple files")
    multi_parser.add_argument("--files", nargs="+", required=True, help="JSON files to analyze")
    multi_parser.add_argument("--min-days", type=int, default=15, help="Minimum days")
    multi_parser.add_argument("--max-days", type=int, default=20, help="Maximum days")
    
    # Directory analysis
    dir_parser = subparsers.add_parser("directory", help="Analyze directory")
    dir_parser.add_argument("--path", required=True, help="Directory path")
    dir_parser.add_argument("--pattern", default="*tracking*.json", help="File pattern")
    dir_parser.add_argument("--min-days", type=int, default=15, help="Minimum days")
    dir_parser.add_argument("--max-days", type=int, default=20, help="Maximum days")
    
    # Batch analysis
    batch_parser = subparsers.add_parser("batch", help="Batch analysis with multiple scenarios")
    
    # Programmatic example
    prog_parser = subparsers.add_parser("programmatic", help="Show programmatic usage example")
    
    args = parser.parse_args()
    
    print("🤖 Automated Void Analyzer Examples")
    print("=" * 50)
    
    if args.command == "single":
        example_single_file_analysis(args.file, args.min_days, args.max_days)
    elif args.command == "multiple":
        example_multiple_files_analysis(args.files, args.min_days, args.max_days)
    elif args.command == "directory":
        example_directory_analysis(args.path, args.pattern, args.min_days, args.max_days)
    elif args.command == "batch":
        example_batch_analysis_with_custom_settings()
    elif args.command == "programmatic":
        example_programmatic_usage()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
