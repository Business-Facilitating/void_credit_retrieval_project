# Quick Reference: Label-Only Filter Workflow

## 🚀 Two-Step Workflow

### Step 1: Ingest Data (85-89 days ago)
```bash
poetry run python src/src/dlt_pipeline_examples.py
```
**Output**: `carrier_invoice_tracking_range_YYYYMMDD_to_YYYYMMDD.duckdb`

### Step 2: Filter for Label-Only
```bash
poetry run python src/src/ups_label_only_filter.py
```
**Output**: `ups_label_only_tracking_range_YYYYMMDD_to_YYYYMMDD.csv`

---

## 📅 Date Range

**85-89 days ago** (5-day window)

Example (Today = Oct 2, 2025):
- Start: July 5, 2025 (89 days ago)
- End: July 9, 2025 (85 days ago)

---

## 🎯 What Gets Filtered

**Included** (Label-Only):
- ✅ Exactly 1 activity record
- ✅ Status: "Shipper created a label, UPS has not received the package yet."
- ✅ Code: MP
- ✅ Type: M

**Excluded**:
- ❌ Multiple activity records (package moved/scanned)
- ❌ Different status (delivered, in transit, etc.)
- ❌ No activity records

---

## 📁 Output

**CSV File**: Only tracking numbers with label-only status

```csv
tracking_number,account_number,status_description,status_code,status_type,date_processed
1Z6A2V900332443747,123456,Shipper created a label...,MP,M,20251002_143500
```

---

## ⚙️ Configuration (.env)

```bash
DLT_TRANSACTION_START_CUTOFF_DAYS=89
DLT_TRANSACTION_END_CUTOFF_DAYS=85
```

---

## 📚 Full Documentation

- [Complete Workflow](WORKFLOW_CLARIFICATION.md)
- [Label-Only Filter Details](UPS_LABEL_ONLY_FILTER.md)
- [Main Workflow Guide](WORKFLOW_85_89_DAYS.md)

