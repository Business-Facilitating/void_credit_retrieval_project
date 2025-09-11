# DLT Pipeline Modifications - Exact Date Filtering

## Overview

The DLT pipeline in `src/src/dlt_pipeline_examples.py` has been modified to extract tracking numbers from ClickHouse where the associated `invoice_date` is **exactly 30 days prior** to the current extraction date, rather than within the last 30 days.

## Key Changes Made

### 1. Date Filtering Logic

**Before:**
```sql
WHERE invoice_date >= %(cutoff_date)s
```

**After:**
```sql
WHERE invoice_date = %(target_date)s
```

The pipeline now filters for records where `invoice_date` matches exactly one specific date (30 days ago), not a date range.

### 2. Variable Naming

- Changed `cutoff_date` to `target_date` throughout the code for clarity
- Updated parameter dictionaries to use `target_date` instead of `cutoff_date`

### 3. Enhanced CSV Export

**Filename Format:**
- **Before:** `carrier_invoice_data_30days_{timestamp}.csv`
- **After:** `carrier_invoice_tracking_exact_{target_date}_{timestamp}.csv`

**Query Optimization:**
- Added tracking number prioritization in the ORDER BY clause
- Records with tracking numbers are sorted first

**Enhanced Statistics:**
- Added tracking number count and unique count reporting
- Shows sample tracking numbers in the output
- Displays the exact target date used for filtering

### 4. New Tracking Number Extraction Function

Added `extract_tracking_numbers_from_pipeline(pipeline)` function that:
- Extracts unique tracking numbers from the filtered data
- Provides detailed statistics about tracking numbers found
- Returns a list of tracking numbers for further processing

### 5. Improved Logging

- Shows the exact target date being used at pipeline start
- Displays tracking number statistics during CSV export
- Added tracking number extraction step to main pipeline flow

## Environment Variables

The pipeline still uses the same environment variable:
- `DLT_INVOICE_CUTOFF_DAYS` (default: 30) - Number of days back to target

## Usage

### Running the Pipeline

```bash
# Run with default 30-day lookback
poetry run python src/src/dlt_pipeline_examples.py

# Run with custom lookback period (e.g., 45 days)
DLT_INVOICE_CUTOFF_DAYS=45 poetry run python src/src/dlt_pipeline_examples.py
```

### Testing the Changes

```bash
# Run the test script to verify configuration
poetry run python tests/test_exact_date_pipeline.py
```

## Expected Output

When running the pipeline, you'll see:

```
🚀 ClickHouse Carrier Invoice Data Extraction Pipeline
============================================================
🎯 Target invoice date: 2025-08-09 (exactly 30 days ago)
📥 Extracting data from ClickHouse...
🎯 Target table: carrier_carrier_invoice_original_flat_ups
📍 Destination: duckdb

✅ Extraction pipeline completed successfully!
📊 carrier_invoice_data: 1,234 rows extracted

📤 Exporting data to CSV...
📊 Exporting 1,234 rows to CSV...
✅ CSV export completed successfully!
📁 File saved: data/output/carrier_invoice_tracking_exact_20250809_143022.csv
📊 Exported 1,234 rows with 45 columns
📅 Date range: 2025-08-09 to 2025-08-09
📦 Tracking numbers: 987 total, 987 unique
📋 Sample tracking numbers: ['1Z005W760290052334', '1Z005W760390165201', '1Z005W760390197089']

📦 Extracting tracking numbers from pipeline data...
📊 Found 987 unique tracking numbers
🎯 Target date was: 2025-08-09
📋 Sample tracking numbers: ['1Z005W760290052334', '1Z005W760390165201', '1Z005W760390197089', '1Z005W760390184084', '1Z005W760390160779']
✅ Successfully extracted 987 tracking numbers
```

## File Structure

```
gsr_automation/
├── src/src/dlt_pipeline_examples.py    # Modified pipeline (main changes)
├── tests/test_exact_date_pipeline.py   # Test script for verification
├── docs/EXACT_DATE_PIPELINE_CHANGES.md # This documentation
└── data/output/                        # CSV exports with new naming
    └── carrier_invoice_tracking_exact_YYYYMMDD_HHMMSS.csv
```

## Benefits

1. **Precise Date Targeting:** Extracts data for exactly one date, not a range
2. **Tracking Number Focus:** Prioritizes and reports on tracking numbers
3. **Better Traceability:** Clear filename indicates exact date extracted
4. **Enhanced Monitoring:** Detailed statistics and logging
5. **Maintained Functionality:** All existing features (incremental loading, batching, memory management) preserved

## Backward Compatibility

- All existing environment variables work the same way
- Pipeline interface remains unchanged
- CSV export location and format enhanced but compatible
- Incremental loading based on `import_time` still functions

## Next Steps

1. Run the test script to verify configuration
2. Execute the pipeline to extract tracking numbers for exactly 30 days ago
3. Use the extracted tracking numbers for 17Track API processing
4. Monitor the enhanced logging for insights into data extraction patterns
