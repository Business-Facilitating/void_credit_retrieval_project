# GSR Automation Pipeline - Error Handling Documentation

## Overview

This document describes the error handling strategy for the GSR Automation pipeline. The pipeline consists of 5 sequential steps, each with specific error handling behavior designed to ensure reliability while maximizing pipeline completion rates.

## Error Handling Philosophy

The error handling follows this principle:

```
┌─────────────────────────────────────────────────────────┐
│  CRITICAL: Steps that produce data needed by later steps │
│  - Step 0: IP whitelisting (enables database access)     │
│  - Step 1: ClickHouse data (needed for Step 3)          │
│  - Step 3: Filtered tracking (needed for Step 4)        │
│  - Step 4: Void automation (main goal)                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  NON-CRITICAL: Steps that enhance but aren't required    │
│  - Step 2: PeerDB logins (fallback credentials exist)   │
│  - All GCS uploads (backup only, not operational)       │
└─────────────────────────────────────────────────────────┘
```

## Error Handling Summary Table

| Step       | Script                            | On Script Failure          | On GCS Upload Failure      | Pipeline Behavior                  |
| ---------- | --------------------------------- | -------------------------- | -------------------------- | ---------------------------------- |
| **Step 0** | `slack_whitelist_ip.py`           | ❌ **STOPS** (`exit 1`)    | N/A (no upload)            | Critical - Must succeed            |
| **Step 1** | `dlt_pipeline_examples.py`        | ❌ **STOPS** (`exit 1`)    | ⚠️ **CONTINUES** (warning) | Script critical, upload optional   |
| **Step 2** | `peerdb_pipeline.py`              | ⚠️ **CONTINUES** (warning) | ⚠️ **CONTINUES** (warning) | Non-critical - Can proceed without |
| **Step 3** | `ups_label_only_filter.py`        | ❌ **STOPS** (`exit 1`)    | ⚠️ **CONTINUES** (warning) | Script critical, upload optional   |
| **Step 4** | `ups_shipment_void_automation.py` | ❌ **STOPS** (`exit 1`)    | ⚠️ **CONTINUES** (warning) | Script critical, upload optional   |

## Detailed Error Handling by Step

### Step 0: IP Whitelisting 🔐

**Script**: `src/src/slack_whitelist_ip.py`

**Error Handling**:

```bash
if [ $? -eq 0 ]; then
    echo "✅ Step 0 completed successfully"
else
    echo "❌ Step 0 failed - IP whitelisting unsuccessful"
    exit 1  # STOPS PIPELINE
fi
```

**Behavior**:

- **Script Failure**: **CRITICAL** - Pipeline stops immediately
- **GCS Upload**: N/A (no output files)

**Rationale**: Without IP whitelisting, the VM cannot access ClickHouse or PeerDB databases, making all subsequent steps impossible. This must succeed for the pipeline to proceed.

**Common Failure Scenarios**:

- Slack API token invalid or expired
- G-bot not responding in channel
- Network connectivity issues
- GCP metadata service unavailable

**Recovery**: Fix Slack credentials or network issues, then restart pipeline

---

### Step 1: ClickHouse Extraction 🚀

**Script**: `src/src/dlt_pipeline_examples.py`

**Error Handling**:

```bash
if [ $? -eq 0 ]; then
    echo "✅ Step 1 completed successfully"
    echo "📤 Uploading Step 1 outputs to GCS..."
    poetry run python gcs_upload.py --step 1 --files carrier_invoice_extraction.duckdb || \
        echo "⚠️ GCS upload failed (continuing pipeline)"
else
    echo "❌ Step 1 failed"
    exit 1  # STOPS PIPELINE
fi
```

**Behavior**:

- **Script Failure**: **CRITICAL** - Pipeline stops immediately
- **GCS Upload Failure**: **NON-CRITICAL** - Warning logged, pipeline continues

**Rationale**:

- The ClickHouse data is essential for Step 3 (filtering tracking numbers)
- GCS upload is for backup/archival only, not operationally required

**Output Files**:

- `data/output/carrier_invoice_extraction.duckdb` (uploaded to GCS)

**Common Failure Scenarios**:

- ClickHouse connection timeout (IP not whitelisted)
- Database credentials invalid
- Query timeout or resource limits
- Disk space full

**Recovery**:

- Script failure: Fix database connection, restart from Step 1
- GCS upload failure: Files remain on VM, can be manually uploaded later

---

