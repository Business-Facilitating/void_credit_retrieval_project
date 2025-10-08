# UPS Label-Only Filter Documentation

## Overview

The `ups_label_only_filter.py` script identifies UPS tracking numbers that have **ONLY** created a shipping label but were **never actually shipped** to UPS.

---

## 🎯 Purpose

Find tracking numbers with **exclusively** this status:
- **Status Description**: `"Shipper created a label, UPS has not received the package yet."`
- **Status Code**: `MP`
- **Status Type**: `M`
- **Activity Count**: Exactly **1 record** (no other tracking events)

---

## 📅 Date Range

**Default**: 85-89 days ago (configurable)

This matches the same date range used in the main DLT pipeline workflow.

---

## 🔄 How It Works

### Step 1: Extract Tracking Numbers from DuckDB

**Source**: `carrier_invoice_extraction.duckdb`

**Filters**:
- ✅ Tracking number is not null/empty
- ✅ Tracking number starts with `1Z` (UPS format)
- ✅ **Transaction date is 85-89 days ago**
- ✅ Processes **ALL** tracking numbers (no limit)

**Output**: List of `{tracking_number, account_number}` pairs

---

### Step 2: Get UPS API Access Token

Authenticates with UPS OAuth API using credentials from `.env`:
- `UPS_USERNAME` (client ID)
- `UPS_PASSWORD` (client secret)

---

### Step 3: Query UPS Tracking API

For each tracking number:
1. Calls UPS Tracking API
2. Gets complete tracking history
3. Returns full UPS response with all activity records

---

### Step 4: Filter for Label-Only Status

**This is the KEY filtering logic:**

```
UPS Response Structure:
trackResponse → shipment[0] → package[0] → activity[]
```

**Validation Checks**:

1. **Activity Count Check**:
   - ❌ If 0 activities → Excluded (no tracking data)
   - ❌ If 2+ activities → Excluded (package has moved/been scanned)
   - ✅ If exactly 1 activity → Continue checking

2. **Status Match Check** (for the single activity):
   - Description must be: `"Shipper created a label, UPS has not received the package yet."`
   - Code must be: `MP`
   - Type must be: `M`

3. **Result**:
   - ✅ **Label-Only**: All criteria match
   - ❌ **Excluded**: Doesn't match criteria

---

### Step 5: Process All Tracking Numbers

For each tracking number:
1. Query UPS API
2. Check if it's label-only
3. Categorize into:
   - ✅ **Label-only** (matches criteria)
   - ❌ **Excluded** (has other activity or different status)
   - 🚫 **API errors** (failed to query)
4. Add 0.5 second delay between requests (rate limiting)

---

### Step 6: Save Results

Creates **2 output files**:

#### JSON File (Complete Data)
**Filename**: `ups_label_only_filter_range_YYYYMMDD_to_YYYYMMDD_timestamp.json`

**Contains**:
```json
{
  "label_only_tracking_numbers": [
    {
      "tracking_number": "1Z6A2V900332443747",
      "account_number": "123456",
      "reason": "Matches label-only criteria exactly",
      "ups_response": { /* full UPS API response */ }
    }
  ],
  "excluded_tracking_numbers": [
    {
      "tracking_number": "1ZVX23230333926007",
      "account_number": "123456",
      "reason": "Has 5 activity records (expected exactly 1)",
      "ups_response": { /* full UPS API response */ }
    }
  ],
  "api_errors": [],
  "total_processed": 150,
  "total_label_only": 12,
  "total_excluded": 138,
  "total_errors": 0
}
```

#### CSV File (Filtered List)
**Filename**: `ups_label_only_tracking_range_YYYYMMDD_to_YYYYMMDD_timestamp.csv`

**Contains**: Only label-only tracking numbers
```csv
tracking_number,account_number,status_description,status_code,status_type,date_processed
1Z6A2V900332443747,123456,Shipper created a label; UPS has not received the package yet.,MP,M,20251002_143500
1Z6A2V900332443748,123456,Shipper created a label; UPS has not received the package yet.,MP,M,20251002_143500
```

---

## 📊 Example Workflow

### Input (from DuckDB - 85-89 days ago):
```
Total tracking numbers: 150
Date range: 2025-07-05 to 2025-07-09
```

### Processing Examples:

**Tracking #1: `1Z6A2V900332443747`**
```
UPS API Response:
  - Activity count: 1
  - Status: "Shipper created a label, UPS has not received the package yet."
  - Code: MP
  - Type: M
  
Result: ✅ MATCH (Label-only)
```

