# Ephemeral VM Deployment - Quick Start Guide

**Project:** gsr_automation  
**Deployment Type:** Option 2 - Ephemeral VM with Cloud Scheduler  
**Last Updated:** 2025-11-22

---

## 📋 Overview

This deployment creates a **fully automated, cost-effective** pipeline that:
- ✅ Runs every other day at 2:00 AM EST
- ✅ Creates a fresh VM for each run
- ✅ Executes the 5-step pipeline (IP whitelist → ClickHouse → PeerDB → Label filter → UPS void)
- ✅ Uploads results to Cloud Storage (including screenshots)
- ✅ Deletes the VM after completion
- ✅ Costs ~$0.50-1/month instead of ~$50-70/month (persistent VM)

---

## 🚀 Deployment Steps

### Prerequisites

1. ✅ GCP project: `void-automation`
2. ✅ `gcloud` CLI installed and authenticated
3. ✅ `.env` file with all credentials (already in Secret Manager version 3)
4. ✅ All code pushed to `dev` branch on GitHub

### Step 1: Navigate to Deployment Folder

```bash
cd deployment/option2_ephemeral_vm
```

### Step 2: Review Configuration

The `deploy_ephemeral.sh` script is already configured with:
- **Project ID:** `void-automation`
- **Region:** `us-central1`
- **Zone:** `us-central1-a`
- **Bucket:** `void_automation` (existing bucket)
- **Repository:** `https://github.com/Business-Facilitating/void_credit_retrieval_project.git`
- **Branch:** `dev`
- **Schedule:** Every other day at 2:00 AM EST

### Step 3: Run Deployment Script

```bash
# Make script executable (if not already)
chmod +x deploy_ephemeral.sh

# Run deployment
./deploy_ephemeral.sh
```

The script will:
1. ✅ Enable required GCP APIs (Compute, Cloud Functions, Cloud Scheduler, Secret Manager, Storage)
2. ✅ Create service account `gsr-automation-runner` with permissions
3. ✅ Use existing secret `gsr-automation-env` (or update if needed)
4. ✅ Use existing Cloud Storage bucket `void_automation`
5. ✅ Deploy Cloud Function `trigger-gsr-automation`
6. ✅ Create Cloud Scheduler job `gsr-automation-scheduler`
7. ✅ Optionally trigger a test run

**Estimated time:** 5-10 minutes

### Step 4: Test the Deployment

```bash
# Trigger a manual test run
gcloud scheduler jobs run gsr-automation-scheduler --location=us-central1

# Watch the Cloud Function logs
gcloud functions logs read trigger-gsr-automation --gen2 --region=us-central1 --limit=50

# Check if VM was created
gcloud compute instances list --filter='name~gsr-automation'

# Wait ~60-90 minutes for pipeline to complete (processes 10k+ tracking numbers)

# Check results in Cloud Storage
gsutil ls gs://void_automation/pipeline_runs/
```

---

## 📊 What Happens During Each Run

### 1. Cloud Scheduler Triggers (Every Other Day at 2:00 AM EST)
- Sends HTTP POST to Cloud Function

### 2. Cloud Function Creates VM
- VM name: `gsr-automation-runner-YYYYMMDD-HHMMSS`
- Machine type: `e2-medium` (2 vCPU, 4GB RAM)
- Preemptible: Yes (cheaper)
- Boot disk: 20GB Ubuntu 22.04 LTS

### 3. VM Startup Script Runs
- Installs GUI components (X11, XFCE, Xvfb) for headed browser mode
- Installs Python 3.10, Poetry, Playwright
- Clones repository from `dev` branch
- Fetches `.env` from Secret Manager
- Installs dependencies
- Runs: `make -C deployment/option1_persistent_vm pipeline-full`

### 4. Pipeline Executes (5 Steps)
- **Step 0:** IP whitelist via Slack API
- **Step 1:** Extract 10k+ tracking numbers from ClickHouse (85-89 days ago)
- **Step 2:** Extract 861 login credentials from PeerDB
- **Step 3:** Filter label-only shipments (88-89 days ago) → ~8 found
- **Step 4:** Automated UPS void (login, search, attempt dispute)

### 5. Results Uploaded to GCS
- CSV files (tracking numbers, results)
- JSON files (full API responses)
- PNG screenshots (browser automation)
- Log files (pipeline execution)

### 6. VM Self-Terminates
- Automatically deleted after pipeline completes

---

## 📁 Results Location

All results are uploaded to:
```
gs://void_automation/pipeline_runs/YYYY-MM-DD_HH-MM-SS/
├── step0_slack_whitelist/
├── step1_dlt_pipeline/
├── step2_peerdb_pipeline/
├── step3_label_filter/
│   ├── ups_label_only_tracking_range_*.csv
│   └── ups_label_only_filter_range_*.json
└── step4_void_automation/
    ├── ups_void_automation_results_*.csv
    └── *.png (screenshots)
```

---

## 🔧 Common Operations

### Pause Automation
```bash
gcloud scheduler jobs pause gsr-automation-scheduler --location=us-central1
```

### Resume Automation
```bash
gcloud scheduler jobs resume gsr-automation-scheduler --location=us-central1
```

### Manual Trigger
```bash
gcloud scheduler jobs run gsr-automation-scheduler --location=us-central1
```

### Update .env Credentials
```bash
# Update secret with new .env
gcloud secrets versions add gsr-automation-env --data-file=.env
```

### Change Schedule
```bash
# Example: Run every day instead of every other day
gcloud scheduler jobs update http gsr-automation-scheduler \
    --location=us-central1 \
    --schedule="0 2 * * *"
```

### Download Latest Results
```bash
# List all runs
gsutil ls gs://void_automation/pipeline_runs/

# Download specific run
gsutil -m cp -r gs://void_automation/pipeline_runs/2025-11-22_02-00-00/ ./results/
```

---

## 💰 Cost Estimate

| Component           | Usage                          | Monthly Cost |
| ------------------- | ------------------------------ | ------------ |
| **Compute Engine**  | 15 runs × 90 min × $0.033/hour | ~$0.75       |
| **Cloud Function**  | 15 invocations × $0.40/million | ~$0.01       |
| **Cloud Scheduler** | 1 job × $0.10/job              | $0.10        |
| **Cloud Storage**   | Already included               | $0.00        |
| **Secret Manager**  | 15 accesses × $0.03/10k        | ~$0.01       |
| **TOTAL**           |                                | **~$0.87/mo**|

**Savings:** $50-70/month (persistent VM) → **~95% cheaper!**

---

## ✅ Deployment Checklist

- [ ] Reviewed configuration in `deploy_ephemeral.sh`
- [ ] Ran `./deploy_ephemeral.sh` successfully
- [ ] Triggered test run
- [ ] Verified VM was created
- [ ] Waited for pipeline to complete (~60-90 min)
- [ ] Checked results in Cloud Storage
- [ ] Verified VM was deleted after completion
- [ ] Set up budget alerts (optional)

---

## 🎉 Success!

Your ephemeral VM deployment is now live! The pipeline will run automatically every other day at 2:00 AM EST.

**Next Steps:**
1. Monitor the first few scheduled runs
2. Review results in Cloud Storage
3. Adjust schedule if needed
4. Set up budget alerts
5. Delete the persistent VM `gsr-automation-vm` to save costs