### Step 2: PeerDB Extraction 📊

**Script**: `src/src/peerdb_pipeline.py`

**Error Handling**:

```bash
if [ $? -eq 0 ]; then
    echo "✅ Step 2 completed successfully"
    echo "📤 Uploading Step 2 outputs to GCS..."
    poetry run python gcs_upload.py --step 2 --files peerdb_industry_index_logins_*.csv || \
        echo "⚠️ GCS upload failed (continuing pipeline)"
else
    echo "⚠️ Step 2 failed - continuing with pipeline (login credentials may not be available)"
    # NO exit 1 - CONTINUES
fi
```

**Behavior**:

- **Script Failure**: **NON-CRITICAL** - Warning logged, pipeline continues
- **GCS Upload Failure**: **NON-CRITICAL** - Warning logged, pipeline continues

**Rationale**:

- Login credentials from PeerDB enhance Step 4 but aren't strictly required
- Step 4 has fallback credential rotation mechanism
- Better to proceed with limited credentials than stop entire pipeline

**Output Files**:

- `data/output/peerdb_industry_index_logins_YYYYMMDD_HHMMSS.csv` (uploaded to GCS if successful)

**Common Failure Scenarios**:

- PeerDB connection timeout (IP not whitelisted)
- Database credentials invalid
- Table schema changed
- No matching account numbers found

**Recovery**: Pipeline continues automatically; Step 4 will use fallback credentials

---

### Step 3: Label Filter 🔍

**Script**: `src/src/ups_label_only_filter.py`

**Error Handling**:

```bash
if [ $? -eq 0 ]; then
    echo "✅ Step 3 completed successfully"
    echo "📤 Uploading Step 3 outputs to GCS..."
    poetry run python gcs_upload.py --step 3 \
        --files ups_label_only_tracking_range_*.csv ups_label_only_filter_range_*.json || \
        echo "⚠️ GCS upload failed (continuing pipeline)"
else
    echo "❌ Step 3 failed"
    exit 1  # STOPS PIPELINE
fi
```

**Behavior**:

- **Script Failure**: **CRITICAL** - Pipeline stops immediately
- **GCS Upload Failure**: **NON-CRITICAL** - Warning logged, pipeline continues

**Rationale**:

- Filtered tracking numbers are essential input for Step 4
- Without filtered tracking numbers, Step 4 has nothing to process
- GCS upload is for backup/archival only

**Output Files**:

- `data/output/ups_label_only_tracking_range_YYYYMMDD_to_YYYYMMDD_TIMESTAMP.csv` (uploaded to GCS)
- `data/output/ups_label_only_filter_range_YYYYMMDD_to_YYYYMMDD_TIMESTAMP.json` (uploaded to GCS)

**Common Failure Scenarios**:

- DuckDB file from Step 1 not found or corrupted
- No tracking numbers match filter criteria (80-85 days ago, label-only status)
- UPS API rate limit exceeded
- Invalid tracking number format

**Recovery**:

- Script failure: Fix data issues, restart from Step 3
- GCS upload failure: Files remain on VM, can be manually uploaded later

---

### Step 4: Void Automation 🌐

**Script**: `src/src/ups_shipment_void_automation.py`

**Error Handling**:

```bash
poetry run python ups_shipment_void_automation.py --headed 2>&1 | tee log;
EXIT_CODE=$?;
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Step 4 completed successfully"
    echo "📤 Uploading Step 4 outputs to GCS (excluding screenshots)..."
    poetry run python gcs_upload.py --step 4 \
        --files ups_void_automation_results_*.csv || \
        echo "⚠️ GCS upload failed (continuing pipeline)"
else
    echo "❌ Step 4 failed"
    exit 1  # STOPS PIPELINE
fi
```

**Behavior**:

- **Script Failure**: **CRITICAL** - Pipeline stops immediately
- **GCS Upload Failure**: **NON-CRITICAL** - Warning logged, pipeline continues

**Rationale**:

- Void automation is the primary goal of the entire pipeline
- Failure indicates shipments were not voided, requiring manual intervention
- GCS upload is for backup/archival only

**Output Files**:

- `data/output/ups_void_automation_results_YYYYMMDD_HHMMSS.csv` (uploaded to GCS)
- `data/output/*.png` (screenshots - **NOT uploaded to GCS**)

**Common Failure Scenarios**:

- UPS website structure changed (Playwright selectors broken)
- Login credentials invalid or expired
- UPS API rate limit exceeded
- Browser automation timeout
- X11 display not available
- Network connectivity issues

