# GSR Automation Pipeline - Complete Overview

## Pipeline Architecture

The GSR Automation pipeline is designed for **ephemeral VM deployment** on Google Cloud Platform:

```
┌─────────────────────────────────────────────────────────────────┐
│                    EPHEMERAL VM DEPLOYMENT                       │
│                                                                   │
│  1. Create VM → 2. Run Pipeline → 3. Upload to GCS → 4. Destroy │
└─────────────────────────────────────────────────────────────────┘
```

## Pipeline Steps (5 Steps Total)

| Step  | Name               | Script                            | Purpose                             | Critical | Output Files                                                                  |
| ----- | ------------------ | --------------------------------- | ----------------------------------- | -------- | ----------------------------------------------------------------------------- |
| **0** | IP Whitelisting    | `slack_whitelist_ip.py`           | Whitelist VM IP for database access | ✅ Yes   | None                                                                          |
| **1** | ClickHouse Extract | `dlt_pipeline_examples.py`        | Extract carrier invoice data        | ✅ Yes   | `carrier_invoice_extraction.duckdb`                                           |
| **2** | PeerDB Extract     | `peerdb_pipeline.py`              | Extract login credentials           | ⚠️ No    | `peerdb_industry_index_logins_*.csv`                                          |
| **3** | Label Filter       | `ups_label_only_filter.py`        | Filter label-only tracking numbers  | ✅ Yes   | `ups_label_only_tracking_range_*.csv`<br>`ups_label_only_filter_range_*.json` |
| **4** | Void Automation    | `ups_shipment_void_automation.py` | Automated UPS shipment void         | ✅ Yes   | `ups_void_automation_results_*.csv`<br>`*.png` (screenshots)                  |

---

## Step 0: IP Whitelisting 🔐

**Purpose**: Whitelist the VM's public IP address to enable database access

**Script**: `src/src/slack_whitelist_ip.py`

**Command**:

```bash
poetry run python src/src/slack_whitelist_ip.py
```

**Process**:

1. Detects VM's public IPv4 address from GCP metadata service
2. Posts message to Slack channel `C03B931H51A`: `<@U09HGK7HH8Q> ip_whitelist {ip}`
3. G-bot (gbot2) processes the mention and whitelists the IP in database firewall

**Output Files**: None

**GCS Upload**: None (no files to upload)

**Delay After**: 10 seconds

**Error Handling**: **CRITICAL** - Pipeline stops if whitelisting fails

---

## Step 1: Extract Carrier Invoice Data 🚀

**Purpose**: Extract carrier invoice data from ClickHouse to DuckDB

**Script**: `src/src/dlt_pipeline_examples.py`

**Command**:

```bash
poetry run python src/src/dlt_pipeline_examples.py
```

**Process**:

1. Connects to ClickHouse database (requires IP whitelisting from Step 0)
2. Extracts data from `carrier_carrier_invoice_original_flat_ups` table
3. Filters by `invoice_date` (last 30 days from extraction date)
4. Uses incremental loading via `import_time` field
5. Exports to DuckDB file with batching (50k-100k records per batch)

**Output Files**:

- `data/output/carrier_invoice_extraction.duckdb` (fixed filename, replaces existing)

**GCS Upload**:

```bash
poetry run python src/src/gcs_upload.py --step 1 --files data/output/carrier_invoice_extraction.duckdb
```

- Uploads to: `gs://void_automation/pipeline_runs/YYYY-MM-DD_HH-MM-SS/step1_clickhouse/carrier_invoice_extraction.duckdb`

**Delay After**: 60 seconds

**Error Handling**:

- Script failure: **CRITICAL** - Pipeline stops
- GCS upload failure: **NON-CRITICAL** - Warning logged, pipeline continues

---

## Step 2: Extract Industry Index Logins 📊

**Purpose**: Extract login credentials from PeerDB for UPS automation

**Script**: `src/src/peerdb_pipeline.py`

**Command**:

```bash
poetry run python src/src/peerdb_pipeline.py
```

**Process**:

1. Connects to PeerDB database (requires IP whitelisting from Step 0)
2. Extracts data from `peerdb.industry_index_logins` table
3. Maps account numbers using equation: `industry_index_login.account_number = RIGHT(carrier_invoice.account_number, 6)`
4. Exports to timestamped CSV file

**Output Files**:

- `data/output/peerdb_industry_index_logins_YYYYMMDD_HHMMSS.csv`

**GCS Upload**:

