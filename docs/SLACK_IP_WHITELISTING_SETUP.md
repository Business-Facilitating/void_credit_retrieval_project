# Slack IP Whitelisting Integration - Setup Summary

## ✅ Completed Changes

I've successfully integrated the Slack-based IP whitelisting step into your GSR Automation deployment pipeline. Here's what was done:

### 1. **Added `requests` Dependency**

- Updated `pyproject.toml` to include `requests (>=2.31.0,<3.0.0)`
- Required for making HTTP requests to the Slack API

### 2. **Updated `.env` Configuration**

- Added Slack configuration variables:
  ```bash
  SLACK_BOT_TOKEN=xoxb-1196297734070-9958913172178-qwmmXiyCUlZllamu2D2J41bN
  SLACK_WHITELIST_CHANNEL=C03B931H51A
  SLACK_WHITELIST_COMMAND_TEMPLATE=@G-bot ip_whitelist {ip}
  ```

### 3. **Updated Deployment Makefile**

- Added **Step 0** (IP whitelisting) to the pipeline
- Updated `pipeline-full` to run 5 steps instead of 4
- Added `pipeline-step0` target for manual execution
- Added `test-step0` target for testing
- Added `DELAY_AFTER_WHITELIST=10` timing configuration

### 4. **Deployment Scripts Already Compatible**

- Both ephemeral VM and persistent VM deployments use `make pipeline-full`
- No changes needed to the startup scripts - they'll automatically include Step 0

### 5. **Created Documentation**

- `docs/SLACK_IP_WHITELISTING.md` - Comprehensive guide for the IP whitelisting feature

---

## 🔧 Required Actions (You Need to Complete)

### **STEP 1: Configuration Complete ✅**

The Slack configuration has been updated with:

- **Slack Channel ID**: `C03B931H51A` (channel where G-bot is present)
- **Whitelisting Command**: `@G-bot ip_whitelist {ip}`
  - This will mention the G-bot user and use the `ip_whitelist` command
  - Example result: `@G-bot ip_whitelist 203.0.113.42`

### **STEP 2: Install Dependencies**

Install the new `requests` dependency:

```bash
poetry install
```

### **STEP 3: Test Locally (Optional but Recommended)**

Test the IP whitelisting step before deploying to GCP:

```bash
# Dry run (doesn't actually send to Slack)
poetry run python src/src/slack_whitelist_ip.py --dry-run

# Test with a specific IP (dry run)
poetry run python src/src/slack_whitelist_ip.py --ip 203.0.113.42 --dry-run

# Full test (sends actual Slack message to channel C03B931H51A)
# This will post: "@G-bot ip_whitelist <your-current-ip>"
make test-step0
```

### **STEP 4: Update Google Secret Manager**

For GCP deployment, update the secret with your updated `.env` file:

```bash
# Update the secret
gcloud secrets versions add gsr-automation-env --data-file=.env

# Verify the update
gcloud secrets versions access latest --secret=gsr-automation-env
```

---

## 📋 Pipeline Execution Order (Updated)

The full pipeline now executes in this order:

1. **Step 0**: 🔐 Whitelist VM IP via Slack ← **NEW**

   - Detects VM's public IPv4 address
   - Posts whitelisting command to Slack
   - Waits 10 seconds

2. **Step 1**: 🚀 Extract carrier invoice data from ClickHouse

   - Waits 60 seconds

3. **Step 2**: 📊 Extract industry index logins from PeerDB

   - Waits 60 seconds

4. **Step 3**: 🔍 Filter label-only tracking numbers

   - Waits 120 seconds

5. **Step 4**: 🌐 Automated UPS shipment void

---

## 🧪 Testing Commands

```bash
# Test only the IP whitelisting step
make test-step0

# Test the full pipeline (all 5 steps)
make pipeline-full

# Run individual steps
make pipeline-step0  # IP whitelisting
make pipeline-step1  # ClickHouse extraction
make pipeline-step2  # PeerDB extraction
make pipeline-step3  # Label filter
make pipeline-step4  # UPS void automation
```

---

## 📁 Files Modified

1. `pyproject.toml` - Added `requests` dependency
2. `.env` - Added Slack configuration (needs channel and command template)
3. `deployment/option1_persistent_vm/Makefile` - Added Step 0 to pipeline
4. `docs/SLACK_IP_WHITELISTING.md` - New documentation

---

## 🔍 Files Already Existing (No Changes Needed)

- `src/src/slack_whitelist_ip.py` - The IP whitelisting script (already existed!)
- `deployment/option2_ephemeral_vm/gcp_ephemeral_vm_setup.sh` - Uses `make pipeline-full`
- `deployment/option2_ephemeral_vm/cloud_function/main.py` - Uses `make pipeline-full`

---

## 🚀 Deployment Flow (Ephemeral VM)

```
Cloud Scheduler (every other day)
    ↓
Cloud Function triggered
    ↓
Create ephemeral VM
    ↓
Startup script runs
    ↓
Install dependencies (Poetry, Playwright, etc.)
    ↓
Fetch .env from Secret Manager
    ↓
Run: make pipeline-full
    ↓
    ├─ Step 0: Whitelist IP via Slack ← NEW
    ├─ Step 1: Extract from ClickHouse
    ├─ Step 2: Extract from PeerDB
    ├─ Step 3: Filter tracking numbers
    └─ Step 4: UPS void automation
    ↓
Upload results to Cloud Storage
    ↓
VM self-terminates
```

---

## ✅ Configuration Complete!

The Slack IP whitelisting is now fully configured:

- **Channel**: `C03B931H51A` (where G-bot is present)
- **Command**: `@G-bot ip_whitelist {ip}`
- **Example**: When the VM has IP `203.0.113.42`, the message will be: `@G-bot ip_whitelist 203.0.113.42`

You can now proceed with testing and deployment!

---

## 📚 Additional Resources

- Full documentation: `docs/SLACK_IP_WHITELISTING.md`
- Deployment guide: `docs/GOOGLE_CLOUD_DEPLOYMENT.md`
- Deployment comparison: `deployment/DEPLOYMENT_COMPARISON.md`