**Recovery**:

- Script failure: Review logs, fix automation issues, restart from Step 4
- GCS upload failure: Files remain on VM, can be manually uploaded later

---

## GCS Upload Error Handling

All GCS uploads use the same error handling pattern:

```bash
poetry run python gcs_upload.py --step N --files <files> || \
    echo "⚠️ GCS upload failed (continuing pipeline)"
```

**Behavior**:

- Upload failures are logged but **never stop the pipeline**
- The `||` operator ensures the pipeline continues even if upload fails
- Warning message is displayed for visibility

**Rationale**:

- GCS uploads are for backup/archival purposes only
- Output files remain on the VM even if upload fails
- Better to complete the pipeline than stop for a backup failure
- Files can be manually uploaded later if needed

**Common GCS Upload Failure Scenarios**:

- GCS bucket doesn't exist
- Service account lacks permissions (needs `roles/storage.objectCreator`)
- Network connectivity issues
- GCS API quota exceeded
- Invalid bucket name or path
- Authentication failure (missing credentials)

**Recovery**:

- Files remain in `data/output/` directory on VM
- Can manually upload using: `gsutil cp <file> gs://void_automation/pipeline_runs/...`
- Or re-run GCS upload script: `poetry run python src/src/gcs_upload.py --step N --files <files>`

---

## Pipeline Flow with Error Handling

```
Step 0: IP Whitelist
  ├─ Success → Continue to Step 1
  └─ Failure → ❌ STOP (exit 1)
      └─ Fix: Slack credentials, network, restart pipeline

Step 1: ClickHouse Extract
  ├─ Success → Upload to GCS
  │   ├─ Upload Success → Continue to Step 2
  │   └─ Upload Failure → ⚠️ Warning, Continue to Step 2
  └─ Failure → ❌ STOP (exit 1)
      └─ Fix: Database connection, restart from Step 1

Step 2: PeerDB Extract
  ├─ Success → Upload to GCS
  │   ├─ Upload Success → Continue to Step 3
  │   └─ Upload Failure → ⚠️ Warning, Continue to Step 3
  └─ Failure → ⚠️ Warning, Continue to Step 3
      └─ Note: Step 4 will use fallback credentials

Step 3: Label Filter
  ├─ Success → Upload to GCS
  │   ├─ Upload Success → Continue to Step 4
  │   └─ Upload Failure → ⚠️ Warning, Continue to Step 4
  └─ Failure → ❌ STOP (exit 1)
      └─ Fix: Data issues, UPS API, restart from Step 3

Step 4: Void Automation
  ├─ Success → Upload to GCS
  │   ├─ Upload Success → ✅ Pipeline Complete
  │   └─ Upload Failure → ⚠️ Warning, ✅ Pipeline Complete
  └─ Failure → ❌ STOP (exit 1)
      └─ Fix: Automation issues, restart from Step 4
```

---

## Exit Codes

The pipeline uses standard exit codes:

| Exit Code | Meaning                            | Action                    |
| --------- | ---------------------------------- | ------------------------- |
| `0`       | Success                            | Continue to next step     |
| `1`       | Critical failure                   | Stop pipeline immediately |
| N/A       | Non-critical failure (Step 2 only) | Log warning, continue     |

**GCS Upload Exit Codes** (handled by `gcs_upload.py`):

- `0`: All files uploaded successfully
- `1`: Partial success (some files uploaded)
- `2`: Complete failure (no files uploaded)

Note: All GCS upload exit codes are suppressed by `|| echo "warning"` pattern, so they never stop the pipeline.

---

## Logging

All steps log to `logs/` directory with timestamped filenames:

- `logs/step0_slack_whitelist_YYYYMMDD_HHMMSS.log`
- `logs/step1_dlt_pipeline_YYYYMMDD_HHMMSS.log`
- `logs/step2_peerdb_pipeline_YYYYMMDD_HHMMSS.log`
- `logs/step3_label_filter_YYYYMMDD_HHMMSS.log`
- `logs/step4_void_automation_YYYYMMDD_HHMMSS.log`

**Log Retention**:

- Use `make clean-logs` to remove logs older than 7 days
- Use `make logs` to view recent logs

**GCS Upload Logs**:

- GCS upload output is included in the step's log file
- Look for `📤 Uploading` messages and `✅ Upload successful` or `❌ Upload failed`

---

## Best Practices