```bash
poetry run python src/src/gcs_upload.py --step 2 --files data/output/peerdb_industry_index_logins_*.csv
```

- Uploads to: `gs://void_automation/pipeline_runs/YYYY-MM-DD_HH-MM-SS/step2_peerdb/peerdb_industry_index_logins_*.csv`

**Delay After**: 60 seconds

**Error Handling**:

- Script failure: **NON-CRITICAL** - Warning logged, pipeline continues (Step 4 uses fallback credentials)
- GCS upload failure: **NON-CRITICAL** - Warning logged, pipeline continues

---

## Step 3: Filter Label-Only Tracking Numbers 🔍

**Purpose**: Filter tracking numbers with "label created" status for voiding

**Script**: `src/src/ups_label_only_filter.py`

**Command**:

```bash
poetry run python src/src/ups_label_only_filter.py
```

**Process**:

1. Reads tracking numbers from DuckDB file (Step 1 output)
2. Filters by `transaction_date` (80-85 days before extraction date)
3. Queries UPS API for tracking status
4. Filters to only tracking numbers with status: "Shipper created a label, UPS has not received the package yet."
5. Processes in batches of 40 to avoid API rate limits
6. Exports filtered results to CSV and JSON

**Output Files**:

- `data/output/ups_label_only_tracking_range_YYYYMMDD_to_YYYYMMDD_TIMESTAMP.csv`
- `data/output/ups_label_only_filter_range_YYYYMMDD_to_YYYYMMDD_TIMESTAMP.json`

**GCS Upload**:

```bash
poetry run python src/src/gcs_upload.py --step 3 \
  --files data/output/ups_label_only_tracking_range_*.csv \
          data/output/ups_label_only_filter_range_*.json
```

- Uploads to: `gs://void_automation/pipeline_runs/YYYY-MM-DD_HH-MM-SS/step3_label_filter/`

**Delay After**: 120 seconds

**Error Handling**:

- Script failure: **CRITICAL** - Pipeline stops
- GCS upload failure: **NON-CRITICAL** - Warning logged, pipeline continues

---

## Step 4: Automated UPS Shipment Void 🌐

**Purpose**: Automatically void UPS shipments via web automation

**Script**: `src/src/ups_shipment_void_automation.py`

**Command**:

```bash
poetry run python src/src/ups_shipment_void_automation.py --headed
```

**Process**:

1. Reads tracking numbers from Step 3 output (latest CSV file matching pattern)
2. Uses Playwright browser automation in **headed mode** (visible browser with X11 display)
3. Logs into UPS website using credentials from Step 2 (or fallback credentials)
4. Navigates to void shipment page
5. Processes tracking numbers with automatic credential rotation on rate limits (HTTP 429)
6. Saves results to CSV and screenshots to PNG files

**Output Files**:

- `data/output/ups_void_automation_results_YYYYMMDD_HHMMSS.csv` ✅ **UPLOADED**
- `data/output/*.png` (screenshots: `01_login_page_*.png`, `02_username_entered_*.png`, etc.) ❌ **NOT UPLOADED**

**GCS Upload**:

```bash
poetry run python src/src/gcs_upload.py --step 4 --files data/output/ups_void_automation_results_*.csv
```

- Uploads to: `gs://void_automation/pipeline_runs/YYYY-MM-DD_HH-MM-SS/step4_void_automation/ups_void_automation_results_*.csv`
- **Note**: Screenshots (PNG files) are automatically excluded by the GCS upload script

**Display Requirements**: Requires X11 display (DISPLAY=:0) for headed browser mode

**Delay After**: None (final step)

**Error Handling**:

- Script failure: **CRITICAL** - Pipeline stops
- GCS upload failure: **NON-CRITICAL** - Warning logged, pipeline continues

---

## GCS Upload Summary

All output files are automatically uploaded to Google Cloud Storage after each successful step:

### GCS Bucket Structure

