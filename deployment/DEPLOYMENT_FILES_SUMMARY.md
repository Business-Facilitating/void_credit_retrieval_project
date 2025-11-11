# GSR Automation - Deployment Files Summary

**Created:** 2025-10-30
**Purpose:** GCP deployment with two options: Persistent VM (cron) or Ephemeral VM (Cloud Scheduler)

---

## 🎯 Deployment Options

### Option 1: Persistent VM with Cron (Traditional)

- **Best for:** Frequent runs, complex workflows
- **Cost:** ~$25-30/month (VM running 24/7)
- **Files:** Makefile, crontab.txt

### Option 2: Ephemeral VM with Cloud Scheduler (Recommended) ⭐

- **Best for:** Infrequent runs (every other day), cost optimization
- **Cost:** ~$0.50-1/month (VM only when running)
- **Files:** gcp_ephemeral_vm_setup.sh, Cloud Scheduler configuration
- **Savings:** ~95% cheaper!

---

## 📁 Files Created

### 1. Core Automation Files

#### **Makefile** (Project Root)

- **Purpose:** Main automation file with all pipeline commands
- **Features:**
  - Setup and dependency checking
  - Pipeline execution (individual steps and full pipeline)
  - Testing commands
  - Monitoring and logging
  - Cleanup utilities
- **Key Commands:**
  - `make setup` - Install dependencies and setup
  - `make pipeline-full` - Run all 3 steps sequentially
  - `make status` - Show pipeline status
  - `make logs` - View recent logs
  - `make help` - Show all commands

#### **crontab.txt** (Project Root)

- **Purpose:** Cron job configuration examples and documentation
- **Contains:**
  - Multiple scheduling options (daily, multiple times, specific days)
  - Maintenance jobs (log cleanup, output cleanup)
  - Detailed documentation and best practices
  - Troubleshooting tips
- **Recommended Setup:**
  ```bash
  0 2 * * * cd /home/YOUR_USERNAME/gsr_automation && make pipeline-full >> logs/cron_pipeline_full.log 2>&1
  ```

---

### 2. Helper Scripts

#### **scripts/run_pipeline_with_notifications.sh**

- **Purpose:** Enhanced pipeline runner with error handling and notifications
- **Features:**
  - Sequential execution with error handling
  - Detailed logging with timestamps
  - Email notifications (optional)
  - Automatic cleanup
  - Status reporting
- **Usage:**
  ```bash
  chmod +x scripts/run_pipeline_with_notifications.sh
  ./scripts/run_pipeline_with_notifications.sh
  ```

#### **scripts/gcp_vm_setup.sh**

- **Purpose:** Automated setup script for GCP VMs
- **Features:**
  - Installs all system dependencies
  - Installs Poetry
  - Clones repository
  - Sets up project
  - Creates .env template
  - Makes scripts executable
- **Usage:**
  ```bash
  curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/gsr_automation/main/scripts/gcp_vm_setup.sh | bash
  ```

#### **scripts/README.md**

- **Purpose:** Documentation for scripts directory
- **Contains:**
  - Script descriptions
  - Usage instructions
  - Configuration details
  - Troubleshooting tips

---

### 3. Documentation Files

#### **docs/DEPLOYMENT_SUMMARY.md**

- **Purpose:** Complete deployment overview
- **Contains:**
  - Overview of all created files
  - Pipeline architecture diagram
  - File structure
  - Configuration details
  - Deployment steps
  - Monitoring and troubleshooting

#### **docs/MAKEFILE_CRON_DEPLOYMENT.md**

- **Purpose:** Detailed deployment guide
- **Contains:**
  - Complete Makefile commands reference
  - Cron job configuration options
  - Configuration details
  - Monitoring and troubleshooting
  - Security best practices
  - Performance optimization
  - Example workflows
  - Deployment checklist

#### **docs/DEPLOYMENT_QUICK_REFERENCE.md**

- **Purpose:** Quick reference card
- **Contains:**
  - One-time setup commands
  - Quick commands for daily operations
  - Cron job setup
  - Troubleshooting quick fixes
  - Pipeline steps overview
  - Important files reference
  - Checklists

#### **DEPLOYMENT_FILES_SUMMARY.md** (This File)

- **Purpose:** Summary of all deployment files created
- **Contains:**
  - List of all files
  - Purpose and features of each file
  - Quick start guide
  - File relationships

---

### 4. Updated Files

#### **README.md**

- **Added:** Deployment section with GCP VM instructions
- **Added:** Reference to deployment documentation
- **Added:** Quick start commands for deployment

---

## 🚀 Quick Start Guide

### For First-Time Setup on GCP VM

```bash
# Option 1: Use automated setup script
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/gsr_automation/main/scripts/gcp_vm_setup.sh | bash

# Option 2: Manual setup
sudo apt-get update
sudo apt-get install -y python3 python3-pip xvfb git
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
git clone YOUR_REPO_URL gsr_automation
cd gsr_automation
make setup
poetry run playwright install chromium
poetry run playwright install-deps chromium
```

### For Running the Pipeline

```bash
# Test individual steps
make test-step1
make test-step2
make test-step3

# Run full pipeline
make pipeline-full

# Run in background
make pipeline-full-bg

# Check status
make status

# View logs
make logs
```

### For Automated Scheduling

