# Google Cloud Storage Upload Setup Guide

## Overview

The GSR Automation pipeline now automatically uploads output files from each pipeline step to Google Cloud Storage (GCS) for backup and archival purposes. This is especially important for the ephemeral VM deployment pattern where the VM is destroyed after the pipeline completes.

## Features

- ✅ **Automatic Upload**: Files are uploaded after each successful pipeline step
- ✅ **Organized Structure**: Files are organized by run timestamp and step name
- ✅ **Screenshot Exclusion**: Step 4 automatically excludes screenshot files (PNG/JPG)
- ✅ **Error Handling**: Upload failures don't stop the pipeline
- ✅ **Enable/Disable**: Can be toggled via environment variable
- ✅ **Dry Run Mode**: Test uploads without actually uploading

## GCS Bucket Structure

```
gs://void_automation/
  └── pipeline_runs/
      └── 2025-11-21_14-30-00/  # Run timestamp
          ├── step1_clickhouse/
          │   └── carrier_invoice_extraction.duckdb
          ├── step2_peerdb/
          │   └── peerdb_industry_index_logins_20251121_143015.csv
          ├── step3_label_filter/
          │   ├── ups_label_only_tracking_range_20250820_to_20250821_20251121_143045.csv
          │   └── ups_label_only_filter_range_20250820_to_20250821_20251121_143045.json
          └── step4_void_automation/
              └── ups_void_automation_results_20251121_143200.csv
```

## Configuration

### Environment Variables (.env)

Add the following to your `.env` file:

```bash
# Google Cloud Storage Configuration (for pipeline output backup)
GCS_BUCKET_NAME=void_automation
GCS_ENABLE_UPLOAD=true
GCS_PROJECT_ID=your-gcp-project-id  # Optional, uses default credentials if not set
```

### Configuration Options

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GCS_BUCKET_NAME` | GCS bucket name | `void_automation` | Yes |
| `GCS_ENABLE_UPLOAD` | Enable/disable uploads | `true` | No |
| `GCS_PROJECT_ID` | GCP project ID | Auto-detected | No |

## GCP Setup

### 1. Create GCS Bucket

```bash
# Create the bucket (if it doesn't exist)
gsutil mb gs://void_automation

# Verify bucket exists
gsutil ls gs://void_automation
```

### 2. Set Up Authentication

#### Option A: Service Account (Recommended for VMs)

1. Create a service account:
```bash
gcloud iam service-accounts create gsr-automation-uploader \
    --display-name="GSR Automation GCS Uploader"
```

2. Grant Storage Object Creator role:
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:gsr-automation-uploader@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectCreator"
```

3. For VM deployment, attach the service account to the VM:
```bash
gcloud compute instances create gsr-automation-vm \
    --service-account=gsr-automation-uploader@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --scopes=https://www.googleapis.com/auth/devstorage.read_write
```

#### Option B: Application Default Credentials (Local Development)

```bash
gcloud auth application-default login
```

### 3. Update GCP Secret Manager (for VM deployment)

```bash
# Update the secret with new .env file
gcloud secrets versions add gsr-automation-env --data-file=.env
```

## Usage

### Automatic Upload (via Makefile)

The Makefile automatically uploads files after each step:

```bash
# Run full pipeline (uploads happen automatically)
make pipeline-full

# Run individual steps (uploads happen automatically)
make pipeline-step1
make pipeline-step2
make pipeline-step3
make pipeline-step4
```

### Manual Upload

You can also upload files manually using the `gcs_upload.py` script:

```bash
# Upload Step 1 output
poetry run python src/src/gcs_upload.py --step 1 --files data/output/carrier_invoice_extraction.duckdb

# Upload Step 2 output
poetry run python src/src/gcs_upload.py --step 2 --files data/output/peerdb_industry_index_logins_*.csv

# Upload Step 3 outputs
poetry run python src/src/gcs_upload.py --step 3 --files data/output/ups_label_only_tracking_range_*.csv data/output/ups_label_only_filter_range_*.json

# Upload Step 4 output (screenshots automatically excluded)
poetry run python src/src/gcs_upload.py --step 4 --files data/output/ups_void_automation_results_*.csv

# Dry run (test without uploading)
poetry run python src/src/gcs_upload.py --step 1 --files data/output/carrier_invoice_extraction.duckdb --dry-run
```

## Files Uploaded by Step

| Step | Script | Files Uploaded | Notes |
|------|--------|----------------|-------|
| 0 | `slack_whitelist_ip.py` | None | No output files |
| 1 | `dlt_pipeline_examples.py` | `carrier_invoice_extraction.duckdb` | DuckDB database |
| 2 | `peerdb_pipeline.py` | `peerdb_industry_index_logins_*.csv` | CSV with timestamps |
| 3 | `ups_label_only_filter.py` | `ups_label_only_tracking_range_*.csv`<br>`ups_label_only_filter_range_*.json` | CSV and JSON |
| 4 | `ups_shipment_void_automation.py` | `ups_void_automation_results_*.csv` | **Excludes** `*.png` screenshots |

## Troubleshooting

### Upload Failures Don't Stop Pipeline

By design, GCS upload failures are logged but don't stop the pipeline execution. This ensures the pipeline completes even if GCS is temporarily unavailable.

### Check Upload Logs

```bash
# View recent logs
make logs

# View specific step log
tail -f logs/step1_dlt_pipeline_*.log
```

### Disable Uploads

To temporarily disable uploads:

```bash
# In .env file
GCS_ENABLE_UPLOAD=false
```

### Verify Uploads

```bash
# List recent uploads
gsutil ls -lh gs://void_automation/pipeline_runs/

# List specific run
gsutil ls -lh gs://void_automation/pipeline_runs/2025-11-21_14-30-00/

# Download a file
gsutil cp gs://void_automation/pipeline_runs/2025-11-21_14-30-00/step1_clickhouse/carrier_invoice_extraction.duckdb ./
```

## Best Practices

1. **Monitor Storage Costs**: Regularly review and clean up old pipeline runs
2. **Set Lifecycle Policies**: Configure automatic deletion of old files
3. **Use Service Accounts**: For VM deployments, use service accounts with minimal permissions
4. **Test Locally First**: Use `--dry-run` to test uploads before deploying
5. **Check Logs**: Always review logs after pipeline runs to ensure uploads succeeded

## Next Steps

- Set up GCS lifecycle policies to automatically delete old files
- Configure Cloud Monitoring alerts for upload failures
- Consider using Cloud Storage Transfer Service for large-scale backups