### 1. Monitor Critical Steps

Focus monitoring on critical steps that can stop the pipeline:

- Step 0: IP whitelisting
- Step 1: ClickHouse extraction
- Step 3: Label filtering
- Step 4: Void automation

### 2. Review Logs After Each Run

Always check logs after pipeline completion:

```bash
make logs
```

### 3. Handle Step 2 Failures Gracefully

If Step 2 fails frequently:

- Verify PeerDB connection and credentials
- Ensure account number mapping is correct
- Consider adding fallback credentials to environment variables

### 4. GCS Upload Monitoring

Set up Cloud Monitoring alerts for:

- Repeated GCS upload failures
- Missing expected files in GCS bucket
- Storage quota approaching limits

### 5. Partial Pipeline Runs

If a step fails, you can restart from that step:

```bash
# If Step 3 failed, restart from Step 3
make pipeline-step3
make pipeline-step4
```

### 6. Manual Intervention

For critical failures requiring manual intervention:

1. Review the step's log file
2. Fix the underlying issue (credentials, network, etc.)
3. Restart from the failed step
4. Verify GCS uploads completed successfully

---

## Troubleshooting Guide

### Step 0 Fails: IP Whitelisting

**Symptoms**: `❌ Step 0 failed - IP whitelisting unsuccessful`

**Checks**:

1. Verify Slack bot token is valid: `SLACK_BOT_TOKEN`
2. Verify G-bot is in channel: `SLACK_WHITELIST_CHANNEL`
3. Check G-bot user ID is correct: `<@U09HGK7HH8Q>`
4. Test Slack API manually: `make test-step0`
5. Check GCP metadata service is accessible

**Fix**: Update `.env` with correct Slack credentials, restart pipeline

---

### Step 1 Fails: ClickHouse Extraction

**Symptoms**: `❌ Step 1 failed`

**Checks**:

1. Verify IP was whitelisted in Step 0
2. Check ClickHouse credentials: `CLICKHOUSE_HOST`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`
3. Test ClickHouse connection manually
4. Check disk space: `df -h`
5. Review query timeout settings

**Fix**: Fix database connection, ensure IP is whitelisted, restart from Step 1

---

### Step 2 Fails: PeerDB Extraction

**Symptoms**: `⚠️ Step 2 failed - continuing with pipeline`

**Checks**:

1. Verify IP was whitelisted in Step 0
2. Check PeerDB credentials
3. Verify `peerdb.industry_index_logins` table exists
4. Check account number mapping logic

**Fix**: Pipeline continues automatically; Step 4 will use fallback credentials. Fix PeerDB connection for future runs.

---

### Step 3 Fails: Label Filter

**Symptoms**: `❌ Step 3 failed`

**Checks**:

1. Verify Step 1 completed successfully (DuckDB file exists)
2. Check date range (80-85 days ago) has data
3. Verify UPS API credentials: `UPS_CLIENT_ID`, `UPS_CLIENT_SECRET`
4. Check UPS API rate limits
5. Review tracking number format

**Fix**: Fix data or API issues, restart from Step 3

---

### Step 4 Fails: Void Automation

**Symptoms**: `❌ Step 4 failed`

**Checks**:

1. Verify Step 3 completed successfully (CSV file exists)
2. Check X11 display is available: `echo $DISPLAY`
3. Verify UPS credentials are valid
4. Check browser automation selectors (UPS website may have changed)
5. Review Playwright logs for timeout errors

**Fix**: Fix automation issues, restart from Step 4

---

### GCS Upload Fails

**Symptoms**: `⚠️ GCS upload failed (continuing pipeline)`

**Checks**:

1. Verify GCS bucket exists: `gsutil ls gs://void_automation`
2. Check service account permissions: `roles/storage.objectCreator`
3. Verify authentication is configured
4. Check network connectivity to GCS
5. Review GCS API quotas

**Fix**: Files remain in `data/output/`, can be manually uploaded later

---

## Summary

The error handling strategy is designed to:

✅ **Maximize pipeline completion** - Only stop for truly critical failures
✅ **Preserve data** - GCS uploads never block the pipeline
✅ **Provide visibility** - Clear error messages and comprehensive logging
✅ **Enable recovery** - Can restart from any failed step
✅ **Handle gracefully** - Non-critical failures (Step 2, GCS uploads) don't stop progress

This approach ensures the pipeline is robust, reliable, and production-ready for ephemeral VM deployment on Google Cloud Platform.