```bash
# Edit crontab
crontab -e

# Add this line (replace YOUR_USERNAME)
0 2 * * * cd /home/YOUR_USERNAME/gsr_automation && make pipeline-full >> logs/cron_pipeline_full.log 2>&1

# Verify
crontab -l
```

---

## 📊 File Relationships

```
Deployment Files Structure:

Makefile (Main automation)
    ├── Calls: src/src/dlt_pipeline_examples.py (Step 1)
    ├── Calls: src/src/ups_label_only_filter.py (Step 2)
    ├── Calls: src/src/ups_shipment_void_automation.py (Step 3)
    └── Uses: run_with_xvfb.sh (for Step 3)

crontab.txt (Scheduling)
    └── Schedules: make pipeline-full

scripts/run_pipeline_with_notifications.sh (Enhanced runner)
    └── Calls: make pipeline-step1, make pipeline-step2, make pipeline-step3

scripts/gcp_vm_setup.sh (Setup automation)
    ├── Installs: System dependencies
    ├── Installs: Poetry
    ├── Runs: make setup
    └── Creates: .env template

Documentation:
    ├── docs/DEPLOYMENT_SUMMARY.md (Overview)
    ├── docs/MAKEFILE_CRON_DEPLOYMENT.md (Detailed guide)
    ├── docs/DEPLOYMENT_QUICK_REFERENCE.md (Quick reference)
    └── DEPLOYMENT_FILES_SUMMARY.md (This file)
```

---

## 🎯 Pipeline Flow

```
Cron Job (Daily at 2:00 AM)
    ↓
make pipeline-full
    ↓
make pipeline-step1 → dlt_pipeline_examples.py → Extract from ClickHouse
    ↓ (Wait 60 seconds)
make pipeline-step2 → ups_label_only_filter.py → Filter label-only
    ↓ (Wait 120 seconds)
make pipeline-step3 → Xvfb + ups_web_login.py → UPS web login
    ↓
Output: logs/*.log, data/output/*.{csv,json,png}
```

---

## 📖 Documentation Hierarchy

1. **Quick Start:** `docs/DEPLOYMENT_QUICK_REFERENCE.md`
2. **Complete Guide:** `docs/MAKEFILE_CRON_DEPLOYMENT.md`
3. **Overview:** `docs/DEPLOYMENT_SUMMARY.md`
4. **This Summary:** `DEPLOYMENT_FILES_SUMMARY.md`
5. **Cron Examples:** `crontab.txt`
6. **Scripts Help:** `scripts/README.md`

---

## ✅ Deployment Checklist

Use this checklist to ensure complete deployment:

- [ ] All files created and in correct locations
- [ ] Makefile tested: `make help`
- [ ] Scripts made executable: `chmod +x scripts/*.sh`
- [ ] .env file created with credentials
- [ ] Dependencies installed: `make setup`
- [ ] Individual steps tested: `make test-step1`, `make test-step2`, `make test-step3`
- [ ] Full pipeline tested: `make pipeline-full`
- [ ] Cron jobs configured: `crontab -e`
- [ ] Logs verified: `make logs`
- [ ] Output files verified: `ls -l data/output/`
- [ ] Cleanup jobs scheduled
- [ ] Documentation reviewed

---

## 🔗 Related Files (Existing)

These existing files work with the new deployment setup:

- **run_with_xvfb.sh** - Xvfb wrapper for Step 3
- **src/src/dlt_pipeline_examples.py** - Step 1 script
- **src/src/ups_label_only_filter.py** - Step 2 script
- **src/src/ups_web_login.py** - Step 3 script
- **.env** - Environment variables (user must create)
- **docs/GOOGLE_CLOUD_DEPLOYMENT.md** - Existing GCP guide
- **docs/LINUX_DEPLOYMENT_SUMMARY.md** - Existing Linux guide

---

## 💡 Key Features

### Makefile

✅ Color-coded output  
✅ Error handling  
✅ Sequential execution with delays  
✅ Background execution support  
✅ Comprehensive logging  
✅ Cleanup utilities

### Cron Configuration

✅ Multiple scheduling options  
✅ Maintenance jobs  
✅ Detailed documentation  
✅ Best practices

### Helper Scripts

✅ Automated setup  
✅ Error handling  
✅ Email notifications  
✅ Status reporting

### Documentation

✅ Quick reference  
✅ Complete guide  
✅ Troubleshooting  
✅ Examples

---

## 📞 Support

For help with deployment:

1. **Quick answers:** See `docs/DEPLOYMENT_QUICK_REFERENCE.md`
2. **Detailed guide:** See `docs/MAKEFILE_CRON_DEPLOYMENT.md`
3. **Troubleshooting:** Run `make check-deps` and `make env-check`
4. **View logs:** Run `make logs`
5. **Check status:** Run `make status`

---

## 🎉 Summary

**Total Files Created:** 8 files

- 1 Makefile
- 1 Cron configuration file
- 3 Shell scripts
- 3 Documentation files
- 1 Summary file (this file)

**Total Files Updated:** 1 file

- README.md (added deployment section)

**Purpose:** Enable automated, scheduled execution of the 3-step GSR Automation pipeline on GCP Linux VMs with comprehensive monitoring, logging, and error handling.

**Status:** ✅ Ready for deployment

---

**Next Steps:** Follow the Quick Start Guide above to deploy on your GCP VM! 🚀