**Tracking #2: `1ZVX23230333926007`**
```
UPS API Response:
  - Activity count: 5
  - Statuses: 
    1. Label created
    2. Picked up
    3. In transit
    4. Out for delivery
    5. Delivered
  
Result: ❌ EXCLUDED (Has 5 activity records, expected exactly 1)
```

**Tracking #3: `1ZX041680390454826`**
```
UPS API Response:
  - Activity count: 1
  - Status: "Package voided"
  - Code: VD
  - Type: V
  
Result: ❌ EXCLUDED (Different status description)
```

### Output Summary:
```
📊 Total Processed: 150
✅ Label-Only Found: 12
❌ Excluded: 138
🚫 API Errors: 0
📈 Label-Only Rate: 8.0%
```

---

## 🚀 Usage

### Basic Usage

```bash
poetry run python src/src/ups_label_only_filter.py
```

### Configuration

Set in `.env` file:

```bash
# Date range (85-89 days ago)
DLT_TRANSACTION_START_CUTOFF_DAYS=89
DLT_TRANSACTION_END_CUTOFF_DAYS=85

# DuckDB path
DUCKDB_PATH=carrier_invoice_extraction.duckdb

# Output directory
OUTPUT_DIR=data/output

# UPS API credentials
UPS_TOKEN_URL=https://onlinetools.ups.com/security/v1/oauth/token
UPS_TRACKING_URL=https://onlinetools.ups.com/api/track/v1/details/
UPS_USERNAME=your_client_id
UPS_PASSWORD=your_client_secret
```

---

## 📁 Output Files

Both files are saved to `data/output/`:

1. **JSON**: Complete results with all tracking numbers and full UPS responses
2. **CSV**: Filtered list of only label-only tracking numbers

**Filename Pattern**:
```
ups_label_only_filter_range_20250705_to_20250709_20251002_143500.json
ups_label_only_tracking_range_20250705_to_20250709_20251002_143500.csv
```

---

## 🔍 Use Cases

### Why Find Label-Only Tracking Numbers?

1. **Fraud Detection**: Identify potentially fraudulent orders where labels were created but never shipped
2. **Inventory Issues**: Find packages that were never actually sent to customers
3. **Operational Problems**: Detect systematic issues in shipping processes
4. **Customer Service**: Proactively identify orders that need attention
5. **Refund Processing**: Identify orders that may need refunds

---

## 📊 Comparison with Other Scripts

| Feature | `ups_api.py` | `ups_label_only_filter.py` |
|---------|--------------|----------------------------|
| **Purpose** | Get status for ALL tracking numbers | Find ONLY label-only tracking numbers |
| **Date Range** | 85-89 days ago | 85-89 days ago |
| **Filtering** | None (returns all statuses) | Strict (exactly 1 activity, specific status) |
| **Output** | All tracking results | Only label-only matches |
| **Use Case** | General tracking status | Identify unshipped packages |
| **Processing** | All tracking numbers | All tracking numbers |

---

## ⚙️ Technical Details

### DuckDB Query
```sql
SELECT DISTINCT tracking_number, account_number
FROM carrier_invoice_extraction.carrier_invoice_data
WHERE tracking_number IS NOT NULL
  AND tracking_number != ''
  AND LENGTH(TRIM(tracking_number)) > 0
  AND tracking_number LIKE '1Z%'
  AND transaction_date >= '2025-07-05'
  AND transaction_date <= '2025-07-09'
ORDER BY tracking_number
```

### UPS API Response Structure
```json
{
  "trackResponse": {
    "shipment": [{
      "package": [{
        "activity": [
          {
            "status": {
              "description": "Shipper created a label, UPS has not received the package yet.",
              "code": "MP",
              "type": "M"
            }
          }
        ]
      }]
    }]
  }
}
```

---

## 🛠️ Troubleshooting

### No tracking numbers found
```
❌ No tracking numbers found. Exiting.
```
**Solution**: Check if DuckDB file exists and has data for the 85-89 days ago range.

### UPS API authentication failed
```
❌ Failed to get UPS access token
```
**Solution**: Verify UPS API credentials in `.env` file.

### DuckDB file not found
```
❌ DuckDB file not found: carrier_invoice_extraction.duckdb
```
**Solution**: Run the DLT pipeline first to create the database.

---

## 📈 Performance

- **Rate Limiting**: 0.5 second delay between API calls
- **Processing Speed**: ~2 tracking numbers per second
- **Example**: 150 tracking numbers ≈ 75 seconds

---

## 🔐 Security

- All credentials stored in `.env` file
- OAuth token obtained dynamically
- No hardcoded credentials in code

---

**Last Updated**: October 2, 2025  
**Project**: gsr_automation  
**Author**: Gabriel Jerdhy Lapuz

