# GSR Automation Workflow Summary

## Overview

The GSR Automation project implements a **2-step workflow** to track UPS shipments from a specific historical time window (85-89 days ago).

---

## 📋 Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         STEP 1: DATA EXTRACTION                      │
│                    (dlt_pipeline_examples.py)                        │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │   ClickHouse Database     │
                    │  carrier_carrier_invoice  │
                    │  _original_flat_ups       │
                    └───────────────────────────┘
                                    │
                                    │ Filter: transaction_date
                                    │ WHERE date BETWEEN
                                    │   (today - 89 days) AND
                                    │   (today - 85 days)
                                    ▼
                    ┌───────────────────────────┐
                    │   Extract Data via DLT    │
                    │   - Batch processing      │
                    │   - Date standardization  │
                    │   - Incremental loading   │
                    └───────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │   DuckDB Output File      │
                    │ carrier_invoice_tracking_ │
                    │ range_YYYYMMDD_to_        │
                    │ YYYYMMDD_timestamp.duckdb │
                    └───────────────────────────┘
                                    │
                                    │ Contains:
                                    │ - Tracking numbers
                                    │ - Invoice data
                                    │ - Transaction dates
                                    │
┌─────────────────────────────────────────────────────────────────────┐
│                      STEP 2: UPS API TRACKING                        │
│                         (ups_api.py)                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │  Read DuckDB File         │
                    │  (most recent)            │
                    └───────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │  Extract Unique           │
                    │  Tracking Numbers         │
                    └───────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │  UPS OAuth                │
                    │  Authentication           │
                    └───────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │  Query UPS Tracking API   │
                    │  (for each tracking #)    │
                    └───────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────┐
                    │  JSON Output Files        │
                    │  - Individual responses   │
                    │  - Batch summary          │
                    └───────────────────────────┘
```

---

## 🎯 Purpose

**Goal**: Track the current delivery status of UPS shipments that were transacted 85-89 days ago.

**Use Cases**:
- Monitor delivery performance for historical shipments
- Identify undelivered or problematic packages
- Analyze shipping patterns over time
- Generate reports on delivery success rates

---

## 🔧 Configuration

### Date Range (Default: 85-89 days ago)

Set in `.env` file:

```bash
DLT_TRANSACTION_START_CUTOFF_DAYS=89  # Start of range
DLT_TRANSACTION_END_CUTOFF_DAYS=85    # End of range
```

### Required Credentials

```bash
# ClickHouse Database
CLICKHOUSE_HOST=your-host
CLICKHOUSE_PORT=8443
CLICKHOUSE_USERNAME=your-username
CLICKHOUSE_PASSWORD=your-password
CLICKHOUSE_DATABASE=your-database

# UPS API
UPS_TOKEN_URL=https://onlinetools.ups.com/security/v1/oauth/token
UPS_TRACKING_URL=https://onlinetools.ups.com/api/track/v1/details/
UPS_USERNAME=your-client-id
UPS_PASSWORD=your-client-secret
```

---

## 📊 Data Flow

| Step | Input | Process | Output |
|------|-------|---------|--------|
| **1** | ClickHouse DB | Filter by transaction_date (85-89 days) | DuckDB file with tracking numbers |
| **2** | DuckDB file | Query UPS API for each tracking # | JSON files with current status |

---

## 📁 File Structure

```
gsr_automation/
├── src/src/
│   ├── dlt_pipeline_examples.py  ← STEP 1: Extract from ClickHouse
│   └── ups_api.py                ← STEP 2: Query UPS API
├── data/output/
│   ├── carrier_invoice_tracking_range_*.duckdb  ← Step 1 output
│   ├── ups_tracking_*.json                      ← Step 2 individual
│   └── ups_tracking_batch_*.json                ← Step 2 batch
├── docs/
│   ├── WORKFLOW_85_89_DAYS.md       ← Full documentation
│   ├── QUICK_START_85_89_DAYS.md    ← Quick reference
│   └── WORKFLOW_SUMMARY.md          ← This file
└── .env                             ← Configuration
```

---

## 🚀 Quick Start

```bash
# Step 1: Extract tracking numbers (85-89 days ago)
poetry run python src/src/dlt_pipeline_examples.py

# Step 2: Query UPS API for current status
poetry run python src/src/ups_api.py
```

---

## 📈 Example Output

### Step 1 Console Output
```
🎯 Target transaction date range: 2025-07-04 to 2025-07-08 (89-85 days ago)
✅ Extracted batch: 50000 rows (total: 150,000)
📁 File saved: carrier_invoice_tracking_range_20250704_to_20250708_20251001_143022.duckdb
📦 Tracking numbers: 45,230 total, 42,150 unique
```

### Step 2 Console Output
```
📂 Using DuckDB file: carrier_invoice_tracking_range_20250704_to_20250708_20251001_143022.duckdb
✅ Extracted 42,150 tracking numbers from DuckDB
📊 Total tracking numbers to process: 42,150

Processing tracking number 1/42150: 1Z6A2V900332443747
  Status: Delivered (code: 011)
  
All responses saved to: ups_tracking_batch_20251001_143500.json
Total tracking numbers processed: 42,150
```

---

## 🔍 Key Features

### Step 1: DLT Pipeline
- ✅ Incremental loading with time-based filtering
- ✅ Batch processing (50k-100k rows per batch)
- ✅ Date standardization (YYYY-MM-DD format)
- ✅ Memory-efficient keyset pagination
- ✅ Automatic schema detection

### Step 2: UPS API Integration
- ✅ OAuth authentication
- ✅ Automatic DuckDB file detection
- ✅ Individual and batch JSON outputs
- ✅ Error handling and retry logic
- ✅ Progress tracking

---

## 📚 Documentation

- **Full Workflow Guide**: [WORKFLOW_85_89_DAYS.md](WORKFLOW_85_89_DAYS.md)
- **Quick Start**: [QUICK_START_85_89_DAYS.md](QUICK_START_85_89_DAYS.md)
- **Security Setup**: [SECURITY_SETUP.md](SECURITY_SETUP.md)
- **Main README**: [../README.md](../README.md)

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| No DuckDB file found | Run Step 1 first |
| No tracking numbers | Check ClickHouse data for 85-89 days ago |
| UPS API auth failed | Verify credentials in `.env` |
| Connection timeout | Check network/firewall settings |

---

## 💡 Tips

1. **Always run Step 1 before Step 2** - The UPS API script needs the DuckDB file
2. **Check date ranges** - Verify the 85-89 day window matches your needs
3. **Monitor output files** - Review JSON files to ensure data quality
4. **Archive old files** - Clean up `data/output/` periodically
5. **Use environment variables** - Customize date ranges without code changes

---

## 📞 Support

For questions or issues:
1. Check the documentation in `docs/`
2. Review error messages in console output
3. Verify `.env` configuration
4. Check ClickHouse and UPS API connectivity

---

**Last Updated**: October 2, 2025  
**Project**: gsr_automation  
**Author**: Gabriel Jerdhy Lapuz

