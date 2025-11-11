# Deployment Configuration Update Summary

## Overview

Updated all deployment configurations to use `ups_shipment_void_automation.py` instead of `ups_web_login.py` for Step 3 of the pipeline.

## Changes Made

### 1. Main Automation Script (`src/src/ups_shipment_void_automation.py`)

**Added `--submit` flag to control dispute form submission:**

- **Default behavior (without `--submit`)**: Fills out the dispute form but does NOT submit it
  - Selects "Void Credits" from Reason dropdown
  - Selects "Package" from Dispute Level dropdown
  - Takes screenshot of filled form
  - Keeps browser open for 10 seconds to review
  - Does NOT click Submit button

- **With `--submit` flag**: Fills out and submits the dispute form
  - Selects "Void Credits" from Reason dropdown
  - Selects "Package" from Dispute Level dropdown
  - Clicks Submit button
  - Waits 3 seconds for submission to process
  - Takes screenshot of submitted form

**Usage:**
```bash
# Fill form but don't submit (default)
poetry run python src/src/ups_shipment_void_automation.py --headed

# Fill form AND submit
poetry run python src/src/ups_shipment_void_automation.py --headed --submit
```

### 2. Deployment Files Updated

#### `deployment/option1_persistent_vm/Makefile`

**Changes:**
- Line 29: Changed `SCRIPT_WEB_LOGIN` to `SCRIPT_VOID_AUTOMATION`
- Line 29: Changed script path from `ups_web_login.py` to `ups_shipment_void_automation.py`
- Line 67: Updated help text from "Automated UPS web login" to "Automated UPS shipment void"
- Line 74: Updated test help text from "Web login with Xvfb" to "Void automation with Xvfb"
- Line 155: Updated step 3 title from "Automated UPS Web Login" to "Automated UPS Shipment Void"
- Line 165: Changed script call from `$(SCRIPT_WEB_LOGIN)` to `$(SCRIPT_VOID_AUTOMATION) --headless`
- Line 165: Updated log filename from `step3_web_login_*.log` to `step3_void_automation_*.log`
- Line 193: Updated step 3 description from "Running automated UPS web login" to "Running automated UPS shipment void"
- Line 225: Updated test step 3 description from "Web Login" to "Void Automation"

**Note:** The Makefile runs the script with `--headless` flag by default (no `--submit` flag), so it will fill forms but NOT submit them automatically.

#### `deployment/option1_persistent_vm/MAKEFILE_CRON_DEPLOYMENT.md`

**Changes:**
- Line 10: Updated Step 3 description from `ups_web_login.py` to `ups_shipment_void_automation.py`

#### `deployment/option1_persistent_vm/run_pipeline_with_notifications.sh`

**Changes:**
- Line 108: Updated warning message from "Step 3 (web login) will fail" to "Step 3 (void automation) will fail"
- Line 234: Updated step 3 name from "Automated UPS Web Login" to "Automated UPS Shipment Void"
- Line 239: Updated email notification from "Step 3 (Web Login) failed" to "Step 3 (Void Automation) failed"

#### `deployment/DEPLOYMENT_FILES_SUMMARY.md`

**Changes:**
- Line 226: Updated Makefile calls from `ups_web_login.py` to `ups_shipment_void_automation.py`

#### `docs/GOOGLE_CLOUD_DEPLOYMENT.md`

**Changes:**
- Line 173: Updated script call from `ups_web_login.py` to `ups_shipment_void_automation.py --headless`

## Pipeline Workflow (Updated)

### Step 1: Extract Carrier Invoice Data
- Script: `src/src/dlt_pipeline_examples.py`
- Extracts data from ClickHouse where transaction_date is 80-85 days ago

### Step 2: Filter Label-Only Tracking Numbers
- Script: `src/src/ups_label_only_filter.py`
- Filters tracking numbers with only "Shipper created a label, UPS has not received the package yet" status

### Step 3: Automated UPS Shipment Void (NEW)
- Script: `src/src/ups_shipment_void_automation.py`
- Logs into UPS accounts
- Navigates to Billing Center
- Searches for tracking numbers
- Clicks Invoice Number to open invoice details
- Filters invoice table by tracking number
- Clicks three-dot menu → Dispute
- Selects "Void Credits" and "Package" level
- **Does NOT submit** (unless `--submit` flag is used)

## Testing the Changes

### Test Individual Steps

```bash
# Test Step 1 (ClickHouse extraction)
make test-step1

# Test Step 2 (Label-only filter)
make test-step2

# Test Step 3 (Void automation - fills forms but doesn't submit)
make test-step3
```

### Run Full Pipeline

```bash
# Run all 3 steps sequentially (foreground)
make pipeline-full

# Run all 3 steps in background
make pipeline-full-bg
```

### Manual Testing with Submit Flag

If you want to test with actual submission:

```bash
# Start Xvfb
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99

# Run with submit flag
poetry run python src/src/ups_shipment_void_automation.py --headed --submit

# Kill Xvfb
killall Xvfb
```

## Important Notes

1. **Default Behavior**: The deployment configuration runs the script WITHOUT the `--submit` flag, so disputes will be filled but NOT submitted automatically.

2. **To Enable Auto-Submit**: If you want the pipeline to automatically submit disputes, edit the Makefile line 165:
   ```makefile
   # Change from:
   $(POETRY_RUN) $(SCRIPT_VOID_AUTOMATION) --headless 2>&1 | tee $(LOG_DIR)/step3_void_automation_$(TIMESTAMP).log; \
   
   # To:
   $(POETRY_RUN) $(SCRIPT_VOID_AUTOMATION) --headless --submit 2>&1 | tee $(LOG_DIR)/step3_void_automation_$(TIMESTAMP).log; \
   ```

3. **Screenshots**: All screenshots are saved to `data/output/` directory with timestamps.

4. **Logs**: All logs are saved to `logs/` directory with timestamps.

## Next Steps

1. Test the updated pipeline on your local machine
2. Deploy to Google Cloud VM using the updated Makefile
3. Verify the automation works correctly
4. If needed, add the `--submit` flag to enable automatic submission

## Files Modified

- `src/src/ups_shipment_void_automation.py` - Added `--submit` flag
- `deployment/option1_persistent_vm/Makefile` - Updated Step 3 to use new script
- `deployment/option1_persistent_vm/MAKEFILE_CRON_DEPLOYMENT.md` - Updated documentation
- `deployment/option1_persistent_vm/run_pipeline_with_notifications.sh` - Updated script names
- `deployment/DEPLOYMENT_FILES_SUMMARY.md` - Updated file relationships
- `docs/GOOGLE_CLOUD_DEPLOYMENT.md` - Updated deployment guide

---

**Author**: Gabriel Jerdhy Lapuz  
**Project**: gsr_automation  
**Date**: 2025-11-07

