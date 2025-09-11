#!/usr/bin/env python3
"""
Automated Void Analyzer for 17Track Results

This module provides automated analysis of existing 17Track JSON output files
to identify packages with "label created" status that need voiding (15-20 days old).

Features:
- Reads JSON files from tracking_17_demo.py or tracking_17.py
- Identifies packages with label created 15-20 days ago
- Handles multiple JSON file structures
- Exports results to CSV and JSON formats
- Robust error handling for malformed data

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import glob
import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from dateutil import parser

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Default output directory
DEFAULT_OUTPUT_DIR = "data/output"


class VoidAnalyzer:
    """
    Automated analyzer for identifying packages that need voiding from 17Track results
    """

    def __init__(self, output_dir: str = DEFAULT_OUTPUT_DIR):
        """
        Initialize the void analyzer

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def find_label_created_event(
        self, track_info: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the "label created" event from tracking information

        Args:
            track_info: Track info dictionary from 17Track API response

        Returns:
            Label created event dictionary if found, None otherwise
        """
        try:
            # Method 1: Check tracking providers for events
            tracking = track_info.get("tracking", {})
            providers = tracking.get("providers", [])

            for provider in providers:
                events = provider.get("events", [])

                # Look for InfoReceived stage or label creation descriptions
                for event in events:
                    stage = event.get("stage", "")
                    sub_status = event.get("sub_status", "")
                    description = event.get("description", "").lower()

                    # Check for label created indicators
                    if (
                        stage == "InfoReceived"
                        or sub_status == "InfoReceived"
                        or "label" in description
                        or "shipper created" in description
                    ):
                        return event

            # Method 2: Check milestone data for InfoReceived
            milestone = track_info.get("milestone", [])
            for milestone_event in milestone:
                if milestone_event.get("key_stage") == "InfoReceived":
                    time_iso = milestone_event.get("time_iso")
                    if time_iso:
                        return {
                            "time_iso": time_iso,
                            "stage": "InfoReceived",
                            "description": "Label created (from milestone)",
                            "sub_status": "InfoReceived",
                        }

        except Exception as e:
            logger.debug(f"Error finding label created event: {e}")

        return None

    def calculate_days_since_label_created(
        self, label_event: Dict[str, Any]
    ) -> Optional[int]:
        """
        Calculate the number of days since the label was created

        Args:
            label_event: Label created event dictionary

        Returns:
            Number of days since label creation, None if unable to calculate
        """
        try:
            time_iso = label_event.get("time_iso")
            if not time_iso:
                return None

            # Parse the ISO timestamp with timezone support
            label_date = parser.parse(time_iso)
            current_date = datetime.now(label_date.tzinfo)  # Use same timezone

            # Calculate difference in days
            days_diff = (current_date - label_date).days
            return days_diff

        except Exception as e:
            logger.debug(f"Error calculating days since label created: {e}")
            return None

    def extract_tracking_items(self, data: Union[Dict, List]) -> List[Dict[str, Any]]:
        """
        Extract tracking items from various JSON file structures

        Args:
            data: JSON data from tracking files

        Returns:
            List of tracking items with normalized structure
        """
        tracking_items = []

        try:
            # Handle different JSON structures
            if isinstance(data, list):
                # List of batch results
                for batch_item in data:
                    if isinstance(batch_item, dict):
                        # Extract from batch structure
                        tracking_result = (
                            batch_item.get("tracking_result")
                            or batch_item.get("result")
                            or batch_item
                        )

                        if tracking_result and isinstance(tracking_result, dict):
                            api_data = tracking_result.get("data", {})
                            accepted_items = api_data.get("accepted", [])

                            for item in accepted_items:
                                if item and isinstance(item, dict):
                                    tracking_items.append(
                                        {
                                            "item": item,
                                            "batch_number": batch_item.get(
                                                "batch_number", "unknown"
                                            ),
                                        }
                                    )

            elif isinstance(data, dict):
                # Single result structure
                if "data" in data and "accepted" in data["data"]:
                    # Direct 17Track API response
                    accepted_items = data["data"]["accepted"]
                    for item in accepted_items:
                        if item and isinstance(item, dict):
                            tracking_items.append(
                                {"item": item, "batch_number": "single"}
                            )
                elif "tracking_result" in data or "result" in data:
                    # Wrapped result
                    tracking_result = data.get("tracking_result") or data.get("result")
                    if tracking_result and "data" in tracking_result:
                        accepted_items = tracking_result["data"].get("accepted", [])
                        for item in accepted_items:
                            if item and isinstance(item, dict):
                                tracking_items.append(
                                    {
                                        "item": item,
                                        "batch_number": data.get(
                                            "batch_number", "single"
                                        ),
                                    }
                                )
                else:
                    # Try to find tracking items in any nested structure
                    self._extract_nested_items(data, tracking_items)

        except Exception as e:
            logger.warning(f"Error extracting tracking items: {e}")

        return tracking_items

    def _extract_nested_items(
        self, data: Dict, tracking_items: List, batch_num: str = "nested"
    ) -> None:
        """
        Recursively extract tracking items from nested structures

        Args:
            data: Dictionary to search
            tracking_items: List to append found items to
            batch_num: Batch number identifier
        """
        try:
            if isinstance(data, dict):
                # Look for accepted items
                if "accepted" in data and isinstance(data["accepted"], list):
                    for item in data["accepted"]:
                        if item and isinstance(item, dict) and "track_info" in item:
                            tracking_items.append(
                                {"item": item, "batch_number": batch_num}
                            )

                # Recursively search nested dictionaries
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        if isinstance(value, dict):
                            self._extract_nested_items(value, tracking_items, batch_num)
                        elif isinstance(value, list):
                            for i, list_item in enumerate(value):
                                if isinstance(list_item, dict):
                                    self._extract_nested_items(
                                        list_item, tracking_items, f"{batch_num}_{i}"
                                    )

        except Exception as e:
            logger.debug(f"Error in nested extraction: {e}")

    def analyze_file(
        self, file_path: str, min_days: int = 15, max_days: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Analyze a single JSON file for void candidates

        Args:
            file_path: Path to JSON file
            min_days: Minimum days since label creation
            max_days: Maximum days since label creation

        Returns:
            List of void candidates
        """
        logger.info(f"📂 Analyzing file: {os.path.basename(file_path)}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

        except Exception as e:
            logger.error(f"❌ Error reading file {file_path}: {e}")
            return []

        # Extract tracking items
        tracking_items = self.extract_tracking_items(data)
        logger.info(f"📊 Found {len(tracking_items)} tracking items")

        void_candidates = []

        for tracking_item in tracking_items:
            item = tracking_item["item"]
            batch_number = tracking_item["batch_number"]

            tracking_number = item.get("number")
            track_info = item.get("track_info", {})

            if not tracking_number or not track_info:
                continue

            # Find label created event
            label_event = self.find_label_created_event(track_info)

            if not label_event:
                logger.debug(f"📋 No label created event found for {tracking_number}")
                continue

            # Calculate days since label creation
            days_since_label = self.calculate_days_since_label_created(label_event)

            if days_since_label is None:
                logger.debug(f"⚠️ Could not calculate days for {tracking_number}")
                continue

            # Check if it falls within the void candidate range
            if min_days <= days_since_label <= max_days:
                # Get current status for context
                latest_status = track_info.get("latest_status", {})
                current_status = latest_status.get("status", "unknown")
                current_sub_status = latest_status.get("sub_status", "unknown")

                void_candidate = {
                    "tracking_number": tracking_number,
                    "source_file": os.path.basename(file_path),
                    "batch_number": batch_number,
                    "days_since_label_created": days_since_label,
                    "label_created_date": label_event.get("time_iso"),
                    "label_event_description": label_event.get("description", ""),
                    "current_status": current_status,
                    "current_sub_status": current_sub_status,
                    "void_reason": f"Label created {days_since_label} days ago",
                    "analysis_timestamp": datetime.now().isoformat(),
                    "needs_void": True,
                }

                void_candidates.append(void_candidate)

                logger.info(
                    f"🚨 VOID CANDIDATE: {tracking_number} - "
                    f"Label created {days_since_label} days ago "
                    f"(Status: {current_status})"
                )

        return void_candidates

    def analyze_multiple_files(
        self, file_paths: List[str], min_days: int = 15, max_days: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple JSON files for void candidates

        Args:
            file_paths: List of paths to JSON files
            min_days: Minimum days since label creation
            max_days: Maximum days since label creation

        Returns:
            Combined list of void candidates from all files
        """
        logger.info(f"🔍 Analyzing {len(file_paths)} files for void candidates")
        logger.info(f"📅 Date range: {min_days}-{max_days} days since label creation")

        all_void_candidates = []

        for file_path in file_paths:
            if os.path.exists(file_path):
                candidates = self.analyze_file(file_path, min_days, max_days)
                all_void_candidates.extend(candidates)
            else:
                logger.warning(f"⚠️ File not found: {file_path}")

        logger.info(f"🎯 Total void candidates found: {len(all_void_candidates)}")
        return all_void_candidates

    def analyze_directory(
        self,
        directory_path: str,
        file_pattern: str = "*tracking*.json",
        min_days: int = 15,
        max_days: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Analyze all matching JSON files in a directory

        Args:
            directory_path: Path to directory containing JSON files
            file_pattern: Glob pattern for matching files
            min_days: Minimum days since label creation
            max_days: Maximum days since label creation

        Returns:
            Combined list of void candidates from all matching files
        """
        logger.info(f"📁 Scanning directory: {directory_path}")
        logger.info(f"🔍 File pattern: {file_pattern}")

        # Find matching files
        search_pattern = os.path.join(directory_path, file_pattern)
        file_paths = glob.glob(search_pattern)

        if not file_paths:
            logger.warning(f"⚠️ No files found matching pattern: {search_pattern}")
            return []

        logger.info(f"📄 Found {len(file_paths)} matching files")

        return self.analyze_multiple_files(file_paths, min_days, max_days)

    def export_to_csv(
        self, void_candidates: List[Dict[str, Any]], filename: Optional[str] = None
    ) -> str:
        """
        Export void candidates to CSV file

        Args:
            void_candidates: List of void candidate dictionaries
            filename: Optional custom filename

        Returns:
            Path to exported CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"automated_void_analysis_{timestamp}.csv"

        csv_path = os.path.join(self.output_dir, filename)

        if not void_candidates:
            # Create empty CSV with headers
            empty_df = pd.DataFrame(
                columns=[
                    "tracking_number",
                    "source_file",
                    "batch_number",
                    "days_since_label_created",
                    "label_created_date",
                    "label_event_description",
                    "current_status",
                    "current_sub_status",
                    "void_reason",
                    "analysis_timestamp",
                    "needs_void",
                ]
            )
            empty_df.to_csv(csv_path, index=False, encoding="utf-8")
            logger.info(f"📊 Exported empty CSV to {csv_path}")
            return csv_path

        # Create DataFrame and export
        df = pd.DataFrame(void_candidates)
        df.to_csv(csv_path, index=False, encoding="utf-8")

        logger.info(f"📊 Exported {len(df)} void candidates to {csv_path}")
        return csv_path

    def export_to_json(
        self, void_candidates: List[Dict[str, Any]], filename: Optional[str] = None
    ) -> str:
        """
        Export void candidates to JSON file

        Args:
            void_candidates: List of void candidate dictionaries
            filename: Optional custom filename

        Returns:
            Path to exported JSON file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"automated_void_analysis_{timestamp}.json"

        json_path = os.path.join(self.output_dir, filename)

        # Add metadata
        export_data = {
            "analysis_metadata": {
                "total_candidates": len(void_candidates),
                "analysis_timestamp": datetime.now().isoformat(),
                "analyzer_version": "1.0.0",
            },
            "void_candidates": void_candidates,
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 Exported void candidates to {json_path}")
        return json_path

    def generate_summary_report(
        self, void_candidates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a summary report of void candidates

        Args:
            void_candidates: List of void candidate dictionaries

        Returns:
            Summary report dictionary
        """
        if not void_candidates:
            return {
                "total_candidates": 0,
                "files_analyzed": 0,
                "status_breakdown": {},
                "days_distribution": {},
                "analysis_timestamp": datetime.now().isoformat(),
            }

        # Calculate summary statistics
        source_files = set(candidate["source_file"] for candidate in void_candidates)

        # Status breakdown
        status_breakdown = {}
        for candidate in void_candidates:
            status = candidate["current_status"]
            status_breakdown[status] = status_breakdown.get(status, 0) + 1

        # Days distribution
        days_distribution = {}
        for candidate in void_candidates:
            days = candidate["days_since_label_created"]
            days_distribution[days] = days_distribution.get(days, 0) + 1

        summary = {
            "total_candidates": len(void_candidates),
            "files_analyzed": len(source_files),
            "source_files": list(source_files),
            "status_breakdown": status_breakdown,
            "days_distribution": dict(sorted(days_distribution.items())),
            "analysis_timestamp": datetime.now().isoformat(),
            "oldest_label": max(
                candidate["days_since_label_created"] for candidate in void_candidates
            ),
            "newest_label": min(
                candidate["days_since_label_created"] for candidate in void_candidates
            ),
        }

        return summary


# Convenience functions for easy usage
def analyze_tracking_files(
    file_paths: Union[str, List[str]],
    min_days: int = 15,
    max_days: int = 20,
    export_csv: bool = True,
    export_json: bool = True,
    output_dir: str = DEFAULT_OUTPUT_DIR,
) -> Dict[str, Any]:
    """
    Convenience function to analyze tracking files and export results

    Args:
        file_paths: Single file path or list of file paths to analyze
        min_days: Minimum days since label creation for void candidates
        max_days: Maximum days since label creation for void candidates
        export_csv: Whether to export results to CSV
        export_json: Whether to export results to JSON
        output_dir: Directory for output files

    Returns:
        Dictionary containing void candidates, summary, and export paths
    """
    analyzer = VoidAnalyzer(output_dir)

    # Handle single file or list of files
    if isinstance(file_paths, str):
        file_paths = [file_paths]

    # Analyze files
    void_candidates = analyzer.analyze_multiple_files(file_paths, min_days, max_days)

    # Generate summary
    summary = analyzer.generate_summary_report(void_candidates)

    # Export results
    export_paths = {}
    if export_csv:
        csv_path = analyzer.export_to_csv(void_candidates)
        export_paths["csv"] = csv_path

    if export_json:
        json_path = analyzer.export_to_json(void_candidates)
        export_paths["json"] = json_path

    # Print summary
    print(f"\n🎯 Void Analysis Complete!")
    print(f"📊 Total void candidates: {summary['total_candidates']}")
    print(f"📁 Files analyzed: {summary['files_analyzed']}")

    if void_candidates:
        print(f"\n🚨 Void Candidates Found:")
        for candidate in void_candidates:
            print(
                f"   • {candidate['tracking_number']}: {candidate['days_since_label_created']} days old"
            )

        print(f"\n📄 Export files:")
        for file_type, path in export_paths.items():
            print(f"   • {file_type.upper()}: {os.path.basename(path)}")
    else:
        print(f"✅ No void candidates found")

    return {
        "void_candidates": void_candidates,
        "summary": summary,
        "export_paths": export_paths,
    }


def analyze_tracking_directory(
    directory_path: str,
    file_pattern: str = "*tracking*.json",
    min_days: int = 15,
    max_days: int = 20,
    export_csv: bool = True,
    export_json: bool = True,
    output_dir: str = DEFAULT_OUTPUT_DIR,
) -> Dict[str, Any]:
    """
    Convenience function to analyze all tracking files in a directory

    Args:
        directory_path: Path to directory containing JSON files
        file_pattern: Glob pattern for matching files (default: "*tracking*.json")
        min_days: Minimum days since label creation for void candidates
        max_days: Maximum days since label creation for void candidates
        export_csv: Whether to export results to CSV
        export_json: Whether to export results to JSON
        output_dir: Directory for output files

    Returns:
        Dictionary containing void candidates, summary, and export paths
    """
    analyzer = VoidAnalyzer(output_dir)

    # Analyze directory
    void_candidates = analyzer.analyze_directory(
        directory_path, file_pattern, min_days, max_days
    )

    # Generate summary
    summary = analyzer.generate_summary_report(void_candidates)

    # Export results
    export_paths = {}
    if export_csv:
        csv_path = analyzer.export_to_csv(void_candidates)
        export_paths["csv"] = csv_path

    if export_json:
        json_path = analyzer.export_to_json(void_candidates)
        export_paths["json"] = json_path

    # Print summary
    print(f"\n🎯 Directory Analysis Complete!")
    print(f"📁 Directory: {directory_path}")
    print(f"🔍 Pattern: {file_pattern}")
    print(f"📊 Total void candidates: {summary['total_candidates']}")
    print(f"📄 Files analyzed: {summary['files_analyzed']}")

    if void_candidates:
        print(f"\n🚨 Void Candidates Found:")
        for candidate in void_candidates:
            print(
                f"   • {candidate['tracking_number']}: {candidate['days_since_label_created']} days old ({candidate['source_file']})"
            )

        print(f"\n📄 Export files:")
        for file_type, path in export_paths.items():
            print(f"   • {file_type.upper()}: {os.path.basename(path)}")
    else:
        print(f"✅ No void candidates found")

    return {
        "void_candidates": void_candidates,
        "summary": summary,
        "export_paths": export_paths,
    }


def main():
    """
    Main function for command-line usage
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Automated Void Analyzer for 17Track Results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --file tracking_results.json
  %(prog)s --directory data/output --pattern "*tracking*.json"
  %(prog)s --file results.json --min-days 10 --max-days 25
  %(prog)s --directory data/output --no-csv --json-only
        """,
    )

    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--file", help="Single JSON file to analyze")
    input_group.add_argument(
        "--directory", help="Directory containing JSON files to analyze"
    )

    # Analysis options
    parser.add_argument(
        "--pattern",
        default="*tracking*.json",
        help="File pattern for directory analysis (default: *tracking*.json)",
    )
    parser.add_argument(
        "--min-days",
        type=int,
        default=15,
        help="Minimum days since label creation (default: 15)",
    )
    parser.add_argument(
        "--max-days",
        type=int,
        default=20,
        help="Maximum days since label creation (default: 20)",
    )

    # Export options
    parser.add_argument("--no-csv", action="store_true", help="Skip CSV export")
    parser.add_argument("--no-json", action="store_true", help="Skip JSON export")
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )

    args = parser.parse_args()

    print("🤖 Automated Void Analyzer for 17Track Results")
    print("=" * 50)

    if args.file:
        result = analyze_tracking_files(
            file_paths=args.file,
            min_days=args.min_days,
            max_days=args.max_days,
            export_csv=not args.no_csv,
            export_json=not args.no_json,
            output_dir=args.output_dir,
        )
    else:
        result = analyze_tracking_directory(
            directory_path=args.directory,
            file_pattern=args.pattern,
            min_days=args.min_days,
            max_days=args.max_days,
            export_csv=not args.no_csv,
            export_json=not args.no_json,
            output_dir=args.output_dir,
        )

    return result


if __name__ == "__main__":
    main()
