# GSR Automation - GCP Deployment Checklist

## Pre-Deployment Requirements

Before starting deployment, ensure you have:

- ✅ Code pushed to GitHub (`dev` branch)
- ⬜ GCP Project ID (need to update in `.env`)
- ⬜ GCP CLI (`gcloud`) installed and authenticated
- ⬜ Billing enabled on GCP project
- ⬜ Required GCP APIs enabled
- ⬜ Service account created with proper permissions
- ⬜ GCS bucket created (`gs://void_automation`)
- ⬜ `.env` file with all credentials ready
- ⬜ Secrets stored in GCP Secret Manager

---

## Step 1: GCP Project Setup

### 1.1 Verify GCP Project

```bash
# Check current project
gcloud config get-value project

# List all projects
gcloud projects list

# Set project (replace YOUR_PROJECT_ID)
gcloud config set project YOUR_PROJECT_ID
```

**Action Required**: What is your GCP Project ID?

---

### 1.2 Enable Required APIs

```bash
# Enable Compute Engine API
gcloud services enable compute.googleapis.com

# Enable Secret Manager API
gcloud services enable secretmanager.googleapis.com

# Enable Cloud Storage API
gcloud services enable storage.googleapis.com

# Enable Cloud Functions API (if using ephemeral deployment)
gcloud services enable cloudfunctions.googleapis.com

# Enable Cloud Scheduler API (if using ephemeral deployment)
gcloud services enable cloudscheduler.googleapis.com

# Verify enabled services
gcloud services list --enabled
```

**Estimated Time**: 2-3 minutes

---

## Step 2: Create Service Account

### 2.1 Create Service Account

```bash
# Create service account for GCS uploads
gcloud iam service-accounts create gsr-automation-uploader \
    --display-name="GSR Automation GCS Uploader" \
    --description="Service account for uploading pipeline outputs to GCS"
```

### 2.2 Grant Permissions

```bash
# Get your project ID
PROJECT_ID=$(gcloud config get-value project)

# Grant Storage Object Creator role (for GCS uploads)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:gsr-automation-uploader@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/storage.objectCreator"

# Grant Secret Manager Secret Accessor role (for reading .env)
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:gsr-automation-uploader@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Verify permissions
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:gsr-automation-uploader@${PROJECT_ID}.iam.gserviceaccount.com"
```

**Estimated Time**: 1-2 minutes

---

## Step 3: Create GCS Bucket

### 3.1 Create Bucket

```bash
# Create GCS bucket (replace REGION with your preferred region, e.g., us-central1)
gsutil mb -l us-central1 gs://void_automation

# Verify bucket creation
gsutil ls gs://void_automation
```

### 3.2 Set Lifecycle Policy (Optional - Auto-delete old files)

Create a file `lifecycle.json`:

```json
{
  "lifecycle": {
    "rule": [
      {
        "action": { "type": "Delete" },
        "condition": { "age": 90 }
      }
    ]
  }
}
```

Apply lifecycle policy:

```bash
gsutil lifecycle set lifecycle.json gs://void_automation
```

**Estimated Time**: 1 minute

---

## Step 4: Store Secrets in Secret Manager

### 4.1 Update .env File

First, update your `.env` file with the correct GCP Project ID:

```bash
# Edit .env file and update:
GCS_PROJECT_ID=YOUR_ACTUAL_PROJECT_ID
```

### 4.2 Create Secret

```bash
# Create secret from .env file
gcloud secrets create gsr-automation-env \
    --data-file=.env \
    --replication-policy="automatic"

# Verify secret creation
gcloud secrets describe gsr-automation-env

# Test reading secret (should show your .env content)
gcloud secrets versions access latest --secret="gsr-automation-env"
```

### 4.3 Grant Service Account Access to Secret

```bash
PROJECT_ID=$(gcloud config get-value project)

gcloud secrets add-iam-policy-binding gsr-automation-env \
    --member="serviceAccount:gsr-automation-uploader@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

**Estimated Time**: 2 minutes

---

## Step 5: Create VM Instance

### 5.1 Choose Deployment Option

**Option A: Ephemeral VM** (Recommended - VM created/destroyed per run)

- See `deployment/option2_ephemeral_vm/README.md`
- Requires Cloud Functions + Cloud Scheduler setup

**Option B: Persistent VM** (Simpler - VM runs continuously with cron)

- See below for setup

---

### 5.2 Create Persistent VM (Option B)

```bash
PROJECT_ID=$(gcloud config get-value project)

