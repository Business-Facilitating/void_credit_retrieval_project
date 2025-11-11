# GSR Automation - GCP Deployment Summary

## 📋 Overview

This document summarizes the deployment setup for running the GSR Automation pipeline on a Google Cloud Platform (GCP) Linux VM with automated scheduling.

**Created:** 2025-10-30  
**Author:** Gabriel Jerdhy Lapuz  
**Project:** gsr_automation

---

## 🎯 What Was Created

### 1. **Makefile** (Project Root)

A comprehensive automation file with commands for:
- **Setup:** `make setup`, `make check-deps`, `make env-check`
- **Pipeline Execution:** `make pipeline-step1`, `make pipeline-step2`, `make pipeline-step3`, `make pipeline-full`
- **Testing:** `make test-step1`, `make test-step2`, `make test-step3`
- **Monitoring:** `make status`, `make logs`
- **Cleanup:** `make clean-logs`, `make clean-output`, `make clean-all`

**Key Features:**
- Color-coded output for better readability
- Automatic Xvfb management for Step 3 (web automation)
- Sequential execution with configurable delays
- Background execution support
- Comprehensive error handling

### 2. **crontab.txt** (Project Root)

Cron job configuration file with:
- Multiple scheduling options (daily, multiple times per day, specific days)
- Maintenance jobs (log cleanup, output cleanup)
- Detailed documentation and examples
- Best practices and troubleshooting tips

**Recommended Cron Setup:**
```bash
# Run full pipeline daily at 2:00 AM
0 2 * * * cd /home/YOUR_USERNAME/gsr_automation && make pipeline-full >> logs/cron_pipeline_full.log 2>&1

# Clean old logs weekly
0 3 * * 0 cd /home/YOUR_USERNAME/gsr_automation && make clean-logs >> logs/cron_cleanup.log 2>&1

# Clean old output files monthly
0 4 1 * * cd /home/YOUR_USERNAME/gsr_automation && make clean-output >> logs/cron_cleanup.log 2>&1
```

### 3. **scripts/run_pipeline_with_notifications.sh**

Enhanced pipeline runner with:
- Comprehensive error handling
- Detailed logging with timestamps
- Email notifications (optional)
- Automatic cleanup
- Status reporting

**Usage:**
```bash
chmod +x scripts/run_pipeline_with_notifications.sh
./scripts/run_pipeline_with_notifications.sh
```

### 4. **Documentation**

- **`docs/MAKEFILE_CRON_DEPLOYMENT.md`** - Complete deployment guide
- **`docs/DEPLOYMENT_QUICK_REFERENCE.md`** - Quick reference card
- **`docs/DEPLOYMENT_SUMMARY.md`** - This file
- **`scripts/README.md`** - Scripts directory documentation

---

## 🚀 Pipeline Architecture

### Sequential Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    GSR Automation Pipeline                   │
└─────────────────────────────────────────────────────────────┘

Step 1: Extract Carrier Invoice Data (2-5 minutes)
├── Script: src/src/dlt_pipeline_examples.py
├── Source: ClickHouse database
├── Filter: transaction_date 85-89 days ago
├── Output: carrier_invoice_extraction.duckdb
└── Log: logs/step1_dlt_pipeline_TIMESTAMP.log

        ⏳ Wait 60 seconds

Step 2: Filter Label-Only Tracking Numbers (1-3 minutes)
├── Script: src/src/ups_label_only_filter.py
├── Source: DuckDB from Step 1
├── Filter: Label-only status (same date range)
├── Output: ups_label_only_tracking_*.csv, *.json
└── Log: logs/step2_label_filter_TIMESTAMP.log

        ⏳ Wait 120 seconds