```
gs://void_automation/
  └── pipeline_runs/
      └── 2025-11-21_14-30-00/  # Run timestamp (shared across all steps)
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

### GCS Upload Features

- ✅ **Automatic Upload**: Files uploaded after each successful step
- ✅ **Organized Structure**: Files organized by run timestamp and step name
- ✅ **Screenshot Exclusion**: Step 4 automatically excludes PNG/JPG screenshot files
- ✅ **Error Handling**: Upload failures don't stop the pipeline
- ✅ **Enable/Disable**: Can be toggled via `GCS_ENABLE_UPLOAD=false`
- ✅ **Dry Run Mode**: Test uploads without actually uploading

### Files Uploaded by Step

| Step | Files Uploaded                                                                | Screenshot Exclusion      |
| ---- | ----------------------------------------------------------------------------- | ------------------------- |
| 0    | None                                                                          | N/A                       |
| 1    | `carrier_invoice_extraction.duckdb`                                           | N/A                       |
| 2    | `peerdb_industry_index_logins_*.csv`                                          | N/A                       |
| 3    | `ups_label_only_tracking_range_*.csv`<br>`ups_label_only_filter_range_*.json` | N/A                       |
| 4    | `ups_void_automation_results_*.csv`                                           | ✅ Yes (excludes `*.png`) |

---

## Pipeline Timing

| Step   | Description           | Delay After  |
| ------ | --------------------- | ------------ |
| Step 0 | IP Whitelisting       | 10 seconds   |
| Step 1 | ClickHouse Extraction | 60 seconds   |
| Step 2 | PeerDB Extraction     | 60 seconds   |
| Step 3 | Label Filter          | 120 seconds  |
| Step 4 | Void Automation       | None (final) |

**Total Delays**: 250 seconds (4 minutes 10 seconds) + actual execution time

---

## How to Run the Pipeline

### Full Pipeline (All 5 Steps)

```bash
make pipeline-full
```

This runs all 5 steps sequentially with automatic delays and GCS uploads.

**Expected Flow**:

1. Step 0: IP Whitelist → Wait 10s
2. Step 1: ClickHouse Extract → Upload to GCS → Wait 60s
3. Step 2: PeerDB Extract → Upload to GCS → Wait 60s
4. Step 3: Label Filter → Upload to GCS → Wait 120s
5. Step 4: Void Automation → Upload to GCS → Done!

### Individual Steps

```bash
make pipeline-step0  # IP whitelisting
make pipeline-step1  # ClickHouse extraction + GCS upload
make pipeline-step2  # PeerDB extraction + GCS upload
make pipeline-step3  # Label filter + GCS upload
make pipeline-step4  # Void automation + GCS upload
```

### Test Individual Steps

```bash
make test-step0  # Test IP whitelisting
make test-step1  # Test ClickHouse extraction
make test-step2  # Test PeerDB extraction
make test-step3  # Test label filter
make test-step4  # Test void automation
```

### Background Execution

```bash
make pipeline-full-bg  # Run full pipeline in background
make logs              # View logs
```

---

## Environment Variables Required

### ClickHouse Configuration

```bash
CLICKHOUSE_HOST=your-clickhouse-host
CLICKHOUSE_PORT=8443
CLICKHOUSE_USER=your-username
CLICKHOUSE_PASSWORD=your-password
CLICKHOUSE_DATABASE=default
```

### PeerDB Configuration

```bash
PEERDB_HOST=your-peerdb-host
PEERDB_PORT=5432
PEERDB_USER=your-username
PEERDB_PASSWORD=your-password
PEERDB_DATABASE=peerdb
```

### UPS API Configuration

```bash
UPS_CLIENT_ID=your-client-id
UPS_CLIENT_SECRET=your-client-secret
UPS_USERNAME_1=your-username-1
UPS_PASSWORD_1=your-password-1
UPS_USERNAME_2=your-username-2
UPS_PASSWORD_2=your-password-2
```

### Slack API Configuration

```bash
SLACK_BOT_TOKEN=xoxb-1196297734070-9958913172178-qwmmXiyCUlZllamu2D2J41bN
SLACK_WHITELIST_CHANNEL=C03B931H51A
SLACK_WHITELIST_COMMAND_TEMPLATE=<@U09HGK7HH8Q> ip_whitelist {ip}
```

### Google Cloud Storage Configuration

```bash
GCS_BUCKET_NAME=void_automation
GCS_ENABLE_UPLOAD=true
GCS_PROJECT_ID=your-gcp-project-id
```

### Pipeline Configuration

```bash
OUTPUT_DIR=data/output
DLT_INVOICE_CUTOFF_DAYS=30
TRANSACTION_DATE_START_DAYS_AGO=85
TRANSACTION_DATE_END_DAYS_AGO=80
```

---

## Logging

All steps log to `logs/` directory with timestamped filenames:

- `logs/step0_slack_whitelist_YYYYMMDD_HHMMSS.log`
- `logs/step1_dlt_pipeline_YYYYMMDD_HHMMSS.log`
- `logs/step2_peerdb_pipeline_YYYYMMDD_HHMMSS.log`
- `logs/step3_label_filter_YYYYMMDD_HHMMSS.log`
- `logs/step4_void_automation_YYYYMMDD_HHMMSS.log`

**View Logs**:

```bash
make logs        # View recent logs
make clean-logs  # Clean logs >7 days old
```

---

## Error Handling

See [PIPELINE_ERROR_HANDLING.md](./PIPELINE_ERROR_HANDLING.md) for comprehensive error handling documentation.

**Quick Summary**:

| Step       | On Failure   | Action                |
| ---------- | ------------ | --------------------- |
| Step 0     | Critical     | ❌ Pipeline stops     |
| Step 1     | Critical     | ❌ Pipeline stops     |
| Step 2     | Non-critical | ⚠️ Pipeline continues |
| Step 3     | Critical     | ❌ Pipeline stops     |
| Step 4     | Critical     | ❌ Pipeline stops     |
| GCS Upload | Non-critical | ⚠️ Pipeline continues |

---

## Deployment Flow

### Ephemeral VM Deployment (Recommended)

```
1. Create GCP VM
   ↓
