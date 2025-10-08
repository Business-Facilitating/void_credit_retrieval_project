# Google Cloud VM Deployment Guide

## 🚀 Deploying UPS Web Automation to Google Cloud VM (Linux)

This guide covers deploying the UPS web login automation to a Google Cloud VM running Linux.

---

## ⚠️ **Important: Headless Mode Limitation**

**UPS blocks headless browsers** with HTTP2 protocol errors. For reliable operation on a headless server, you have two options:

### **Option 1: Xvfb (Virtual Display) - ✅ RECOMMENDED**
- Runs browser in "headed" mode on a virtual display
- Most reliable, works exactly like local development
- Requires Xvfb installation

### **Option 2: Headless with Anti-Detection - ⚠️ EXPERIMENTAL**
- May not work due to UPS anti-bot measures
- Provided as `ups_web_login_headless.py`
- Use only if Xvfb is not an option

---

## 📋 **Prerequisites**

1. Google Cloud VM with:
   - **OS**: Ubuntu 20.04 LTS or newer (recommended)
   - **RAM**: Minimum 2GB (4GB recommended)
   - **Disk**: Minimum 10GB
   - **Firewall**: Outbound HTTPS (443) allowed

2. SSH access to the VM

3. Git installed on the VM

---

## 🔧 **Option 1: Deployment with Xvfb (Recommended)**

### **Step 1: Connect to Your VM**

```bash
# SSH into your Google Cloud VM
gcloud compute ssh YOUR_VM_NAME --zone=YOUR_ZONE

# Or use standard SSH
ssh username@VM_IP_ADDRESS
```

### **Step 2: Install System Dependencies**

```bash
# Update package list
sudo apt-get update

# Install Python 3.10+ and pip
sudo apt-get install -y python3 python3-pip python3-venv

# Install Xvfb (virtual display server)
sudo apt-get install -y xvfb

# Install Git
sudo apt-get install -y git

# Install Playwright system dependencies
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite0 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libxshmfence1
```

### **Step 3: Install Poetry**

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH (add to ~/.bashrc for persistence)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
poetry --version
```

### **Step 4: Clone and Setup Project**

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/gsr_automation.git
cd gsr_automation

# Install project dependencies
poetry install

# Install Playwright browsers
poetry run playwright install chromium

# Install Playwright system dependencies
poetry run playwright install-deps chromium
```

### **Step 5: Configure Environment Variables**

```bash
# Create .env file
nano .env

# Add your credentials (paste the following):
```

```env
# UPS Web Login Configuration
UPS_WEB_LOGIN_URL=https://www.ups.com/lasso/login
UPS_WEB_USERNAME=your_username
UPS_WEB_PASSWORD=your_password
```

Save and exit (Ctrl+X, then Y, then Enter)

### **Step 6: Create Xvfb Wrapper Script**

```bash
# Create wrapper script
nano run_with_xvfb.sh
```

Paste the following:

```bash
#!/bin/bash
# UPS Automation with Virtual Display

# Configuration
DISPLAY_NUM=99
SCREEN_RESOLUTION="1920x1080x24"
LOG_DIR="logs"

# Create log directory
mkdir -p "$LOG_DIR"

# Start Xvfb
echo "Starting virtual display :$DISPLAY_NUM..."
Xvfb :$DISPLAY_NUM -screen 0 $SCREEN_RESOLUTION > "$LOG_DIR/xvfb.log" 2>&1 &
XVFB_PID=$!

# Wait for Xvfb to start
sleep 2

# Export display variable
export DISPLAY=:$DISPLAY_NUM

# Run the automation
echo "Running UPS automation..."
poetry run python src/src/ups_web_login.py

# Capture exit code
EXIT_CODE=$?

# Kill Xvfb
echo "Stopping virtual display..."
kill $XVFB_PID 2>/dev/null

# Exit with same code as automation
exit $EXIT_CODE
```

Make it executable:

```bash
chmod +x run_with_xvfb.sh
```

### **Step 7: Test the Automation**

```bash
# Run the automation
./run_with_xvfb.sh

# Check the output
# Screenshots will be saved to data/output/
ls -lh data/output/
```

### **Step 8: Setup Cron Job (Optional)**

To run the automation on a schedule:

```bash
# Edit crontab
crontab -e

# Add a line to run daily at 2 AM (adjust as needed)
0 2 * * * cd /home/YOUR_USERNAME/gsr_automation && ./run_with_xvfb.sh >> logs/cron.log 2>&1
```

---

## 🔧 **Option 2: Headless Mode (Experimental)**

⚠️ **Warning**: This may not work due to UPS anti-bot measures. Use only if Xvfb is not an option.

### **Setup Steps**

Follow Steps 1-5 from Option 1, then:

```bash
# Run the headless version
poetry run python src/src/ups_web_login_headless.py
```

If you get HTTP2 protocol errors, you'll need to use Option 1 (Xvfb).

