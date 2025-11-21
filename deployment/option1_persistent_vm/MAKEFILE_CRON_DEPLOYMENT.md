# Makefile and Cron Deployment Guide

## 📋 Overview

This guide explains how to deploy and run the GSR Automation pipeline on a Google Cloud Platform (GCP) Linux VM using the provided Makefile and cron job configurations.

The pipeline consists of four sequential steps:

1. **Step 1**: Extract carrier invoice data from ClickHouse (`dlt_pipeline_examples.py`)
2. **Step 2**: Extract industry index logins from PeerDB (`peerdb_pipeline.py`)
3. **Step 3**: Filter tracking numbers with label-only status (`ups_label_only_filter.py`)
4. **Step 4**: Perform automated UPS shipment void (`ups_shipment_void_automation.py`)

---

## 📁 Files Created

### Core Files

- **`Makefile`** - Main automation file with all pipeline commands
- **`crontab.txt`** - Cron job configuration examples and documentation
- **`scripts/run_pipeline_with_notifications.sh`** - Enhanced pipeline runner with error handling

### Documentation

- **`docs/MAKEFILE_CRON_DEPLOYMENT.md`** - This file

---

## 🚀 Quick Start

### 1. First-Time Setup

```bash
# SSH into your GCP VM
gcloud compute ssh YOUR_VM_NAME --zone=YOUR_ZONE

# Navigate to project directory
cd gsr_automation

# Run setup (installs dependencies, creates directories)
make setup

# Verify environment configuration
make env-check
```

### 2. Test Individual Steps

```bash
# Test Step 1: DLT Pipeline
make test-step1

# Test Step 2: Label Filter
make test-step2

# Test Step 3: Web Login (requires Xvfb)
make test-step3
```

### 3. Run Full Pipeline

```bash
# Run all 3 steps sequentially (foreground)
make pipeline-full

# Run all 3 steps in background
make pipeline-full-bg
```

### 4. Setup Automated Scheduling

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 2:00 AM
# (Replace YOUR_USERNAME with your actual username)
0 2 * * * cd /home/YOUR_USERNAME/gsr_automation && make pipeline-full >> logs/cron_pipeline_full.log 2>&1

# Save and exit
```

---

## 📖 Makefile Commands Reference

### Setup and Verification

| Command           | Description                                 |
| ----------------- | ------------------------------------------- |
| `make help`       | Show all available commands                 |
| `make setup`      | Install dependencies and create directories |
| `make check-deps` | Verify all dependencies are installed       |
| `make env-check`  | Validate environment configuration          |

### Pipeline Execution

| Command                 | Description                                        |
| ----------------------- | -------------------------------------------------- |
| `make pipeline-step1`   | Run Step 1: Extract carrier invoice data           |
| `make pipeline-step2`   | Run Step 2: Extract industry index logins (PeerDB) |
| `make pipeline-step3`   | Run Step 3: Filter label-only tracking numbers     |
| `make pipeline-step4`   | Run Step 4: Automated UPS shipment void            |
| `make pipeline-full`    | Run all 4 steps sequentially (foreground)          |
| `make pipeline-full-bg` | Run all 4 steps in background                      |

### Testing

| Command           | Description               |
| ----------------- | ------------------------- |
| `make test-step1` | Test Step 1 only          |
| `make test-step2` | Test Step 2 only (PeerDB) |
| `make test-step3` | Test Step 3 only          |
| `make test-step4` | Test Step 4 only          |

### Monitoring and Logging

| Command       | Description                          |
| ------------- | ------------------------------------ |
| `make logs`   | View recent pipeline logs            |
| `make status` | Show pipeline status and recent runs |

### Cleanup

| Command             | Description                            |
| ------------------- | -------------------------------------- |
| `make clean-logs`   | Remove log files older than 7 days     |
| `make clean-output` | Remove output files older than 30 days |
| `make clean-all`    | Run all cleanup tasks                  |

---

## ⏰ Cron Job Configuration

### Option 1: Run Full Pipeline Daily (Recommended)

```bash
# Run complete pipeline daily at 2:00 AM
0 2 * * * cd /home/YOUR_USERNAME/gsr_automation && make pipeline-full >> logs/cron_pipeline_full.log 2>&1
```

**Pros:**

- Simple, single cron job
- Makefile handles sequential execution and delays
- Easier to manage and monitor

**Cons:**

- Less granular control over timing

### Option 2: Run Individual Steps with Delays

```bash
# Step 1: Extract data (2:00 AM)
0 2 * * * cd /home/YOUR_USERNAME/gsr_automation && make pipeline-step1 >> logs/cron_step1.log 2>&1

# Step 2: Filter tracking numbers (2:05 AM)
5 2 * * * cd /home/YOUR_USERNAME/gsr_automation && make pipeline-step2 >> logs/cron_step2.log 2>&1

# Step 3: Web login (2:10 AM)
10 2 * * * cd /home/YOUR_USERNAME/gsr_automation && make pipeline-step3 >> logs/cron_step3.log 2>&1
```

**Pros:**

- More control over timing
- Separate logs for each step
- Can skip individual steps if needed

**Cons:**

- More cron jobs to manage
- No automatic error handling between steps

### Option 3: Multiple Runs Per Day

```bash
# Run every 6 hours (2 AM, 8 AM, 2 PM, 8 PM)
0 2,8,14,20 * * * cd /home/YOUR_USERNAME/gsr_automation && make pipeline-full >> logs/cron_pipeline_full.log 2>&1
```

### Option 4: Specific Days Only

```bash
# Run on Monday, Wednesday, Friday at 2:00 AM
0 2 * * 1,3,5 cd /home/YOUR_USERNAME/gsr_automation && make pipeline-full >> logs/cron_pipeline_full.log 2>&1
```

### Maintenance Jobs

```bash
# Clean old logs weekly (Sunday at 3:00 AM)
0 3 * * 0 cd /home/YOUR_USERNAME/gsr_automation && make clean-logs >> logs/cron_cleanup.log 2>&1

