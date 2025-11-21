# Headed Mode Configuration for GCP Ephemeral VMs

**Author:** Gabriel Jerdhy Lapuz  
**Project:** gsr_automation  
**Date:** 2025-11-20

---

## 📋 Overview

This document describes the headed (GUI-enabled) browser automation configuration for the GSR Automation ephemeral VM deployment on Google Cloud Platform.

## 🎯 What Changed

The deployment has been modified to run browser automation in **headed mode** instead of traditional headless mode. This means the browser runs with a visible GUI (on a virtual display) rather than in headless mode.

### Key Changes

1. **VM Configuration**: Added GUI/desktop environment support
2. **Startup Script**: Installs and configures X11 display server
3. **Browser Automation**: Runs with `--headed` flag instead of `--headless`
4. **Makefile**: Updated to use headed mode for Step 4 (UPS void automation)

---

## 🔧 Technical Implementation

### 1. GUI Components Installation

The VM startup script now installs:

```bash
# Desktop environment and display server
xserver-xorg          # X11 display server
x11-xserver-utils     # X11 utilities
xfce4                 # Lightweight desktop environment
xfce4-terminal        # Terminal emulator
dbus-x11              # D-Bus session for X11
x11vnc                # VNC server (for remote viewing)
xvfb                  # Virtual framebuffer X server
```

### 2. Display Server Configuration

On VM startup, the following happens:

```bash
# Set display environment variable
export DISPLAY=:0

# Create X11 socket directory
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix

# Start Xvfb virtual display
Xvfb :0 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &

# Start XFCE window manager
startxfce4 &
```

### 3. Browser Launch Configuration

The browser now launches in headed mode:

```python
browser = playwright.chromium.launch(
    headless=False,  # Headed mode enabled
    args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
    ],
)
```

### 4. Makefile Changes

**Before:**
```makefile
$(POETRY_RUN) $(SCRIPT_VOID_AUTOMATION) --headless
```

**After:**
```makefile
$(POETRY_RUN) $(SCRIPT_VOID_AUTOMATION) --headed
```

---

## ✅ Benefits of Headed Mode

1. **Better Compatibility**: More reliable with UPS website automation
2. **Improved Reliability**: Complex web interactions work better
3. **Easier Debugging**: Screenshots show actual browser state
4. **Realistic Behavior**: Reduces bot detection risk

---

## 💰 Cost Impact

**Minimal cost increase:**
- Additional disk space: ~100MB (GUI packages)
- Additional RAM usage: ~50-100MB (window manager)
- **Total VM cost: Still ~$0.50-1/month** (no change)

The e2-medium instance (2 vCPU, 4GB RAM) has sufficient resources.

---

## 🐛 Debugging and Monitoring

### View Browser During Execution (VNC)

```bash
# On the VM, start VNC server
x11vnc -display :0 -bg -nopw -listen localhost -xkb

# From your local machine, create SSH tunnel
gcloud compute ssh gsr-automation-runner-TIMESTAMP \
    --zone=us-central1-a \
    --ssh-flag="-L 5900:localhost:5900"

# Connect VNC client to localhost:5900
```

### Check Display Server Status

```bash
# Verify display is running
xdpyinfo -display :0

# Check Xvfb process
ps aux | grep Xvfb

# Check window manager
ps aux | grep xfce4
```

### View Logs

```bash
# Xvfb logs
cat /var/log/xvfb.log

# XFCE logs
cat /var/log/xfce4.log

# Pipeline logs
tail -f /var/log/gsr-automation-startup.log
```

---

## 🔄 Switching Back to Headless Mode

If needed, you can revert to headless mode:

### 1. Update Makefile

Edit `deployment/option1_persistent_vm/Makefile`:

```makefile
# Change from:
$(POETRY_RUN) $(SCRIPT_VOID_AUTOMATION) --headed

# To:
$(POETRY_RUN) $(SCRIPT_VOID_AUTOMATION) --headless
```

### 2. Simplify Startup Script (Optional)

Edit `deployment/option2_ephemeral_vm/cloud_function/main.py`:

- Remove GUI package installation (xfce4, xserver-xorg, etc.)
- Keep only Xvfb for virtual display
- Remove window manager startup

---

## 📁 Modified Files

1. `deployment/option2_ephemeral_vm/cloud_function/main.py`
   - Added GUI components installation
   - Added X11 display server configuration
   - Added window manager startup

2. `deployment/option1_persistent_vm/Makefile`
   - Changed `--headless` to `--headed` in pipeline-step4
   - Updated display configuration comments
   - Simplified Xvfb handling

3. `deployment/option2_ephemeral_vm/gcp_ephemeral_vm_setup.sh`
   - Added GUI components installation
   - Added X11 display server configuration

4. `deployment/option2_ephemeral_vm/README.md`
   - Added "Headed Mode Configuration" section
   - Updated architecture diagram
   - Added debugging instructions

5. `deployment/DEPLOYMENT_COMPARISON.md`
   - Added browser mode comparison row
   - Added note about headed mode

---

## 🚀 Deployment

No changes needed to your deployment process. Simply run:

```bash
cd deployment/option2_ephemeral_vm
./deploy_ephemeral.sh
```

The VM will automatically be configured for headed mode.

---

## ❓ FAQ

**Q: Will this work on a headless Linux server?**  
A: Yes! The browser runs on a virtual X11 display (Xvfb), so no physical monitor is needed.

**Q: Can I see the browser during execution?**  
A: Yes, using VNC (see "Debugging and Monitoring" section above).

**Q: Does this increase costs?**  
A: No, the cost remains ~$0.50-1/month. The e2-medium instance has sufficient resources.

**Q: Why headed mode instead of headless?**  
A: Headed mode provides better reliability for UPS automation and reduces bot detection risk.

---

**Questions or Issues?** Check the main README or review Cloud Function/Scheduler logs.