Step 3: Automated UPS Web Login (2-5 minutes)
├── Script: src/src/ups_web_login.py
├── Source: PeerDB industry_index_logins table
├── Action: Login to UPS website, navigate to shipping history
├── Output: Screenshots (data/output/*.png)
└── Log: logs/step3_web_login_TIMESTAMP.log

┌─────────────────────────────────────────────────────────────┐
│              Total Duration: ~5-15 minutes                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 File Structure

```
gsr_automation/
├── Makefile                          # Main automation commands
├── crontab.txt                       # Cron job configuration
├── .env                              # Environment variables (create this)
├── run_with_xvfb.sh                  # Xvfb wrapper (existing)
│
├── scripts/
│   ├── run_pipeline_with_notifications.sh  # Enhanced runner
│   └── README.md                     # Scripts documentation
│
├── src/src/
│   ├── dlt_pipeline_examples.py      # Step 1: Extract from ClickHouse
│   ├── ups_label_only_filter.py      # Step 2: Filter label-only
│   └── ups_web_login.py              # Step 3: Web automation
│
├── logs/                             # Pipeline execution logs
│   ├── step1_dlt_pipeline_*.log
│   ├── step2_label_filter_*.log
│   ├── step3_web_login_*.log
│   ├── pipeline_full_*.log
│   └── cron_*.log
│
├── data/output/                      # Pipeline output files
│   ├── carrier_invoice_extraction.duckdb
│   ├── ups_label_only_tracking_*.csv
│   ├── ups_label_only_filter_*.json
│   └── *.png (screenshots)
│
└── docs/
    ├── MAKEFILE_CRON_DEPLOYMENT.md   # Complete deployment guide
    ├── DEPLOYMENT_QUICK_REFERENCE.md # Quick reference card
    ├── DEPLOYMENT_SUMMARY.md         # This file
    ├── GOOGLE_CLOUD_DEPLOYMENT.md    # GCP deployment guide
    └── LINUX_DEPLOYMENT_SUMMARY.md   # Linux deployment summary
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Date filtering (85-89 days ago)
DLT_TRANSACTION_START_CUTOFF_DAYS=89
DLT_TRANSACTION_END_CUTOFF_DAYS=85

# ClickHouse connection
CLICKHOUSE_HOST=your-host
CLICKHOUSE_PORT=8443
CLICKHOUSE_USERNAME=your-username
CLICKHOUSE_PASSWORD=your-password
CLICKHOUSE_DATABASE=peerdb
CLICKHOUSE_SECURE=True

# UPS credentials
UPS_WEB_USERNAME=your-ups-username
UPS_WEB_PASSWORD=your-ups-password
```

### Makefile Configuration

```makefile
# Timing (seconds)
DELAY_AFTER_PIPELINE := 60   # Wait after Step 1
DELAY_AFTER_FILTER := 120    # Wait after Step 2

# Xvfb settings
DISPLAY_NUM := 99
SCREEN_RESOLUTION := 1920x1080x24
```

---

## 🔧 Deployment Steps

### 1. Initial Setup (One-Time)

```bash
# SSH into GCP VM
gcloud compute ssh YOUR_VM_NAME --zone=YOUR_ZONE

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip xvfb git

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

# Clone project
git clone YOUR_REPO_URL gsr_automation
cd gsr_automation

# Run setup
make setup

# Install Playwright
poetry run playwright install chromium
poetry run playwright install-deps chromium

# Make scripts executable
chmod +x scripts/run_pipeline_with_notifications.sh
chmod +x run_with_xvfb.sh
```

### 2. Testing

```bash
# Test individual steps
make test-step1
make test-step2
make test-step3

# Test full pipeline
make pipeline-full
```

### 3. Schedule Automation

```bash
# Edit crontab
crontab -e

# Add cron jobs (see crontab.txt for examples)
0 2 * * * cd /home/YOUR_USERNAME/gsr_automation && make pipeline-full >> logs/cron_pipeline_full.log 2>&1

# Verify
crontab -l
```

---

## 📈 Monitoring

### Daily Checks

```bash
# Check status
make status

# View recent logs
make logs

# View specific log
tail -100 logs/cron_pipeline_full.log
```

### Weekly Maintenance

```bash
# Clean old files
make clean-all

# Check disk usage
df -h
du -sh logs/ data/output/
```

---

## 🔒 Security

- ✅ `.env` file protected: `chmod 600 .env`
- ✅ Scripts executable: `chmod +x scripts/*.sh`
- ✅ Credentials never committed to git
- ✅ Firewall rules configured
- ✅ Regular credential rotation

---

## 📊 Expected Output

### Step 1 Output
- **File:** `carrier_invoice_extraction.duckdb`
- **Contains:** Tracking numbers from 85-89 days ago
- **Size:** Varies (typically 10-100 MB)

### Step 2 Output
- **Files:** 
  - `ups_label_only_tracking_range_*.csv`
  - `ups_label_only_filter_range_*.json`
- **Contains:** Filtered tracking numbers with label-only status
- **Size:** Varies (typically 1-10 MB)

### Step 3 Output
- **Files:** `*.png` (screenshots)
- **Contains:** Screenshots of UPS website navigation
- **Size:** ~100-500 KB per screenshot

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Cron job doesn't run | Check PATH in crontab, verify cron service |
| Step 3 fails | Install Xvfb: `sudo apt-get install -y xvfb` |
| Permission denied | `chmod +x scripts/*.sh` and `chmod 600 .env` |
| Pipeline fails at step | Test individually: `make test-step1`, etc. |

### Debug Commands

```bash
# Check dependencies
make check-deps

# Validate environment
make env-check

# View detailed logs
tail -100 logs/step1_dlt_pipeline_*.log

# Check cron logs
grep CRON /var/log/syslog | tail -20
```

---

## ✅ Deployment Checklist

- [ ] GCP VM created and accessible
- [ ] System dependencies installed
- [ ] Poetry installed
- [ ] Project cloned
- [ ] `.env` file created with credentials
- [ ] `make setup` completed
- [ ] Playwright browsers installed
- [ ] Scripts made executable
- [ ] Individual steps tested
- [ ] Full pipeline tested
- [ ] Cron jobs configured
- [ ] Logs verified
- [ ] Output files verified
- [ ] Cleanup jobs scheduled
- [ ] Documentation reviewed

---

## 🎯 Success Criteria

✅ **Setup Complete When:**
- All `make test-step*` commands pass
- `make pipeline-full` completes successfully
- Output files created in `data/output/`
- Logs created in `logs/`
- Cron jobs listed in `crontab -l`

✅ **Production Ready When:**
- Pipeline runs successfully via cron
- Logs show no errors
- Output files generated daily
- Cleanup jobs running
- Monitoring in place

---

## 📞 Support Resources

- **Makefile Help:** `make help`
- **Quick Reference:** `docs/DEPLOYMENT_QUICK_REFERENCE.md`
- **Full Guide:** `docs/MAKEFILE_CRON_DEPLOYMENT.md`
- **GCP Guide:** `docs/GOOGLE_CLOUD_DEPLOYMENT.md`
- **Cron Examples:** `crontab.txt`

---

## 🎉 Summary

The GSR Automation pipeline is now fully configured for deployment on GCP Linux VMs with:

✅ **Automated Execution** - Makefile commands for all operations  
✅ **Scheduled Runs** - Cron job configurations  
✅ **Error Handling** - Comprehensive logging and notifications  
✅ **Monitoring** - Status and log viewing commands  
✅ **Maintenance** - Automatic cleanup of old files  
✅ **Documentation** - Complete guides and quick references  

**Next Steps:**
1. Complete initial setup on GCP VM
2. Test all pipeline steps
3. Configure cron jobs
4. Monitor first few runs
5. Setup regular maintenance

**The pipeline is ready for production deployment!** 🚀

