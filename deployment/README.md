# GSR Automation - Deployment Guide

This folder contains all deployment configurations for running the GSR Automation pipeline on Google Cloud Platform.

---

## 📁 Folder Structure

```
deployment/
├── README.md                           # This file
├── DEPLOYMENT_COMPARISON.md            # Detailed comparison of both options
├── DEPLOYMENT_FILES_SUMMARY.md         # Summary of all deployment files
│
├── option1_persistent_vm/              # Option 1: Traditional persistent VM
│   ├── Makefile                        # Build automation commands
│   ├── crontab.txt                     # Cron job configuration
│   ├── gcp_vm_setup.sh                 # VM setup script
│   ├── run_pipeline_with_notifications.sh  # Enhanced pipeline runner
│   ├── DEPLOYMENT_QUICK_REFERENCE.md   # Quick start guide
│   ├── DEPLOYMENT_SUMMARY.md           # Overview
│   └── MAKEFILE_CRON_DEPLOYMENT.md     # Complete guide
│
└── option2_ephemeral_vm/               # Option 2: Ephemeral VM (Recommended) ⭐
    ├── deploy_ephemeral.sh             # One-command deployment script
    ├── gcp_ephemeral_vm_setup.sh       # Alternative standalone script
    ├── OPTION2_QUICK_START.md          # Quick start guide (START HERE!)
    ├── GCP_EPHEMERAL_VM_DEPLOYMENT.md  # Complete detailed guide
    └── cloud_function/                 # Cloud Function code
        ├── main.py                     # Function entry point
        ├── requirements.txt            # Python dependencies
        └── .env.yaml                   # Environment variables template
```

---

## 🎯 Which Option Should I Choose?

### Option 2: Ephemeral VM (Recommended) ⭐

**Choose this if you:**
- ✅ Run the pipeline **infrequently** (daily, every other day, weekly)
- ✅ Want **95% cost savings** (~$0.50-1/month vs ~$25-30/month)
- ✅ Prefer **zero maintenance** and auto-updates
- ✅ Want **serverless/managed** infrastructure
- ✅ Value **security** and isolation

**Cost:** ~$0.50-1/month  
**Setup Time:** 5-10 minutes  
**Maintenance:** Zero

👉 **Start here:** [option2_ephemeral_vm/OPTION2_QUICK_START.md](option2_ephemeral_vm/OPTION2_QUICK_START.md)

---

### Option 1: Persistent VM

**Choose this if you:**
- ✅ Run the pipeline **multiple times per day**
- ✅ Need **interactive debugging** frequently
- ✅ Have **other workloads** on the same VM
- ✅ Prefer **traditional** infrastructure

**Cost:** ~$25-30/month  
**Setup Time:** 30-60 minutes  
**Maintenance:** Manual updates required

👉 **Start here:** [option1_persistent_vm/DEPLOYMENT_QUICK_REFERENCE.md](option1_persistent_vm/DEPLOYMENT_QUICK_REFERENCE.md)

---

## 🚀 Quick Start - Option 2 (Recommended)

```bash
# 1. Navigate to option2 folder
cd deployment/option2_ephemeral_vm

# 2. Update configuration
nano deploy_ephemeral.sh  # Set PROJECT_ID and REPO_URL

# 3. Run deployment
chmod +x deploy_ephemeral.sh
./deploy_ephemeral.sh

# 4. Test it
gcloud scheduler jobs run gsr-automation-scheduler --location=us-central1

# 5. Check results
gsutil ls gs://gsr-automation-results/runs/
```

**Done!** Your pipeline now runs automatically every other day.

---

## 🚀 Quick Start - Option 1

```bash
# 1. Navigate to option1 folder
cd deployment/option1_persistent_vm

# 2. Copy Makefile to project root
cp Makefile ../../

# 3. On your GCP VM, run setup
make setup

# 4. Test the pipeline
make pipeline-full

# 5. Setup cron jobs
crontab -e  # Add jobs from crontab.txt
```

---

## 💰 Cost Comparison

| Feature | Option 1 | Option 2 |
|---------|----------|----------|
| **Monthly Cost** | ~$25-30 | ~$0.50-1 |
| **Annual Cost** | ~$300-360 | ~$6-12 |
| **Savings** | - | **95% cheaper** |
| **VM Uptime** | 24/7 | ~4 hours/month |
| **Maintenance** | Manual | Zero |