---

## 📊 **Verification**

### **Check if Automation Worked**

```bash
# Check screenshots
ls -lh data/output/

# View the latest screenshot
# (You'll need to download it to view)
```

### **Download Screenshots for Inspection**

```bash
# From your local machine
gcloud compute scp YOUR_VM_NAME:~/gsr_automation/data/output/*.png ./screenshots/ --zone=YOUR_ZONE

# Or use SCP
scp username@VM_IP:~/gsr_automation/data/output/*.png ./screenshots/
```

---

## 🐛 **Troubleshooting**

### **Issue: "Could not find browser"**

```bash
# Reinstall Playwright browsers
poetry run playwright install chromium
poetry run playwright install-deps chromium
```

### **Issue: "Display :99 not found"**

```bash
# Check if Xvfb is running
ps aux | grep Xvfb

# Kill any existing Xvfb processes
pkill Xvfb

# Try again
./run_with_xvfb.sh
```

### **Issue: "Permission denied"**

```bash
# Make sure script is executable
chmod +x run_with_xvfb.sh

# Check file permissions
ls -l run_with_xvfb.sh
```

### **Issue: "HTTP2 Protocol Error"**

This means headless mode is being blocked. Solutions:
1. Use Xvfb (Option 1) - **Recommended**
2. Try the headless version with anti-detection
3. Use a different approach (API instead of web scraping)

### **Issue: "Module not found"**

```bash
# Reinstall dependencies
poetry install

# Verify Python path
poetry run python -c "import sys; print(sys.path)"
```

---

## 📦 **Production Deployment Checklist**

- [ ] VM has sufficient resources (2GB+ RAM, 10GB+ disk)
- [ ] All system dependencies installed
- [ ] Poetry and project dependencies installed
- [ ] Playwright browsers installed
- [ ] `.env` file configured with credentials
- [ ] Xvfb wrapper script created and executable
- [ ] Test run successful
- [ ] Screenshots captured and verified
- [ ] Cron job configured (if needed)
- [ ] Logging configured
- [ ] Error notifications setup (optional)

---

## 🔒 **Security Best Practices**

1. **Protect `.env` file**:
   ```bash
   chmod 600 .env
   ```

2. **Use Google Secret Manager** (recommended):
   ```bash
   # Store secrets in Google Secret Manager
   gcloud secrets create ups-username --data-file=- <<< "your_username"
   gcloud secrets create ups-password --data-file=- <<< "your_password"
   
   # Retrieve in your script
   export UPS_WEB_USERNAME=$(gcloud secrets versions access latest --secret="ups-username")
   export UPS_WEB_PASSWORD=$(gcloud secrets versions access latest --secret="ups-password")
   ```

3. **Restrict VM access**:
   - Use firewall rules to limit inbound traffic
   - Use service accounts with minimal permissions
   - Enable OS Login for SSH access

4. **Rotate credentials regularly**

---

## 📈 **Monitoring and Logging**

### **Setup Logging**

```bash
# Create logs directory
mkdir -p logs

# Modify wrapper script to log output
./run_with_xvfb.sh >> logs/automation_$(date +%Y%m%d_%H%M%S).log 2>&1
```

### **Monitor with Google Cloud Logging**

```bash
# Install Google Cloud Logging agent
curl -sSO https://dl.google.com/cloudagents/add-logging-agent-repo.sh
sudo bash add-logging-agent-repo.sh --also-install
```

---

## 🚀 **Performance Optimization**

1. **Use Preemptible VMs** for cost savings (if automation can tolerate interruptions)

2. **Use Spot VMs** for even lower costs

3. **Schedule automation** during off-peak hours

4. **Clean up old screenshots**:
   ```bash
   # Add to cron to clean files older than 7 days
   find data/output -name "*.png" -mtime +7 -delete
   ```

---

## 📞 **Support**

If you encounter issues:

1. Check the logs in `logs/` directory
2. Verify screenshots in `data/output/`
3. Test locally first before deploying to cloud
4. Check Playwright documentation: https://playwright.dev/python/

---

## ✅ **Quick Start Commands**

```bash
# Complete setup in one go
sudo apt-get update && \
sudo apt-get install -y python3 python3-pip xvfb git && \
curl -sSL https://install.python-poetry.org | python3 - && \
export PATH="$HOME/.local/bin:$PATH" && \
cd gsr_automation && \
poetry install && \
poetry run playwright install chromium && \
poetry run playwright install-deps chromium && \
chmod +x run_with_xvfb.sh && \
./run_with_xvfb.sh
```

---

## 🎉 **Summary**

- ✅ Use **Xvfb** for reliable operation on Linux VMs
- ✅ Follow the step-by-step guide above
- ✅ Test thoroughly before production deployment
- ✅ Monitor logs and screenshots
- ✅ Secure your credentials properly

**The automation will work on Google Cloud VMs with proper setup!** 🚀

