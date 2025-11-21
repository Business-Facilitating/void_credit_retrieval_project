# GSR Automation - Ephemeral VM Deployment Guide

**Author:** Gabriel Jerdhy Lapuz
**Project:** gsr_automation
**Last Updated:** 2025-11-20

---

## 📋 Overview

This guide shows how to deploy GSR Automation using **ephemeral VMs** on Google Cloud Platform. The system automatically creates a VM, runs your pipeline, and destroys the VM when complete.

### What This System Does

1. **Runs every other day** at 2:00 AM (configurable)
2. **Creates a fresh VM** when needed
3. **Runs 3-step pipeline:**
   - Step 1: Extract carrier invoice data from ClickHouse (85-89 days ago)
   - Step 2: Filter tracking numbers with label-only status (88-89 days ago)
   - Step 3: Automated UPS shipment void with dispute form filling
4. **Saves results** to Cloud Storage
5. **Deletes the VM** automatically
6. **Costs ~$0.50-1/month** instead of $25-30/month for persistent VM

### Cost Comparison

| Approach                                             | Monthly Cost      |
| ---------------------------------------------------- | ----------------- |
| **Persistent VM (e2-medium, 24/7)**                  | ~$25-30/month     |
| **Ephemeral VM (e2-medium, 15 min every other day)** | ~$0.50-1/month    |
| **Savings**                                          | **~95% cheaper!** |

---

## 🏗️ Architecture

```
Cloud Scheduler (Every other day at 2:00 AM)
    ↓
Cloud Function (trigger-gsr-automation)
    ↓
Create Compute Engine VM (ephemeral)
    ↓
VM Startup Script:
    1. Install GUI components (X11, XFCE desktop, Xvfb)
    2. Install dependencies (Python, Poetry, Playwright)
    3. Configure X11 display server for headed browser mode
    4. Clone GitHub repository
    5. Fetch .env from Secret Manager
    6. Install project dependencies
    7. Run pipeline: make pipeline-full
       ├── Step 1: dlt_pipeline_examples.py (ClickHouse extraction)
       ├── Step 2: ups_label_only_filter.py (Label-only filter)
       └── Step 3: ups_shipment_void_automation.py (UPS void automation)
    6. Upload results to Cloud Storage
    7. Signal completion
    ↓
VM Self-Terminates
    ↓
Results stored in Cloud Storage bucket
```

---

## 🚀 Quick Start (5 Steps)

### Prerequisites

- GCP project with billing enabled
- `gcloud` CLI installed and authenticated
- GitHub repository with your gsr_automation code
- `.env` file with all required credentials

### Step 1: Update Configuration

Edit `deploy_ephemeral.sh` and update these values:

```bash
PROJECT_ID="your-gcp-project-id"              # Your GCP project
REPO_URL="https://github.com/YOUR_USERNAME/gsr_automation.git"  # Your repo
```

### Step 2: Verify .env File

Ensure your `.env` file has all required credentials:

```bash
# Check if .env exists
ls -la .env

# Required variables:
# - CLICKHOUSE_HOST
# - CLICKHOUSE_PORT
# - CLICKHOUSE_USERNAME
# - CLICKHOUSE_PASSWORD
# - CLICKHOUSE_DATABASE
# - UPS_USERNAME
# - UPS_PASSWORD
# - UPS_WEB_USERNAME
# - UPS_WEB_PASSWORD
# - PEERDB_HOST
# - PEERDB_PORT
# - PEERDB_USERNAME
# - PEERDB_PASSWORD
# - PEERDB_DATABASE
```

### Step 3: Commit and Push to GitHub

The ephemeral VM will clone your repository, so make sure all changes are pushed:

```bash
git add .
git commit -m "Update deployment configuration"
git push origin main
```

### Step 4: Run Deployment Script

```bash
# Navigate to deployment folder
cd deployment/option2_ephemeral_vm

# Make script executable
chmod +x deploy_ephemeral.sh

# Run deployment (takes ~5-10 minutes)
./deploy_ephemeral.sh
```

The script will:

- ✅ Enable required GCP APIs
- ✅ Create service account with permissions
- ✅ Store .env in Secret Manager
- ✅ Create Cloud Storage bucket
- ✅ Deploy Cloud Function
- ✅ Create Cloud Scheduler job

### Step 5: Test the Setup

