# GSR Automation - Deployment Quick Reference Card

## 🚀 One-Time Setup (GCP Linux VM)

```bash
# 1. SSH into VM
gcloud compute ssh YOUR_VM_NAME --zone=YOUR_ZONE

# 2. Install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip xvfb git

# 3. Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

# 4. Clone and setup project
cd ~
git clone YOUR_REPO_URL gsr_automation
cd gsr_automation

# 5. Run setup
make setup

# 6. Install Playwright browsers
poetry run playwright install chromium
poetry run playwright install-deps chromium

# 7. Make scripts executable
chmod +x scripts/run_pipeline_with_notifications.sh
chmod +x run_with_xvfb.sh
```

---

## ⚡ Quick Commands

### Run Pipeline

```bash
# Run full pipeline (all 3 steps)
make pipeline-full

# Run in background
make pipeline-full-bg

# Run individual steps
make pipeline-step1  # Extract from ClickHouse
make pipeline-step2  # Filter label-only
make pipeline-step3  # UPS web login
```

### Monitor

```bash
# Show status
make status

# View logs
make logs

# View specific log
tail -f logs/pipeline_full_*.log
```

### Cleanup

```bash
# Clean old logs (>7 days)
make clean-logs

# Clean old output (>30 days)
make clean-output

# Clean all
make clean-all
```

---

## ⏰ Setup Cron Jobs

```bash
# Edit crontab
crontab -e

# Add this line (replace YOUR_USERNAME)
0 2 * * * cd /home/YOUR_USERNAME/gsr_automation && make pipeline-full >> logs/cron_pipeline_full.log 2>&1

# Add cleanup jobs
0 3 * * 0 cd /home/YOUR_USERNAME/gsr_automation && make clean-logs >> logs/cron_cleanup.log 2>&1
0 4 1 * * cd /home/YOUR_USERNAME/gsr_automation && make clean-output >> logs/cron_cleanup.log 2>&1

# Save and exit (Ctrl+X, Y, Enter)

# Verify cron jobs
crontab -l
```

---

## 🔍 Troubleshooting

### Check Dependencies

```bash
make check-deps
make env-check
```

### Test Individual Steps

```bash
make test-step1
make test-step2
make test-step3
```

### View Logs

```bash
# Recent logs
ls -lt logs/*.log | head -10

# View specific log
tail -100 logs/step1_dlt_pipeline_*.log

# Follow log in real-time
tail -f logs/cron_pipeline_full.log
```

### Check Cron

```bash
# List cron jobs
crontab -l

# Check cron service
sudo systemctl status cron

# View cron logs
grep CRON /var/log/syslog | tail -20
```

### Common Fixes

```bash
# Xvfb not found
sudo apt-get install -y xvfb

# Poetry not found
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"

# Playwright browser not found
poetry run playwright install chromium
poetry run playwright install-deps chromium

# Permission denied
chmod +x scripts/run_pipeline_with_notifications.sh
chmod 600 .env
```

---

## 📊 Pipeline Steps

| Step | Script | Duration | Description |
|------|--------|----------|-------------|
| 1 | `dlt_pipeline_examples.py` | ~2-5 min | Extract carrier invoice data from ClickHouse (85-89 days ago) |
| 2 | `ups_label_only_filter.py` | ~1-3 min | Filter tracking numbers with label-only status |
| 3 | `ups_web_login.py` | ~2-5 min | Automated UPS web login using PeerDB credentials |

**Total Duration:** ~5-15 minutes

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `Makefile` | Main automation commands |
| `crontab.txt` | Cron job examples and documentation |
| `scripts/run_pipeline_with_notifications.sh` | Enhanced pipeline runner |
| `.env` | Environment variables and credentials |
| `logs/` | Pipeline execution logs |
| `data/output/` | Pipeline output files (CSV, JSON, screenshots) |

---

## 🔒 Security Checklist

- [ ] `.env` file created with credentials
- [ ] `.env` file protected: `chmod 600 .env`
- [ ] Scripts executable: `chmod +x scripts/*.sh`
- [ ] Firewall rules configured
- [ ] Credentials rotated regularly
- [ ] Logs monitored for errors

---

## 📈 Monitoring Checklist

- [ ] Cron jobs installed: `crontab -l`
- [ ] Pipeline runs successfully: `make pipeline-full`
- [ ] Logs created: `ls -l logs/`
- [ ] Output files created: `ls -l data/output/`
- [ ] Cleanup jobs scheduled
- [ ] Status checked regularly: `make status`

---

## 🎯 Daily Operations

### Morning Check

```bash
# Check last night's run
make status

# View recent logs
make logs

# Check output files
ls -lth data/output/ | head -10
```

### Manual Run

```bash
# Run full pipeline
make pipeline-full

# Or run in background
make pipeline-full-bg

# Monitor progress
tail -f logs/pipeline_full_*.log
```

### Weekly Maintenance

```bash
# Clean old files
make clean-all

# Check disk usage
df -h
du -sh logs/ data/output/

# Verify cron jobs
crontab -l
```

---

## 📞 Quick Help

```bash
# Show all commands
make help

# Check status
make status

# View logs
make logs

# Test setup
make check-deps
make env-check
```

---

## 🔗 Related Documentation

- **Full Deployment Guide:** `docs/MAKEFILE_CRON_DEPLOYMENT.md`
- **GCP Deployment:** `docs/GOOGLE_CLOUD_DEPLOYMENT.md`
- **Linux Deployment:** `docs/LINUX_DEPLOYMENT_SUMMARY.md`
- **Cron Examples:** `crontab.txt`

---

## 💡 Pro Tips

1. **Always test before scheduling:**
   ```bash
   make test-step1
   make test-step2
   make test-step3
   ```

2. **Monitor first few runs:**
   ```bash
   tail -f logs/cron_pipeline_full.log
   ```

3. **Setup email notifications:**
   Edit `scripts/run_pipeline_with_notifications.sh` and set:
   ```bash
   ENABLE_EMAIL_NOTIFICATIONS=true
   EMAIL_TO="your-email@example.com"
   ```

4. **Use background mode for long runs:**
   ```bash
   make pipeline-full-bg
   ```

5. **Regular cleanup:**
   Schedule weekly log cleanup and monthly output cleanup

---

**Quick Start:** `make setup` → `make test-step1` → `make pipeline-full` → `crontab -e` 🚀

