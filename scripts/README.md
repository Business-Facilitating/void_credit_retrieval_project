# Scripts Directory

This directory contains helper scripts for running and managing the GSR Automation pipeline.

---

## 📁 Files

### `run_pipeline_with_notifications.sh`

Enhanced pipeline runner with comprehensive error handling, logging, and optional email notifications.

**Features:**
- Sequential execution of all 3 pipeline steps
- Comprehensive error handling (stops on first failure)
- Detailed logging with timestamps
- Email notifications on success/failure (optional)
- Automatic cleanup of old files
- Status reporting and summary generation

**Usage:**

```bash
# Make executable (first time only)
chmod +x scripts/run_pipeline_with_notifications.sh

# Run the pipeline
./scripts/run_pipeline_with_notifications.sh

# Or use from cron
0 2 * * * cd /home/YOUR_USERNAME/gsr_automation && ./scripts/run_pipeline_with_notifications.sh >> logs/cron_pipeline.log 2>&1
```

**Configuration:**

Edit the script to configure email notifications:

```bash
# Enable email notifications
ENABLE_EMAIL_NOTIFICATIONS=true
EMAIL_TO="your-email@example.com"
EMAIL_SUBJECT_PREFIX="[GSR Automation]"
```

**Requirements:**
- For email notifications: Install `mailutils` package
  ```bash
  sudo apt-get install -y mailutils
  ```

**Output:**
- Creates detailed log file: `logs/pipeline_run_TIMESTAMP.log`
- Sends email notifications (if enabled)
- Generates summary report with:
  - Execution status (SUCCESS/FAILED)
  - Duration in seconds
  - Count of output files created
  - Log file location

**Error Handling:**
- Stops execution if prerequisites check fails
- Stops execution if any step fails
- Sends failure notification with step number
- Includes detailed error information in logs

---

## 🔧 Adding New Scripts

When adding new scripts to this directory:

1. **Make them executable:**
   ```bash
   chmod +x scripts/your_script.sh
   ```

2. **Add shebang at the top:**
   ```bash
   #!/bin/bash
   ```

3. **Include documentation header:**
   ```bash
   # Script Name
   # Author: Your Name
   # Description: What this script does
   # Usage: How to run it
   ```

4. **Update this README** with script details

---

## 📖 Related Documentation

- **Makefile Commands:** See `Makefile` in project root
- **Cron Configuration:** See `crontab.txt` in project root
- **Deployment Guide:** See `docs/MAKEFILE_CRON_DEPLOYMENT.md`
- **Quick Reference:** See `docs/DEPLOYMENT_QUICK_REFERENCE.md`

---

## 💡 Tips

1. **Always test scripts locally before using in cron:**
   ```bash
   ./scripts/run_pipeline_with_notifications.sh
   ```

2. **Check script permissions:**
   ```bash
   ls -l scripts/
   ```

3. **View script logs:**
   ```bash
   tail -f logs/pipeline_run_*.log
   ```

4. **Use absolute paths in cron jobs:**
   ```bash
   0 2 * * * cd /home/YOUR_USERNAME/gsr_automation && ./scripts/run_pipeline_with_notifications.sh
   ```

---

## 🐛 Troubleshooting

### Script not executable

```bash
chmod +x scripts/run_pipeline_with_notifications.sh
```

### Script not found in cron

```bash
# Use absolute path
cd /home/YOUR_USERNAME/gsr_automation && ./scripts/run_pipeline_with_notifications.sh
```

### Email notifications not working

```bash
# Install mailutils
sudo apt-get install -y mailutils

# Test email
echo "Test" | mail -s "Test Subject" your-email@example.com
```

---

**For more information, see the main deployment documentation in `docs/`.**

