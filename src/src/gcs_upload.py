#!/usr/bin/env python3
"""
Google Cloud Storage Upload Utility
====================================

This script uploads pipeline output files to Google Cloud Storage (GCS) for backup
and archival purposes. It's designed to work with the ephemeral VM deployment pattern
where the VM is destroyed after the pipeline completes.

Features:
- Upload files to GCS with organized folder structure
- Exclude screenshot files from Step 4 uploads
- Proper error handling and logging
- Support for enabling/disabling uploads via environment variable
- Automatic timestamp-based folder organization

Usage:
    # Upload files from a specific pipeline step
    poetry run python src/src/gcs_upload.py --step 1 --files data/output/carrier_invoice_extraction.duckdb

    # Upload multiple files
    poetry run python src/src/gcs_upload.py --step 3 --files data/output/ups_label_only_*.csv data/output/ups_label_only_*.json

    # Dry run (no actual upload)
    poetry run python src/src/gcs_upload.py --step 4 --files data/output/ups_void_*.csv --dry-run

Environment Variables:
    GCS_BUCKET_NAME: GCS bucket name (default: void_automation)
    GCS_ENABLE_UPLOAD: Enable/disable uploads (default: true)
    GCS_PROJECT_ID: GCP project ID (optional, uses default credentials)

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import argparse
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "void_automation")
GCS_ENABLE_UPLOAD = os.getenv("GCS_ENABLE_UPLOAD", "true").lower() == "true"
GCS_PROJECT_ID = os.getenv("GCS_PROJECT_ID")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data/output")

# Step name mapping
STEP_NAMES = {
    0: "step0_slack_whitelist",
    1: "step1_clickhouse",
    2: "step2_peerdb",
    3: "step3_label_filter",
    4: "step4_void_automation",
}


def get_gcs_client() -> Optional[storage.Client]:
    """
    Initialize and return a GCS client

    Returns:
        storage.Client or None if initialization fails
    """
    try:
        if GCS_PROJECT_ID:
            client = storage.Client(project=GCS_PROJECT_ID)
        else:
            # Use default credentials (works on GCP VMs with proper IAM roles)
            client = storage.Client()

        logger.info(f"✅ GCS client initialized (project: {client.project})")
        return client
    except Exception as e:
        logger.error(f"❌ Failed to initialize GCS client: {e}")
        return None


def get_run_timestamp() -> str:
    """
    Get or create a run timestamp for organizing uploads

    Returns:
        Timestamp string in format YYYY-MM-DD_HH-MM-SS
    """
    # Use environment variable if set (for consistency across steps in same run)
    timestamp = os.getenv("PIPELINE_RUN_TIMESTAMP")
    if not timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # Set for subsequent steps
        os.environ["PIPELINE_RUN_TIMESTAMP"] = timestamp

    return timestamp


def should_exclude_file(filepath: str, step: int) -> bool:
    """
    Determine if a file should be excluded from upload

    Args:
        filepath: Path to the file
        step: Pipeline step number

    Returns:
        True if file should be excluded, False otherwise
    """
    # Step 4: Exclude screenshot files (PNG, JPG, JPEG)
    if step == 4:
        file_ext = Path(filepath).suffix.lower()
        if file_ext in [".png", ".jpg", ".jpeg"]:
            logger.info(f"⏭️  Excluding screenshot file: {Path(filepath).name}")
            return True

    return False


def upload_file_to_gcs(
    client: storage.Client,
    local_filepath: str,
    step: int,
    run_timestamp: str,
    dry_run: bool = False,
) -> bool:
    """
    Upload a single file to GCS

    Args:
        client: GCS client
        local_filepath: Path to local file
        step: Pipeline step number
        run_timestamp: Run timestamp for folder organization
        dry_run: If True, don't actually upload

    Returns:
        True if upload successful, False otherwise
    """
    try:
        # Check if file should be excluded
        if should_exclude_file(local_filepath, step):
            return True  # Not an error, just skipped

        # Check if file exists
        if not os.path.exists(local_filepath):
            logger.error(f"❌ File not found: {local_filepath}")
            return False

        # Get file info
        file_path = Path(local_filepath)
        file_size = file_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        # Build GCS path: pipeline_runs/YYYY-MM-DD_HH-MM-SS/stepN_name/filename
        step_name = STEP_NAMES.get(step, f"step{step}")
        gcs_path = f"pipeline_runs/{run_timestamp}/{step_name}/{file_path.name}"

        logger.info(f"📤 Uploading: {file_path.name} ({file_size_mb:.2f} MB)")
        logger.info(f"   Local:  {local_filepath}")
        logger.info(f"   GCS:    gs://{GCS_BUCKET_NAME}/{gcs_path}")

        if dry_run:
            logger.info("   🔍 DRY RUN - Upload skipped")
            return True

        # Get bucket and upload
        bucket = client.bucket(GCS_BUCKET_NAME)
        blob = bucket.blob(gcs_path)

        # Upload with progress
        blob.upload_from_filename(local_filepath)

        logger.info(f"   ✅ Upload successful!")
        return True

    except GoogleCloudError as e:
        logger.error(f"❌ GCS error uploading {local_filepath}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error uploading {local_filepath}: {e}")
        return False


def upload_files(
    files: List[str],
    step: int,
    dry_run: bool = False,
) -> int:
    """
    Upload multiple files to GCS

    Args:
        files: List of file paths to upload
        step: Pipeline step number
        dry_run: If True, don't actually upload

    Returns:
        Number of files successfully uploaded
    """
    # Check if uploads are enabled
    if not GCS_ENABLE_UPLOAD:
        logger.info("ℹ️  GCS uploads disabled (GCS_ENABLE_UPLOAD=false)")
        return 0

    if not files:
        logger.warning("⚠️  No files specified for upload")
        return 0

    logger.info("=" * 60)
    logger.info(f"🚀 GCS UPLOAD - STEP {step}")
    logger.info("=" * 60)
    logger.info(f"📦 Bucket: gs://{GCS_BUCKET_NAME}")
    logger.info(f"📁 Files to upload: {len(files)}")
    if dry_run:
        logger.info("🔍 DRY RUN MODE - No actual uploads")
    logger.info("=" * 60)

    # Initialize GCS client
    client = get_gcs_client()
    if not client:
        logger.error("❌ Failed to initialize GCS client - aborting upload")
        return 0

    # Get run timestamp
    run_timestamp = get_run_timestamp()
    logger.info(f"⏰ Run timestamp: {run_timestamp}")

    # Upload each file
    success_count = 0
    for filepath in files:
        if upload_file_to_gcs(client, filepath, step, run_timestamp, dry_run):
            success_count += 1

    # Summary
    logger.info("=" * 60)
    logger.info(f"📊 Upload Summary:")
    logger.info(f"   Total files: {len(files)}")
    logger.info(f"   Successful: {success_count}")
    logger.info(f"   Failed: {len(files) - success_count}")
    logger.info("=" * 60)

    if success_count == len(files):
        logger.info("✅ All files uploaded successfully!")
    elif success_count > 0:
        logger.warning(
            f"⚠️  Partial success: {success_count}/{len(files)} files uploaded"
        )
    else:
        logger.error("❌ All uploads failed!")

    return success_count


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Upload pipeline output files to Google Cloud Storage"
    )
    parser.add_argument(
        "--step",
        type=int,
        required=True,
        choices=[0, 1, 2, 3, 4],
        help="Pipeline step number (0-4)",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        required=True,
        help="Files to upload (supports wildcards)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (no actual upload)",
    )

    args = parser.parse_args()

    # Upload files
    success_count = upload_files(
        files=args.files,
        step=args.step,
        dry_run=args.dry_run,
    )

    # Exit with appropriate code
    if success_count == len(args.files):
        sys.exit(0)
    elif success_count > 0:
        sys.exit(1)  # Partial failure
    else:
        sys.exit(2)  # Complete failure


if __name__ == "__main__":
    main()
