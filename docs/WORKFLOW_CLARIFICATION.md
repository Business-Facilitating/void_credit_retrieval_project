# GSR Automation Workflow - Clarification

## 📋 Complete Workflow Overview

This document clarifies the exact workflow for the GSR Automation project.

---

## 🎯 Primary Workflow: Label-Only Filter (85-89 Days)

### **Step 1: Ingest Data from ClickHouse**

**Script**: `dlt_pipeline_examples.py`

**What it does**:
- Connects to ClickHouse database
- Extracts data from `carrier_carrier_invoice_original_flat_ups` table
- Filters by `transaction_date`: **85-89 days ago**
- Creates DuckDB file with all tracking numbers from that date range

**Command**:
```bash
poetry run python src/src/dlt_pipeline_examples.py
```

**Output**:
```
data/output/carrier_invoice_tracking_range_YYYYMMDD_to_YYYYMMDD_timestamp.duckdb
```

**Example**: If today is October 2, 2025:
- Start: July 5, 2025 (89 days ago)
- End: July 9, 2025 (85 days ago)
- File: `carrier_invoice_tracking_range_20250705_to_20250709_20251002_143022.duckdb`

---

### **Step 2: Filter for Label-Only Tracking Numbers**

**Script**: `ups_label_only_filter.py`

**What it does**:
1. Reads the DuckDB file created in Step 1
2. Extracts **ALL** tracking numbers from the 85-89 days range
3. Queries UPS Tracking API for each tracking number
4. Filters for tracking numbers with **ONLY** this status:
   - Status: `"Shipper created a label, UPS has not received the package yet."`
   - Code: `MP`
   - Type: `M`
   - Activity count: **Exactly 1** (no other tracking events)
5. Outputs CSV file with only the label-only tracking numbers

**Command**:
```bash
poetry run python src/src/ups_label_only_filter.py
```

**Output**:
```
data/output/ups_label_only_tracking_range_YYYYMMDD_to_YYYYMMDD_timestamp.csv
data/output/ups_label_only_filter_range_YYYYMMDD_to_YYYYMMDD_timestamp.json
```

**CSV Format**:
```csv
tracking_number,account_number,status_description,status_code,status_type,date_processed
1Z6A2V900332443747,123456,Shipper created a label; UPS has not received the package yet.,MP,M,20251002_143500
1Z6A2V900332443748,123456,Shipper created a label; UPS has not received the package yet.,MP,M,20251002_143500
```

---

## 🔄 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    STEP 1: DATA INGESTION                    │
│              (dlt_pipeline_examples.py)                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
                ┌───────────────────────┐
                │  ClickHouse Database  │
                │  carrier_carrier_     │
                │  invoice_original_    │
                │  flat_ups             │
                └───────────────────────┘
                            ↓
                Filter: transaction_date
                WHERE date BETWEEN
                  (today - 89 days) AND
                  (today - 85 days)
                            ↓
                ┌───────────────────────┐
                │   DuckDB File         │
                │ carrier_invoice_      │
                │ tracking_range_       │
                │ YYYYMMDD_to_          │
                │ YYYYMMDD.duckdb       │
                └───────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              STEP 2: LABEL-ONLY FILTERING                    │
│            (ups_label_only_filter.py)                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
                ┌───────────────────────┐
                │  Extract ALL          │
                │  Tracking Numbers     │
                │  (85-89 days ago)     │
                └───────────────────────┘
                            ↓
                ┌───────────────────────┐
                │  Query UPS API        │
                │  for Each Tracking #  │
                └───────────────────────┘
                            ↓
                ┌───────────────────────┐
                │  Filter Criteria:     │
                │  - Exactly 1 activity │
                │  - Status: Label only │
                │  - Code: MP           │
                │  - Type: M            │
                └───────────────────────┘
                            ↓
                ┌───────────────────────┐
                │  CSV Output File      │
                │  (Label-only          │
                │   tracking numbers)   │
                └───────────────────────┘
```

---

## 📊 Example Execution

### **Today: October 2, 2025**

#### **Step 1: Ingest Data**
```bash
$ poetry run python src/src/dlt_pipeline_examples.py

