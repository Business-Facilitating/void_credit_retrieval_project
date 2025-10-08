# 85-89 Days Tracking Workflow

## Overview

This workflow extracts carrier invoice data from ClickHouse for tracking numbers with transaction dates **85-89 days ago**, then queries the UPS Tracking API to get their current status.

## Why 85-89 Days?

This specific time window allows you to:
- Track packages that were shipped 85-89 days ago
- Monitor delivery status after a specific aging period
- Identify potential issues with older shipments
- Analyze historical shipping patterns

## Workflow Steps

### Step 1: Extract Data from ClickHouse (DLT Pipeline)

**Script:** `src/src/dlt_pipeline_examples.py`

**What it does:**
1. Connects to ClickHouse database
2. Queries the `carrier_carrier_invoice_original_flat_ups` table
3. Filters records where `transaction_date` is between 85-89 days ago
4. Extracts all tracking numbers from this date range
5. Saves data to a timestamped DuckDB file

**Command:**
```bash
poetry run python src/src/dlt_pipeline_examples.py
```

**Output:**
- DuckDB file: `data/output/carrier_invoice_tracking_range_YYYYMMDD_to_YYYYMMDD_timestamp.duckdb`
- Example: `carrier_invoice_tracking_range_20250704_to_20250708_20251001_152942.duckdb`

**Date Calculation Example:**
- Today: October 1, 2025
- 89 days ago: July 4, 2025 (start date)
- 85 days ago: July 8, 2025 (end date)
- **Filter:** `transaction_date >= '2025-07-04' AND transaction_date <= '2025-07-08'`

---

### Step 2: Query UPS Tracking API

**Script:** `src/src/ups_api.py`

**What it does:**
1. Finds the most recent DuckDB file from Step 1
2. Extracts all unique tracking numbers from the DuckDB file
3. Authenticates with UPS API (OAuth)
4. Queries UPS Tracking API for each tracking number
5. Saves individual and batch results to JSON files

**Command:**
```bash
poetry run python src/src/ups_api.py
```

**Output:**
- Individual files: `data/output/ups_tracking_{TRACKING_NUMBER}_{timestamp}.json`
- Batch file: `data/output/ups_tracking_batch_{timestamp}.json`

**What you get:**
- Current delivery status for each tracking number
- Delivery dates, locations, and status codes
- Error information for invalid/not found tracking numbers

---

## Complete Workflow Example

### Scenario: October 1, 2025

```bash
# Step 1: Extract tracking numbers from ClickHouse (85-89 days ago)
poetry run python src/src/dlt_pipeline_examples.py
```

**Output:**
```
🎯 Target transaction date range: 2025-07-04 to 2025-07-08 (89-85 days ago)
✅ Extracted batch: 50000 rows (total: 150,000)
📁 File saved: data/output/carrier_invoice_tracking_range_20250704_to_20250708_20251001_143022.duckdb
📦 Tracking numbers: 45,230 total, 42,150 unique
```

```bash
# Step 2: Query UPS API for those tracking numbers
poetry run python src/src/ups_api.py
```

**Output:**
```
📂 Using DuckDB file: data/output/carrier_invoice_tracking_range_20250704_to_20250708_20251001_143022.duckdb
✅ Extracted 42,150 tracking numbers from DuckDB
📊 Total tracking numbers to process: 42,150

Processing tracking number 1/42150: 1Z6A2V900332443747
  Status: Delivered (code: 011)
  Saved to: data/output/ups_tracking_1Z6A2V900332443747_20251001_143500.json

...

All responses saved to: data/output/ups_tracking_batch_20251001_143500.json
Total tracking numbers processed: 42,150
```

---

## Configuration

### Environment Variables

You can customize the date range in your `.env` file:

```bash
# Default: 85-89 days ago (5-day window)
DLT_TRANSACTION_START_CUTOFF_DAYS=89
DLT_TRANSACTION_END_CUTOFF_DAYS=85

# Example: Change to 90-95 days ago
# DLT_TRANSACTION_START_CUTOFF_DAYS=95
# DLT_TRANSACTION_END_CUTOFF_DAYS=90
```

### UPS API Configuration

Required in `.env`:
```bash
UPS_TOKEN_URL=https://onlinetools.ups.com/security/v1/oauth/token
UPS_TRACKING_URL=https://onlinetools.ups.com/api/track/v1/details/
UPS_USERNAME=your_client_id
UPS_PASSWORD=your_client_secret
```

---

## Data Flow

```
ClickHouse (carrier_carrier_invoice_original_flat_ups)
    ↓
    ↓ [Filter: transaction_date 85-89 days ago]
    ↓
DuckDB File (carrier_invoice_tracking_range_*.duckdb)
    ↓
    ↓ [Extract: unique tracking numbers]
    ↓
UPS Tracking API
    ↓
    ↓ [Query: current status for each tracking number]
    ↓
JSON Output Files (ups_tracking_*.json)
```

---

## Output File Structure

### Individual Tracking Response
`data/output/ups_tracking_1Z6A2V900332443747_20251001_143500.json`

```json
{
  "tracking_number": "1Z6A2V900332443747",
  "request_timestamp": "2025-10-01T14:35:00.123456",
  "response_status_code": 200,
  "ups_response": {
    "trackResponse": {
      "shipment": [{
        "package": [{
          "trackingNumber": "1Z6A2V900332443747",
          "currentStatus": {
            "code": "011",
            "description": "Delivered"
          },
          "deliveryDate": [{
            "date": "20250710"
          }]
        }]
      }]
    }
  }
}
```

### Batch Response
`data/output/ups_tracking_batch_20251001_143500.json`

```json
{
  "batch_timestamp": "2025-10-01T14:35:00.123456",
  "total_tracking_numbers": 42150,
  "responses": [
    { /* individual response 1 */ },
    { /* individual response 2 */ },
    ...
  ]
}
```

---

## Troubleshooting

### No DuckDB file found
```
❌ No DuckDB files found matching pattern: data/output/carrier_invoice_tracking_range_*.duckdb
💡 Run dlt_pipeline_examples.py first to extract data from ClickHouse
```

**Solution:** Run Step 1 first to create the DuckDB file.

### No tracking numbers extracted
```
ℹ️ No tracking numbers found in the extracted data
```

**Solution:** Check if there's data in ClickHouse for the 85-89 days ago date range.

### UPS API authentication failed
```
❌ OAuth failed with status 401
```

**Solution:** Verify your UPS API credentials in `.env` file.

---

## Best Practices

1. **Run Step 1 first** - Always extract fresh data from ClickHouse before querying UPS API
2. **Check date ranges** - Verify the date range matches your analysis needs
3. **Monitor API limits** - UPS API may have rate limits; consider adding delays if needed
4. **Review outputs** - Check the JSON files to ensure data quality
5. **Archive old files** - Regularly clean up old DuckDB and JSON files from `data/output/`

---

## Next Steps

After running this workflow, you can:
- Analyze delivery performance for the 85-89 day window
- Identify undelivered or problematic shipments
- Generate reports on shipping patterns
- Compare with other time windows for trend analysis