```bash
# Trigger a manual test run
gcloud scheduler jobs run gsr-automation-scheduler --location=us-central1

# Watch the Cloud Function logs
gcloud functions logs read trigger-gsr-automation --gen2 --region=us-central1 --limit=50

# Check if VM was created
gcloud compute instances list --filter='name~gsr-automation'

# Wait ~10-20 minutes for pipeline to complete

# Check results in Cloud Storage
gsutil ls gs://gsr-automation-results/runs/

# Download latest results
gsutil -m cp -r gs://gsr-automation-results/runs/$(gsutil ls gs://gsr-automation-results/runs/ | tail -1) ./results/
```

---

## 🖥️ Using Non-Headless VM (With Display)

By default, the VM runs in headless mode (no display). If you want to use a VM with a display for debugging or monitoring:

### Option A: Use VNC Server (Recommended)

Edit `gcp_ephemeral_vm_setup.sh` and add VNC server installation:

```bash
# Install VNC server
sudo apt-get install -y tightvncserver

# Start VNC server
vncserver :1 -geometry 1920x1080 -depth 24

# Set VNC password (optional)
echo "your_password" | vncpasswd -f > ~/.vnc/passwd
chmod 600 ~/.vnc/passwd
```

Then connect using a VNC client:

```bash
# Create SSH tunnel
gcloud compute ssh gsr-automation-runner-TIMESTAMP \
    --zone=us-central1-a \
    --ssh-flag="-L 5901:localhost:5901"

# Connect VNC client to localhost:5901
```

### Option B: Use Chrome Remote Desktop

1. Install Chrome Remote Desktop on the VM
2. Follow GCP's Chrome Remote Desktop setup guide
3. Connect via browser

### Option C: Use X11 Forwarding (For Testing Only)

```bash
# SSH with X11 forwarding
gcloud compute ssh gsr-automation-runner-TIMESTAMP \
    --zone=us-central1-a \
    --ssh-flag="-X"

# Run script with visible browser
cd /opt/gsr_automation
poetry run python src/src/ups_shipment_void_automation.py --headed
```

---

## 🖥️ Headed Mode Configuration (GUI-Enabled VMs)

### Overview

The deployment is configured to run browser automation in **headed mode** (visible browser with GUI) instead of traditional headless mode. This configuration provides better reliability for UPS shipment void automation.

### Why Headed Mode?

- ✅ **Better compatibility** with UPS website automation
- ✅ **Improved reliability** for complex web interactions
- ✅ **Easier debugging** when issues occur
- ✅ **More realistic browser behavior** reduces detection risk

### How It Works

1. **VM Provisioning**: The ephemeral VM is created with GUI support

   - Installs X11 display server (Xorg)
   - Installs XFCE desktop environment
   - Installs Xvfb (virtual framebuffer) for virtual display

2. **Display Configuration**: On VM startup

   - Starts Xvfb on display `:0` with 1920x1080 resolution
   - Starts XFCE window manager for proper window handling
   - Sets `DISPLAY=:0` environment variable

3. **Browser Automation**: UPS void automation runs with `--headed` flag
   - Browser windows are created on the virtual display
   - All interactions are visible (though not to human eyes)
   - Screenshots are captured for debugging

### Technical Details

**Installed Components:**

- `xserver-xorg` - X11 display server
- `x11-xserver-utils` - X11 utilities (including xdpyinfo)
- `xfce4` - Lightweight desktop environment
- `xfce4-terminal` - Terminal emulator
- `dbus-x11` - D-Bus session for X11
- `x11vnc` - VNC server (optional, for remote viewing)
- `xvfb` - Virtual framebuffer X server

**Display Configuration:**

```bash
# Display server runs on :0
export DISPLAY=:0

# Xvfb configuration
Xvfb :0 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset
```

**Browser Launch:**

```python
# Browser runs in headed mode (non-headless)
browser = playwright.chromium.launch(
    headless=False,  # Headed mode enabled
    args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ],
)
```

### Cost Impact

Headed mode has minimal cost impact:

- **Additional packages**: ~100MB extra disk space
- **Runtime overhead**: ~50-100MB extra RAM usage
- **VM cost**: Same as before (~$0.50-1/month)

The e2-medium instance (2 vCPU, 4GB RAM) has sufficient resources for headed mode.

### Debugging Headed Mode

If you need to view the browser during execution:

**Option 1: VNC Access (Recommended)**

```bash
# On the VM, start VNC server
x11vnc -display :0 -bg -nopw -listen localhost -xkb

# Create SSH tunnel from your local machine
gcloud compute ssh gsr-automation-runner-TIMESTAMP \
    --zone=us-central1-a \
    --ssh-flag="-L 5900:localhost:5900"

# Connect VNC client to localhost:5900
```

**Option 2: Screenshots**
The automation automatically saves screenshots to `data/output/` directory, which are uploaded to Cloud Storage after pipeline completion.

