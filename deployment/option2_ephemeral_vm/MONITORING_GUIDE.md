# Ephemeral VM Monitoring Guide

## 📊 Quick Status Check

### Check if VM is running:
```powershell
gcloud compute instances list --filter='name~gsr-automation-runner' --project=void-automation
```

### Check Cloud Scheduler status:
```powershell
gcloud scheduler jobs describe gsr-automation-scheduler --location=us-central1
```

---

## 🔍 Monitoring VM Execution

### 1. **View VM Serial Port Output (Real-time logs)**
```powershell
# Get latest output
gcloud compute instances get-serial-port-output gsr-automation-runner-YYYYMMDD-HHMMSS --zone=us-central1-a --project=void-automation

# Get output starting from specific line (to see only new logs)
gcloud compute instances get-serial-port-output gsr-automation-runner-YYYYMMDD-HHMMSS --zone=us-central1-a --project=void-automation --start=LINE_NUMBER
```

**What to look for:**
- ✅ `Installing Playwright dependencies...` - Dependencies installing
- ✅ `Cloning repository...` - Code downloading
- ✅ `Installing Poetry...` - Poetry setup
- ✅ `Running pipeline...` - Pipeline executing
- ✅ `Step 0: IP Whitelist` - Slack API working
- ✅ `Step 1: ClickHouse Extraction` - Data extraction
- ✅ `Step 2: PeerDB Credentials` - Login credentials loaded
- ✅ `Step 3: Label Filter` - Tracking numbers filtered
- ✅ `Step 4: Void Automation` - UPS website automation
- ✅ `Uploading results to GCS...` - Results uploaded
- ✅ `Deleting VM...` - VM auto-delete
- ❌ `E: Unable to locate package` - Package installation error
- ❌ `Script "startup-script" failed` - Startup script error

---

### 2. **View Cloud Function Logs**
```powershell
# View latest Cloud Function logs
gcloud functions logs read trigger-gsr-automation --gen2 --region=us-central1 --limit=50

# View logs with timestamps
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=trigger-gsr-automation" --limit=50 --format=json --project=void-automation
```

**What to look for:**
- ✅ `Creating VM: gsr-automation-runner-YYYYMMDD-HHMMSS` - VM creation started
- ✅ `VM created successfully` - VM created
- ❌ `Error creating VM` - VM creation failed

---

### 3. **Check GCS Results**
```powershell
# List all pipeline runs
gsutil ls gs://void_automation/pipeline_runs/

# List specific run results
gsutil ls gs://void_automation/pipeline_runs/YYYYMMDD_HHMMSS/

# Download specific file
gsutil cp gs://void_automation/pipeline_runs/YYYYMMDD_HHMMSS/step4_void_automation_results.csv ./

# Download all results from a run
gsutil -m cp -r gs://void_automation/pipeline_runs/YYYYMMDD_HHMMSS/ ./results/
```

---

## 🎯 Manual Trigger

### Trigger Cloud Scheduler manually:
```powershell
gcloud scheduler jobs run gsr-automation-scheduler --location=us-central1
```

### Wait 15 seconds, then check if VM was created:
```powershell
Start-Sleep -Seconds 15
gcloud compute instances list --filter='name~gsr-automation-runner' --project=void-automation
```

---

## 🛑 Emergency Stop

### Delete running VM:
```powershell
# List all running VMs
gcloud compute instances list --filter='name~gsr-automation-runner' --project=void-automation

# Delete specific VM
gcloud compute instances delete gsr-automation-runner-YYYYMMDD-HHMMSS --zone=us-central1-a --project=void-automation --quiet
```

### Pause Cloud Scheduler:
```powershell
gcloud scheduler jobs pause gsr-automation-scheduler --location=us-central1
```

### Resume Cloud Scheduler:
```powershell
gcloud scheduler jobs resume gsr-automation-scheduler --location=us-central1
```

---

## 📅 Schedule Management

### View next scheduled run:
```powershell
gcloud scheduler jobs describe gsr-automation-scheduler --location=us-central1
```

### Update schedule (example: change to daily at 11 PM EST):
```powershell
gcloud scheduler jobs update http gsr-automation-scheduler \
  --location=us-central1 \
  --schedule="0 23 * * *" \
  --time-zone="America/New_York"
```

---

## 🔧 Troubleshooting

### VM stuck or not auto-deleting:
```powershell
# Check VM status
gcloud compute instances describe gsr-automation-runner-YYYYMMDD-HHMMSS --zone=us-central1-a --project=void-automation

# Manually delete VM
gcloud compute instances delete gsr-automation-runner-YYYYMMDD-HHMMSS --zone=us-central1-a --project=void-automation --quiet
```

### Pipeline failed:
```powershell
# Check serial port output for errors
gcloud compute instances get-serial-port-output gsr-automation-runner-YYYYMMDD-HHMMSS --zone=us-central1-a --project=void-automation | grep -i "error\|failed"

# Check GCS for partial results
gsutil ls gs://void_automation/pipeline_runs/YYYYMMDD_HHMMSS/
```

### Cloud Function not triggering:
```powershell
# Check Cloud Function status
gcloud functions describe trigger-gsr-automation --gen2 --region=us-central1

# Check Cloud Scheduler status
gcloud scheduler jobs describe gsr-automation-scheduler --location=us-central1

# Manually trigger to test
gcloud scheduler jobs run gsr-automation-scheduler --location=us-central1
```

---

## 📊 Cost Monitoring

### Estimate costs:
- **Ephemeral VM (e2-medium, preemptible):** ~$0.01/hour
- **Pipeline runtime:** ~1.5 hours per run
- **Runs per month:** 15 (every other day)
- **Total VM cost:** ~$0.23/month
- **Cloud Function:** ~$0.10/month
- **Cloud Scheduler:** ~$0.10/month
- **GCS storage:** ~$0.02/month (for results)

**Total estimated cost:** ~$0.45/month 🎉

Compare to persistent VM: ~$50-70/month

**Savings:** ~99% cost reduction! 💰

---

## 🎉 Success Indicators

A successful pipeline run will:
1. ✅ Create VM in ~30 seconds
2. ✅ Install dependencies in ~5 minutes
3. ✅ Run pipeline in ~60-90 minutes
4. ✅ Upload results to GCS
5. ✅ Auto-delete VM
6. ✅ Leave results in `gs://void_automation/pipeline_runs/YYYYMMDD_HHMMSS/`

Check GCS for final results:
```powershell
gsutil ls gs://void_automation/pipeline_runs/ | Sort-Object -Descending | Select-Object -First 1
```