gcloud compute instances create gsr-automation-vm \
    --zone=us-central1-a \
    --machine-type=e2-standard-4 \
    --boot-disk-size=50GB \
    --boot-disk-type=pd-standard \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --service-account=gsr-automation-uploader@${PROJECT_ID}.iam.gserviceaccount.com \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --metadata=enable-oslogin=TRUE \
    --tags=gsr-automation
```

**VM Specifications**:

- Machine Type: `e2-standard-4` (4 vCPUs, 16 GB RAM)
- Disk: 50 GB SSD
- OS: Ubuntu 22.04 LTS
- Region: `us-central1-a` (change as needed)

**Estimated Time**: 3-5 minutes

---

## Step 6: Configure VM

### 6.1 SSH into VM

```bash
gcloud compute ssh gsr-automation-vm --zone=us-central1-a
```

### 6.2 Install Dependencies

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.10+
sudo apt-get install -y python3.10 python3.10-venv python3-pip

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Verify installations
python3 --version
poetry --version

# Install Git
sudo apt-get install -y git

# Install X11 for headed browser mode (Step 4)
sudo apt-get install -y xvfb x11vnc fluxbox
```

**Estimated Time**: 5-10 minutes

---

### 6.3 Clone Repository

```bash
# Clone repository
git clone https://github.com/Business-Facilitating/void_credit_retrieval_project.git
cd void_credit_retrieval_project

# Checkout dev branch
git checkout dev

# Verify you're on the correct branch
git branch
```

### 6.4 Load Environment Variables from Secret Manager

```bash
# Get project ID
PROJECT_ID=$(gcloud config get-value project)

# Download .env from Secret Manager
gcloud secrets versions access latest --secret="gsr-automation-env" > .env

# Verify .env file
head -5 .env
```

### 6.5 Install Python Dependencies

```bash
# Install dependencies using Poetry
poetry install

# Verify installation
poetry run python --version
poetry show
```

### 6.6 Install Playwright Browsers

```bash
# Install Playwright browsers for Step 4
poetry run playwright install chromium
poetry run playwright install-deps
```

**Estimated Time**: 5-10 minutes

---

## Step 7: Test the Pipeline

### 7.1 Test Individual Steps

```bash
# Test Step 0: IP Whitelisting
make test-step0

# Test Step 1: ClickHouse Extraction
make test-step1

# Test Step 2: PeerDB Extraction
make test-step2

# Test Step 3: Label Filter
make test-step3

# Test Step 4: Void Automation (requires X11)
# Start Xvfb first
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
make test-step4
```

### 7.2 Test GCS Upload

```bash
# Test GCS upload in dry-run mode
poetry run python src/src/gcs_upload.py --step 1 --files data/output/test.txt --dry-run

# Create test file
echo "Test data" > data/output/test.txt

# Test actual upload
poetry run python src/src/gcs_upload.py --step 1 --files data/output/test.txt

# Verify upload
gsutil ls gs://void_automation/pipeline_runs/
```

**Estimated Time**: 10-15 minutes

---

## Step 8: Run Full Pipeline

### 8.1 Set Up X11 Display (for Step 4)

```bash
# Start Xvfb (X Virtual Frame Buffer)
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &

# Set DISPLAY environment variable
export DISPLAY=:99

# Add to .bashrc for persistence
echo 'export DISPLAY=:99' >> ~/.bashrc
```

### 8.2 Run Full Pipeline

```bash
# Run full pipeline (all 5 steps)
make pipeline-full

# Monitor logs in real-time
tail -f logs/step*.log
```

### 8.3 Verify Results

```bash
# Check output files
ls -lh data/output/

# Check GCS uploads
gsutil ls -r gs://void_automation/pipeline_runs/

# Download results from GCS
gsutil cp gs://void_automation/pipeline_runs/LATEST_RUN/step4_void_automation/*.csv ./
```

**Estimated Time**: 30-60 minutes (depending on data volume)

---

## Step 9: Set Up Automated Runs (Optional)

### 9.1 Create Cron Job (Persistent VM)

