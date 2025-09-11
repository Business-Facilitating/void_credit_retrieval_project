# UPS Label-Only Tracking Filter

## Overview

The UPS Label-Only Tracking Filter (`ups_label_only_filter.py`) is a specialized tool that extracts tracking numbers from the DuckDB database and filters them to find packages that have **exclusively** the "Shipper created a label, UPS has not received the package yet." status.

This tool is designed to identify packages that may be candidates for void processing, as they represent labels that were created but never actually shipped.

## Key Features

- **DuckDB Integration**: Extracts tracking numbers directly from the carrier invoice database
- **Precise Filtering**: Identifies tracking numbers with exactly one activity record matching specific criteria
- **UPS API Integration**: Uses the official UPS Tracking API to get real-time status information
- **Comprehensive Logging**: Detailed logging of processing steps and results
- **Multiple Output Formats**: Saves results in both JSON (detailed) and CSV (summary) formats

## Filtering Criteria

The tool applies strict filtering criteria to identify label-only packages:

### Required Conditions (ALL must be met):

1. **Single Activity Record**: The tracking number must have exactly ONE activity record
2. **Exact Status Description**: `"Shipper created a label, UPS has not received the package yet. "`
3. **Correct Status Code**: `"MP"`
4. **Correct Status Type**: `"M"`

### Expected Activity Structure:

```json
"activity": [
  {
    "location": {
      "address": {
        "countryCode": "US",
        "country": "US"
      }
    },
    "status": {
      "type": "M",
      "description": "Shipper created a label, UPS has not received the package yet. ",
      "code": "MP",
      "statusCode": "003"
    },
    "date": "20250905",
    "time": "140622",
    "gmtDate": "20250905",
    "gmtOffset": "-04:00",
    "gmtTime": "18:06:22"
  }
]
```

## Usage

### Basic Usage

```bash
poetry run python src/src/ups_label_only_filter.py
```

### Test the Functionality

```bash
poetry run python tests/test_ups_label_only_filter.py
```

## Configuration

The script uses the following configuration options:

### Environment Variables

- `DUCKDB_PATH`: Path to the DuckDB database (default: `carrier_invoice_extraction.duckdb`)
- `OUTPUT_DIR`: Output directory for results (default: `data/output`)

### Built-in Configuration

- **Processing Limit**: 50 tracking numbers (configurable in code)
- **API Rate Limiting**: 0.5 second delay between API calls
- **UPS API Credentials**: Uses existing credentials from `ups_api.py`

## Output Files

The script generates two output files with timestamps:

### 1. JSON File: `ups_label_only_filter_YYYYMMDD_HHMMSS.json`

Contains complete results including:

- List of label-only tracking numbers with full UPS API responses
- List of excluded tracking numbers with reasons
- API errors and statistics
- Processing metadata

### 2. CSV File: `ups_label_only_tracking_YYYYMMDD_HHMMSS.csv`

Contains filtered tracking numbers with complete status information:

```csv
tracking_number,status_description,status_code,status_type,date_processed
1Z6A2V900332443747,Shipper created a label; UPS has not received the package yet.,MP,M,20250908_223625
1Z1234567890123456,Shipper created a label; UPS has not received the package yet.,MP,M,20250908_223625
```

#### CSV Column Descriptions:

- **tracking_number**: The UPS tracking number
- **status_description**: The exact status description from UPS API
- **status_code**: The UPS status code (MP = Manifest Package)
- **status_type**: The UPS status type (M = Manifest)
- **date_processed**: Timestamp when the tracking number was processed

## Example Output

```
🚀 Starting UPS Label-Only Tracking Filter
============================================================
📊 Step 1: Extracting tracking numbers from DuckDB...
✅ Connected to DuckDB: carrier_invoice_extraction.duckdb
🔍 Extracting up to 50 tracking numbers from carrier_invoice_extraction.carrier_invoice_data...
📊 Found 50 unique UPS tracking numbers
📋 Sample tracking numbers: ['1Z005W760390048196', '1Z005W760390087359', ...]

🔑 Step 2: Getting UPS API access token...
✅ Successfully obtained UPS access token

🔄 Step 3: Processing tracking numbers...
📦 Processing 1/50: 1Z005W760390048196
   ❌ EXCLUDED: Has 3 activity records (expected exactly 1)
📦 Processing 2/50: 1Z6A2V900332443747
   ✅ MATCH: Matches label-only criteria exactly

💾 Step 4: Saving results...

============================================================
🎯 UPS LABEL-ONLY FILTER SUMMARY
============================================================
📊 Total Processed: 50
✅ Label-Only Found: 3
❌ Excluded: 45
🚫 API Errors: 2
📈 Label-Only Rate: 6.0%

🎯 LABEL-ONLY TRACKING NUMBERS:
   📦 1Z6A2V900332443747
   📦 1Z7890123456789012
   📦 1Z1234567890123456

📁 Results saved to:
   JSON: data/output/ups_label_only_filter_20250908_223625.json
   CSV:  data/output/ups_label_only_tracking_20250908_223625.csv

✅ UPS Label-Only Filter completed successfully!
```

## Integration with Existing Workflow

This tool builds upon the existing GSR automation infrastructure:

### Dependencies

- **DuckDB Database**: Uses the carrier invoice extraction database
- **UPS API Credentials**: Reuses existing UPS API configuration
- **Output Directory**: Follows existing file organization patterns

### Workflow Integration

1. **Data Source**: Extracts from the same DuckDB database used by other tools
2. **API Integration**: Uses the same UPS API credentials and patterns as `ups_api.py`
3. **Output Format**: Compatible with existing data processing workflows
4. **Error Handling**: Follows established error handling patterns

## Technical Details

### Database Query

The tool queries the DuckDB database with the following criteria:

- Non-null, non-empty tracking numbers
- UPS format (starts with "1Z")
- Unique values only
- Ordered results for consistent processing

### API Rate Limiting

- 0.5 second delay between API calls to respect UPS rate limits
- Proper error handling for API failures
- Retry logic for transient errors

### Memory Management

- Processes tracking numbers one at a time to minimize memory usage
- Streams results to files rather than keeping everything in memory
- Closes database connections properly

## Error Handling

The tool handles various error conditions:

### Database Errors

- Missing DuckDB file
- Connection failures
- Query execution errors

### API Errors

- Authentication failures
- Rate limiting
- Network timeouts
- Invalid tracking numbers

### Data Parsing Errors

- Malformed API responses
- Missing required fields
- Unexpected data structures

## Future Enhancements

Potential improvements for future versions:

1. **Batch Processing**: Process multiple tracking numbers in single API calls
2. **Caching**: Cache API responses to avoid duplicate calls
3. **Filtering Options**: Add date range and other filtering criteria
4. **Integration**: Direct integration with void processing systems
5. **Monitoring**: Add metrics and monitoring capabilities

## Related Documentation

- [UPS API Integration](README_UPS_API.md)
- [DuckDB Data Pipeline](README_DuckDB_Pipeline.md)
- [Automated Void Analyzer](README_Automated_Void_Analyzer.md)