### Switching Back to Headless Mode

If you need to switch back to headless mode:

1. **Update Makefile** (`deployment/option1_persistent_vm/Makefile`):

   ```makefile
   # Change line 181 from:
   $(POETRY_RUN) $(SCRIPT_VOID_AUTOMATION) --headed
   # To:
   $(POETRY_RUN) $(SCRIPT_VOID_AUTOMATION) --headless
   ```

2. **Simplify VM Setup** (optional):
   - Remove GUI packages from startup script
   - Keep only Xvfb for headless operation

**Note:** Current configuration uses headed mode because it provides better reliability for UPS automation.

---

## 🔧 Configuration

### Pipeline Date Ranges

The pipeline uses separate date range configurations for each step:

**Step 1 (ClickHouse Extraction):**

- Environment variables: `DLT_PIPELINE_START_DAYS=89`, `DLT_PIPELINE_END_DAYS=85`
- Date range: 85-89 days ago (5-day window)
- Example: August 13-17, 2025

**Step 2 (UPS Tracking Filter):**

- Environment variables: `UPS_FILTER_START_DAYS=89`, `UPS_FILTER_END_DAYS=88`
- Date range: 88-89 days ago (2-day window)
- Example: August 13-14, 2025

Both steps filter based on the `transaction_date` column.

### Submit Flag Behavior

**Default Configuration (Safe):**

```makefile
$(POETRY_RUN) $(SCRIPT_VOID_AUTOMATION) --headless
```

This will:

- ✅ Fill out all dispute forms
- ✅ Take screenshots
- ❌ **NOT submit** the forms

**To Enable Auto-Submit:**

Edit `deployment/option1_persistent_vm/Makefile` (line 165):

```makefile
$(POETRY_RUN) $(SCRIPT_VOID_AUTOMATION) --headless --submit
```

Then commit and push the change.

### Schedule Options

```bash
# Every other day at 2:00 AM (default)
--schedule="0 2 */2 * *"

# Every day at 2:00 AM
--schedule="0 2 * * *"

# Every Monday and Thursday at 2:00 AM
--schedule="0 2 * * 1,4"

# Every 3 days at 2:00 AM
--schedule="0 2 */3 * *"

# First day of every month at 2:00 AM
--schedule="0 2 1 * *"
```

To change schedule:

```bash
gcloud scheduler jobs update http gsr-automation-scheduler \
    --location=us-central1 \
    --schedule="0 2 * * *"
```

---

## 📊 Monitoring

### View Logs

```bash
# Cloud Function logs
gcloud functions logs read trigger-gsr-automation \
    --gen2 \
    --region=us-central1 \
    --limit=50

# List all VMs (including running ones)
gcloud compute instances list --filter='name~gsr-automation'

# Get VM serial output (while running)
gcloud compute instances get-serial-port-output VM_NAME \
    --zone=us-central1-a
```

### Download Results

```bash
# List all runs
gsutil ls gs://gsr-automation-results/runs/

# Download specific run
gsutil -m cp -r gs://gsr-automation-results/runs/20251111_020000/ ./results/

# Download latest run
LATEST=$(gsutil ls gs://gsr-automation-results/runs/ | tail -1)
gsutil -m cp -r $LATEST ./results/
```

### Set Up Budget Alerts

```bash
gcloud billing budgets create \
    --billing-account=YOUR_BILLING_ACCOUNT \
    --display-name="GSR Automation Budget" \
    --budget-amount=5USD \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=90 \
    --threshold-rule=percent=100
```

---

## 🔧 Common Operations

### Pause/Resume Automation

```bash
# Pause (stop automatic runs)
gcloud scheduler jobs pause gsr-automation-scheduler --location=us-central1

# Resume
gcloud scheduler jobs resume gsr-automation-scheduler --location=us-central1
```

### Update .env Credentials

```bash
# Update secret with new .env
gcloud secrets versions add gsr-automation-env --data-file=.env
```

### Manual Trigger

```bash
# Run pipeline immediately
gcloud scheduler jobs run gsr-automation-scheduler --location=us-central1
```

---

## 🐛 Troubleshooting

### Issue: Deployment script fails

**Check:**

```bash
# Verify gcloud is installed and authenticated
gcloud auth list

# Verify project is set
gcloud config get-value project

# Check if .env file exists
ls -la .env
```

### Issue: Cloud Function fails to create VM

**Check:**

```bash
# View function logs
gcloud functions logs read trigger-gsr-automation --gen2 --region=us-central1 --limit=50

# Check service account permissions
gcloud projects get-iam-policy YOUR_PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:gsr-automation-runner"
```