```bash
# Edit crontab
crontab -e

# Add cron job to run every other day at 2 AM
0 2 */2 * * cd /home/YOUR_USERNAME/void_credit_retrieval_project && /home/YOUR_USERNAME/.local/bin/poetry run make pipeline-full >> /home/YOUR_USERNAME/pipeline.log 2>&1
```

### 9.2 Set Up Cloud Scheduler (Ephemeral VM)

See `deployment/option2_ephemeral_vm/README.md` for Cloud Functions + Cloud Scheduler setup.

**Estimated Time**: 5 minutes

---

## Step 10: Monitoring and Maintenance

### 10.1 Set Up Logging

```bash
# View recent logs
make logs

# Clean old logs (>7 days)
make clean-logs

# Monitor GCS bucket size
gsutil du -sh gs://void_automation/
```

### 10.2 Set Up Alerts (Optional)

Create Cloud Monitoring alerts for:

- VM CPU/Memory usage
- GCS upload failures
- Pipeline execution failures
- Disk space usage

### 10.3 Regular Maintenance

- **Weekly**: Review logs for errors
- **Monthly**: Check GCS bucket size and costs
- **Quarterly**: Update dependencies (`poetry update`)
- **As Needed**: Rotate credentials, update UPS API keys

---

## Troubleshooting

### Common Issues

**Issue 1: IP Whitelisting Fails**

```bash
# Check Slack bot token
grep SLACK_BOT_TOKEN .env

# Test Slack API manually
curl -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer YOUR_SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"channel":"C03B931H51A","text":"Test message"}'
```

**Issue 2: GCS Upload Fails**

```bash
# Check service account permissions
gcloud projects get-iam-policy $(gcloud config get-value project) \
  --flatten="bindings[].members" \
  --filter="bindings.members:gsr-automation-uploader"

# Test GCS access
gsutil ls gs://void_automation/
```

**Issue 3: Playwright/Browser Issues**

```bash
# Reinstall Playwright
poetry run playwright install --force chromium
poetry run playwright install-deps

# Check X11 display
echo $DISPLAY
ps aux | grep Xvfb
```

**Issue 4: Database Connection Fails**

```bash
# Check if IP is whitelisted
curl ifconfig.me

# Test ClickHouse connection
poetry run python -c "import clickhouse_connect; print('ClickHouse OK')"

# Test PeerDB connection
poetry run python -c "import psycopg2; print('PeerDB OK')"
```

---

## Deployment Summary

### Total Estimated Time

- **Initial Setup**: 30-45 minutes
- **First Pipeline Run**: 30-60 minutes
- **Total**: 1-2 hours

### Costs Estimate (Monthly)

- **VM (e2-standard-4, persistent)**: ~$120/month
- **GCS Storage (100 GB)**: ~$2/month
- **Secret Manager**: ~$0.06/month
- **Network Egress**: ~$5-10/month
- **Total**: ~$130-140/month

**Ephemeral VM** (recommended):

- **VM (e2-standard-4, 2 hours/day)**: ~$8/month
- **Cloud Functions**: ~$0.40/month
- **Cloud Scheduler**: ~$0.10/month
- **GCS + Other**: ~$7/month
- **Total**: ~$15-20/month (90% cost savings!)

---

## Next Steps

1. ✅ **Start with Step 1**: Verify GCP project and enable APIs
2. ✅ **Complete Steps 2-6**: Set up infrastructure
3. ✅ **Test Pipeline (Step 7)**: Verify each step works
4. ✅ **Run Full Pipeline (Step 8)**: Execute complete workflow
5. ✅ **Set Up Automation (Step 9)**: Schedule regular runs
6. ✅ **Monitor (Step 10)**: Set up logging and alerts

---

## Support Documentation

- **[PIPELINE_OVERVIEW.md](./PIPELINE_OVERVIEW.md)** - Complete pipeline overview
- **[PIPELINE_ERROR_HANDLING.md](./PIPELINE_ERROR_HANDLING.md)** - Error handling guide
- **[GCS_UPLOAD_SETUP.md](../docs/GCS_UPLOAD_SETUP.md)** - GCS upload setup
- **[SLACK_IP_WHITELISTING.md](../docs/SLACK_IP_WHITELISTING.md)** - Slack setup guide

---

**Ready to deploy!** 🚀

Start with Step 1 and work through each step sequentially. Good luck!