**For running every other day: Option 2 saves ~$300/year!**

---

## 📊 Architecture Comparison

### Option 1: Persistent VM
```
Persistent VM (24/7) → Cron → Pipeline → Local Storage
```

### Option 2: Ephemeral VM
```
Cloud Scheduler → Cloud Function → Create VM → Pipeline → Cloud Storage → Delete VM
```

---

## 📚 Documentation

### General
- [DEPLOYMENT_COMPARISON.md](DEPLOYMENT_COMPARISON.md) - Side-by-side comparison
- [DEPLOYMENT_FILES_SUMMARY.md](DEPLOYMENT_FILES_SUMMARY.md) - File descriptions

### Option 1 Documentation
- [Quick Reference](option1_persistent_vm/DEPLOYMENT_QUICK_REFERENCE.md)
- [Complete Guide](option1_persistent_vm/MAKEFILE_CRON_DEPLOYMENT.md)
- [Summary](option1_persistent_vm/DEPLOYMENT_SUMMARY.md)

### Option 2 Documentation
- [Quick Start](option2_ephemeral_vm/OPTION2_QUICK_START.md) ⭐ **Start here!**
- [Complete Guide](option2_ephemeral_vm/GCP_EPHEMERAL_VM_DEPLOYMENT.md)

---

## 🔧 Common Operations

### Option 2 (Ephemeral VM)

```bash
# Trigger manual run
gcloud scheduler jobs run gsr-automation-scheduler --location=us-central1

# View logs
gcloud functions logs read trigger-gsr-automation --gen2 --region=us-central1 --limit=50

# Download results
gsutil -m cp -r gs://gsr-automation-results/runs/$(gsutil ls gs://gsr-automation-results/runs/ | tail -1) ./results/

# Update credentials
gcloud secrets versions add gsr-automation-env --data-file=../../.env

# Pause automation
gcloud scheduler jobs pause gsr-automation-scheduler --location=us-central1

# Resume automation
gcloud scheduler jobs resume gsr-automation-scheduler --location=us-central1
```

### Option 1 (Persistent VM)

```bash
# Run pipeline
make pipeline-full

# View logs
make logs

# Check status
make status

# Clean old files
make clean-all
```

---

## 🎉 Recommendation

**For your use case (running every other day):**

# Use Option 2: Ephemeral VM ⭐

**Why:**
- ✅ **95% cost savings** ($25-30/month → $0.50-1/month)
- ✅ **Zero maintenance** (auto-fresh environment)
- ✅ **Better security** (Secret Manager, no persistent VM)
- ✅ **Easier setup** (one script does everything)
- ✅ **More scalable** (easy to add more accounts)

**Get started:** [option2_ephemeral_vm/OPTION2_QUICK_START.md](option2_ephemeral_vm/OPTION2_QUICK_START.md)

---

## 🐛 Troubleshooting

### Option 2 Issues

**Deployment fails:**
```bash
# Check gcloud authentication
gcloud auth list

# Verify project
gcloud config get-value project

# Check .env file exists
ls -la ../../.env
```

**Pipeline fails:**
```bash
# View VM logs
gcloud compute instances get-serial-port-output VM_NAME --zone=us-central1-a

# Check function logs
gcloud functions logs read trigger-gsr-automation --gen2 --region=us-central1
```

### Option 1 Issues

**Make commands fail:**
```bash
# Check dependencies
make check-deps

# Verify environment
make env-check
```

**Cron not running:**
```bash
# Check cron status
systemctl status cron

# View cron logs
grep CRON /var/log/syslog
```

---

## 📞 Support

For detailed troubleshooting, see:
- Option 2: [GCP_EPHEMERAL_VM_DEPLOYMENT.md](option2_ephemeral_vm/GCP_EPHEMERAL_VM_DEPLOYMENT.md)
- Option 1: [MAKEFILE_CRON_DEPLOYMENT.md](option1_persistent_vm/MAKEFILE_CRON_DEPLOYMENT.md)

---

**Ready to deploy?** Choose your option and follow the quick start guide! 🚀