### Issue: Pipeline fails on VM

**Check:**

```bash
# Get VM serial output
gcloud compute instances get-serial-port-output VM_NAME --zone=us-central1-a

# Check if .env secret is correct
gcloud secrets versions access latest --secret=gsr-automation-env
```

### Issue: No results in Cloud Storage

**Check:**

```bash
# Verify bucket exists
gsutil ls gs://gsr-automation-results/

# Check bucket permissions
gsutil iam get gs://gsr-automation-results/

# Check VM logs for upload errors
gcloud compute instances get-serial-port-output VM_NAME --zone=us-central1-a | grep "gsutil"
```

---

## 💰 Cost Breakdown

### Monthly Cost Estimate (Every Other Day)

| Component           | Usage                          | Cost             |
| ------------------- | ------------------------------ | ---------------- |
| **Compute Engine**  | 15 runs × 15 min × $0.033/hour | ~$0.25           |
| **Cloud Function**  | 15 invocations × $0.40/million | ~$0.01           |
| **Cloud Scheduler** | 1 job × $0.10/job              | $0.10            |
| **Cloud Storage**   | 5GB × $0.02/GB                 | $0.10            |
| **Secret Manager**  | 15 accesses × $0.03/10k        | ~$0.01           |
| **Network Egress**  | Minimal                        | ~$0.03           |
| **TOTAL**           |                                | **~$0.50/month** |

**Savings vs Persistent VM:** ~$25-30/month → **95% cheaper!**

---

## ✅ Deployment Checklist

- [ ] GCP project created with billing enabled
- [ ] `gcloud` CLI installed and authenticated
- [ ] `.env` file created with all required credentials
- [ ] All changes committed and pushed to GitHub
- [ ] Updated `PROJECT_ID` in `deploy_ephemeral.sh`
- [ ] Updated `REPO_URL` in `deploy_ephemeral.sh`
- [ ] Decided on submit flag behavior (default: no auto-submit)
- [ ] Tested pipeline locally (optional but recommended)
- [ ] Deployment script ran successfully
- [ ] Test run triggered and completed
- [ ] Results visible in Cloud Storage
- [ ] Budget alerts configured

---

## 📚 Project Summary

### Pipeline Steps

**Step 1: Extract Carrier Invoice Data**

- Script: `src/src/dlt_pipeline_examples.py`
- Extracts data from ClickHouse where `transaction_date` is 85-89 days ago
- Uses DLT (data load tool) for incremental loading
- Outputs: DuckDB file with carrier invoice data

**Step 2: Filter Label-Only Tracking Numbers**

- Script: `src/src/ups_label_only_filter.py`
- Filters tracking numbers where `transaction_date` is 88-89 days ago
- Uses UPS Tracking API to check status
- Filters for tracking numbers with exactly 1 activity: "Shipper created a label, UPS has not received the package yet."
- Outputs: CSV and JSON files with filtered tracking numbers

**Step 3: Automated UPS Shipment Void**

- Script: `src/src/ups_shipment_void_automation.py`
- Logs into UPS accounts using credentials from PeerDB
- Navigates to Billing Center
- Searches for tracking numbers from Step 2
- Fills out dispute forms (Void Credits + Package level)
- Takes screenshots of filled forms
- Optionally submits forms (controlled by `--submit` flag)

### Key Technologies

- **DLT (Data Load Tool):** Python framework for data pipelines
- **ClickHouse:** Cloud-hosted analytical database
- **DuckDB:** Embedded analytical database for local processing
- **Playwright:** Browser automation framework
- **PeerDB:** PostgreSQL database with UPS login credentials
- **Google Cloud Platform:** Cloud deployment platform
  - Compute Engine (ephemeral VMs)
  - Cloud Functions (serverless triggers)
  - Cloud Scheduler (cron jobs)
  - Secret Manager (credential storage)
  - Cloud Storage (result storage)

---

## 🎉 Summary

You now have a **fully automated, cost-effective** deployment that:

✅ Runs every other day (or your custom schedule)  
✅ Creates a fresh VM for each run  
✅ Executes the 3-step pipeline  
✅ Stores results in Cloud Storage  
✅ Deletes the VM after completion  
✅ Costs ~$0.50-1/month instead of ~$25-30/month

**Next Steps:**

1. Test the setup with a manual trigger
2. Monitor the first few scheduled runs
3. Adjust VM size and schedule as needed
4. Set up budget alerts
5. Decide if you want to enable `--submit` flag for auto-submission

---

**Questions or Issues?** Check the troubleshooting section or review Cloud Function/Scheduler logs.