# Clean old output files monthly (1st at 4:00 AM)
0 4 1 * * cd /home/YOUR_USERNAME/gsr_automation && make clean-output >> logs/cron_cleanup.log 2>&1
```

---

## 🔧 Configuration

### Environment Variables

The pipeline uses environment variables from the `.env` file:

```bash
# Date filtering (used by Steps 1 and 2)
DLT_TRANSACTION_START_CUTOFF_DAYS=89
DLT_TRANSACTION_END_CUTOFF_DAYS=85

# ClickHouse connection
CLICKHOUSE_HOST=your-host
CLICKHOUSE_USERNAME=your-username
CLICKHOUSE_PASSWORD=your-password

# UPS credentials (for Step 3)
UPS_WEB_USERNAME=your-ups-username
UPS_WEB_PASSWORD=your-ups-password
```

### Makefile Configuration

You can customize timing in the `Makefile`:

```makefile
# Delay after Step 1 (seconds)
DELAY_AFTER_PIPELINE := 60

# Delay after Step 2 (seconds)
DELAY_AFTER_FILTER := 120

# Xvfb display number
DISPLAY_NUM := 99
```

---

## 📊 Monitoring and Troubleshooting

### View Pipeline Status

```bash
# Show recent runs and output files
make status

# View recent logs
make logs

# View specific log file
tail -f logs/pipeline_full_TIMESTAMP.log
```

### Check Cron Jobs

```bash
# List installed cron jobs
crontab -l

# View cron execution logs
grep CRON /var/log/syslog

# Check cron service status
sudo systemctl status cron
```

### Common Issues

#### Issue: Cron job doesn't run

**Solution:**

```bash
# Verify cron service is running
sudo systemctl status cron

# Check PATH includes poetry
which poetry

# Add poetry to PATH in crontab
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/home/YOUR_USERNAME/.local/bin
```

#### Issue: Step 3 fails with "Xvfb not found"

**Solution:**

```bash
# Install Xvfb
sudo apt-get install -y xvfb

# Verify installation
which Xvfb
```

#### Issue: Permission denied

**Solution:**

```bash
# Make scripts executable
chmod +x scripts/run_pipeline_with_notifications.sh

# Protect .env file
chmod 600 .env
```

#### Issue: Pipeline fails at specific step

**Solution:**

```bash
# Test individual steps
make test-step1
make test-step2
make test-step3

# Check logs for errors
tail -100 logs/step1_dlt_pipeline_*.log
```

---

## 🔒 Security Best Practices

1. **Protect credentials:**

   ```bash
   chmod 600 .env
   ```

2. **Use Google Secret Manager (recommended for production):**

   ```bash
   # Store secrets
   gcloud secrets create ups-username --data-file=- <<< "your_username"
   gcloud secrets create ups-password --data-file=- <<< "your_password"
   ```

3. **Restrict VM access:**

   - Use firewall rules
   - Enable OS Login
   - Use service accounts with minimal permissions

4. **Rotate credentials regularly**

---

## 📈 Performance Optimization

### Adjust Delays

If your pipeline runs faster/slower, adjust delays in `Makefile`:

```makefile
DELAY_AFTER_PIPELINE := 30   # Reduce if Step 1 is fast
DELAY_AFTER_FILTER := 60     # Reduce if Step 2 is fast
```

### Run in Background

For long-running pipelines:

```bash
make pipeline-full-bg
```

### Monitor Resource Usage

```bash
# CPU and memory
htop

# Disk usage
df -h
du -sh logs/ data/output/
```

---

## 📝 Example Workflows

### Daily Production Run

```bash
# Crontab entry
0 2 * * * cd /home/gsr/gsr_automation && make pipeline-full >> logs/cron_pipeline_full.log 2>&1
0 3 * * 0 cd /home/gsr/gsr_automation && make clean-logs >> logs/cron_cleanup.log 2>&1
```

### Testing and Development

```bash
# Test each step individually
make test-step1
make test-step2
make test-step3

# Run full pipeline once
make pipeline-full

# Check results
make status
```

### Manual Execution

```bash
# Run specific step
make pipeline-step1

# Run full pipeline in background
make pipeline-full-bg

# Monitor progress
tail -f logs/pipeline_full_*.log
```

---

## ✅ Deployment Checklist

- [ ] GCP VM created (Ubuntu 20.04+, 2GB+ RAM)
- [ ] SSH access configured
- [ ] Dependencies installed (Python, Poetry, Xvfb)
- [ ] Project cloned to VM
- [ ] `.env` file created with credentials
- [ ] `make setup` completed successfully
- [ ] `make env-check` passes
- [ ] Individual steps tested (`make test-step1`, etc.)
- [ ] Full pipeline tested (`make pipeline-full`)
- [ ] Cron jobs configured
- [ ] Logs verified
- [ ] Output files verified
- [ ] Cleanup jobs scheduled

---

## 🎯 Next Steps

1. **Complete initial setup:** `make setup`
2. **Test individual steps:** `make test-step1`, `make test-step2`, `make test-step3`
3. **Run full pipeline:** `make pipeline-full`
4. **Setup cron jobs:** `crontab -e`
5. **Monitor execution:** `make status`, `make logs`

---

## 📞 Support

For issues or questions:

1. Check logs: `make logs`
2. View status: `make status`
3. Test individual steps
4. Review this documentation
5. Check existing deployment guides in `docs/`

---

**The pipeline is ready for production deployment on GCP Linux VMs!** 🚀