2. Install dependencies (poetry install)
   ↓
3. Load .env from Secret Manager
   ↓
4. Run: make pipeline-full
   ├─ Step 0: Whitelist IP → Slack → G-bot
   ├─ Step 1: ClickHouse → DuckDB → GCS
   ├─ Step 2: PeerDB → CSV → GCS
   ├─ Step 3: Filter → CSV/JSON → GCS
   └─ Step 4: Void → CSV → GCS (screenshots excluded)
   ↓
5. All outputs safely in GCS
   ↓
6. Destroy VM
```

### Persistent VM Deployment (Alternative)

```
1. Create GCP VM (persistent)
   ↓
2. Install dependencies (poetry install)
   ↓
3. Load .env from Secret Manager
   ↓
4. Set up cron job: make pipeline-full (every other day)
   ↓
5. Monitor logs and GCS uploads
```

---

## GCP Setup Requirements

### 1. Create GCS Bucket

```bash
gsutil mb gs://void_automation
```

### 2. Create Service Account

```bash
gcloud iam service-accounts create gsr-automation-uploader \
    --display-name="GSR Automation GCS Uploader"
```

### 3. Grant Permissions

```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:gsr-automation-uploader@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectCreator"
```

### 4. Create VM with Service Account

```bash
gcloud compute instances create gsr-automation-vm \
    --service-account=gsr-automation-uploader@YOUR_PROJECT_ID.iam.gserviceaccount.com \
    --scopes=https://www.googleapis.com/auth/devstorage.read_write \
    --machine-type=e2-standard-4 \
    --boot-disk-size=50GB
```

### 5. Store Secrets in Secret Manager

```bash
gcloud secrets create gsr-automation-env --data-file=.env
```

---

## Best Practices

1. ✅ **Monitor Critical Steps**: Focus on Steps 0, 1, 3, 4
2. ✅ **Review Logs**: Always check logs after pipeline runs
3. ✅ **Verify GCS Uploads**: Ensure files are in GCS before VM destruction
4. ✅ **Handle Step 2 Gracefully**: Pipeline continues if PeerDB fails
5. ✅ **Set Up Alerts**: Monitor for repeated failures
6. ✅ **Clean Up Old Data**: Use lifecycle policies on GCS bucket

---

## Documentation

- **[PIPELINE_OVERVIEW.md](./PIPELINE_OVERVIEW.md)** - This document
- **[PIPELINE_ERROR_HANDLING.md](./PIPELINE_ERROR_HANDLING.md)** - Comprehensive error handling guide
- **[GCS_UPLOAD_SETUP.md](../docs/GCS_UPLOAD_SETUP.md)** - GCS upload setup guide
- **[Makefile](./option1_persistent_vm/Makefile)** - Pipeline orchestration

---

## Summary

The GSR Automation pipeline is a **production-ready, robust data pipeline** designed for ephemeral VM deployment on Google Cloud Platform. It:

✅ Automatically whitelists VM IP for database access
✅ Extracts carrier invoice data from ClickHouse
✅ Extracts login credentials from PeerDB
✅ Filters label-only tracking numbers via UPS API
✅ Automates UPS shipment void via browser automation
✅ Uploads all outputs to GCS for preservation
✅ Handles errors gracefully with clear logging
✅ Supports both ephemeral and persistent VM deployment

**Ready for deployment!** 🚀