🎯 Target transaction date range: 2025-07-05 to 2025-07-09 (89-85 days ago)
✅ Extracted batch: 50000 rows (total: 150,000)
📁 File saved: carrier_invoice_tracking_range_20250705_to_20250709_20251002_143022.duckdb
📦 Tracking numbers: 45,230 total, 42,150 unique
```

#### **Step 2: Filter for Label-Only**
```bash
$ poetry run python src/src/ups_label_only_filter.py

🎯 Target transaction_date range: 2025-07-05 to 2025-07-09 (89-85 days ago)
📊 Found 42,150 unique UPS tracking numbers in date range
🔄 Processing 42,150 tracking numbers...

📦 Processing 1/42150: 1Z6A2V900332443747
   ✅ MATCH: Matches label-only criteria exactly

📦 Processing 2/42150: 1ZVX23230333926007
   ❌ EXCLUDED: Has 5 activity records (expected exactly 1)

...

📊 Total Processed: 42,150
✅ Label-Only Found: 1,247
❌ Excluded: 40,903
📈 Label-Only Rate: 3.0%

📁 Results saved to:
   CSV:  data/output/ups_label_only_tracking_range_20250705_to_20250709_20251002_143500.csv
   JSON: data/output/ups_label_only_filter_range_20250705_to_20250709_20251002_143500.json
```

---

## 📁 Final Output

### **CSV File** (Primary Output)
**File**: `ups_label_only_tracking_range_20250705_to_20250709_20251002_143500.csv`

**Contains**: Only tracking numbers with label-only status

```csv
tracking_number,account_number,status_description,status_code,status_type,date_processed
1Z6A2V900332443747,123456,Shipper created a label; UPS has not received the package yet.,MP,M,20251002_143500
1Z6A2V900332443748,123456,Shipper created a label; UPS has not received the package yet.,MP,M,20251002_143500
1Z6A2V900332443749,789012,Shipper created a label; UPS has not received the package yet.,MP,M,20251002_143500
```

**Total**: 1,247 tracking numbers (from 42,150 processed)

---

## 🎯 Use Case

**Purpose**: Identify packages where shipping labels were created but the packages were **never actually shipped** to UPS.

**Why This Matters**:
- 🔍 **Fraud Detection**: Identify potentially fraudulent orders
- 📦 **Inventory Issues**: Find packages that should have shipped but didn't
- 🚨 **Operational Problems**: Detect systematic shipping issues
- 💰 **Refund Processing**: Identify orders that may need refunds
- 📞 **Customer Service**: Proactively contact customers about unshipped orders

---

## ⚙️ Configuration

All settings in `.env` file:

```bash
# Date Range (85-89 days ago)
DLT_TRANSACTION_START_CUTOFF_DAYS=89  # Start: 89 days ago
DLT_TRANSACTION_END_CUTOFF_DAYS=85    # End: 85 days ago

# DuckDB Configuration
DUCKDB_PATH=carrier_invoice_extraction.duckdb

# UPS API Credentials
UPS_TOKEN_URL=https://onlinetools.ups.com/security/v1/oauth/token
UPS_TRACKING_URL=https://onlinetools.ups.com/api/track/v1/details/
UPS_USERNAME=your_client_id
UPS_PASSWORD=your_client_secret

# Output Directory
OUTPUT_DIR=data/output
```

---

## ✅ Summary

**Your Workflow**:
1. ✅ Ingest data from ClickHouse (85-89 days ago) → DuckDB file
2. ✅ Extract ALL tracking numbers from DuckDB
3. ✅ Filter for label-only status via UPS API
4. ✅ Output CSV file with only label-only tracking numbers

**Key Points**:
- Date range: **85-89 days ago** (5-day window)
- Processes: **ALL tracking numbers** (no limit)
- Output: **CSV file** with label-only tracking numbers
- Filter: **Exactly 1 activity** with status "Shipper created a label, UPS has not received the package yet."

---

**Last Updated**: October 2, 2025  
**Project**: gsr_automation  
**Author**: Gabriel Jerdhy Lapuz

