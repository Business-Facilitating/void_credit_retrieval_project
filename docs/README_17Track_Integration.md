# 17Track API Integration for GSR Automation

## Overview

This document describes the new `tracking.py` file that integrates with the 17Track API (api.17track.net/track/v2.4/gettrackinfo) while maintaining the same functionality and interface as the original TrackingMore-based implementation.

## Key Features

✅ **Complete API Integration**: Uses 17Track API for package tracking  
✅ **Batch Processing**: Processes up to 40 tracking numbers per batch  
✅ **CSV Export**: Exports tracking data to CSV files in `data/output/`  
✅ **Progress Indicators**: Shows batch processing progress  
✅ **Error Handling**: Robust error handling for API failures  
✅ **Same Interface**: Drop-in replacement for existing tracking.py  
✅ **Data Compatibility**: Maintains same output format for downstream processing  

## API Configuration

The 17Track integration uses the following configuration:

```python
API_URL = "https://api.17track.net/track/v2.4/gettrackinfo"
API_TOKEN = "3ED9315FC1B2FC06CB396E95FE72AB66"
DEFAULT_CARRIER_CODE = 100002  # UPS carrier code
BATCH_SIZE = 40  # Maximum tracking numbers per API call
```

## Data Structure

### 17Track API Response Format

```json
{
  "code": 0,
  "data": {
    "accepted": [
      {
        "number": "1Z005W760290052334",
        "carrier": 100002,
        "track_info": {
          "latest_status": {
            "status": "Delivered",
            "sub_status": "Delivered_Other"
          },
          "latest_event": {
            "time_iso": "2025-07-30T13:38:47-07:00",
            "description": "Delivered",
            "location": "LAS VEGAS, NV, US"
          },
          "shipping_info": {
            "recipient_address": {
              "country": "US",
              "state": "NV",
              "city": "LAS VEGAS",
              "postal_code": "89102"
            }
          },
          "misc_info": {
            "service_type": "UPS 2nd Day Air",
            "weight_raw": "35.00LBS",
            "weight_kg": "15.88"
          }
        }
      }
    ],
    "rejected": []
  }
}
```

### CSV Export Fields

The CSV export includes the following fields:

- `batch_number`: Batch processing number
- `tracking_number`: The tracking number
- `carrier_code`: Carrier code (100002 for UPS)
- `delivery_status`: Current delivery status
- `sub_status`: Detailed sub-status
- `latest_event_description`: Description of latest event
- `latest_event_time`: ISO timestamp of latest event
- `latest_event_location`: Location of latest event
- `destination_country`: Destination country
- `destination_state`: Destination state
- `destination_city`: Destination city
- `destination_postal_code`: Destination postal code
- `service_type`: Shipping service type
- `weight_raw`: Raw weight string
- `weight_kg`: Weight in kilograms
- `processed_timestamp`: When the data was processed
- `raw_track_data`: Truncated raw tracking data for debugging

## Usage Examples

### Basic Usage

```python
from tracking import SeventeenTrackClient, DEFAULT_CARRIER_CODE

# Initialize client
client = SeventeenTrackClient()

# Track single package
result = client.get_tracking_info("1Z005W760290052334", DEFAULT_CARRIER_CODE)

# Track multiple packages
tracking_numbers = ["1Z005W760290052334", "1Z005W760390165201"]
batch_result = client.get_tracking_results_batch(tracking_numbers, DEFAULT_CARRIER_CODE)
```

### Batch Processing with CSV Export

```python
from tracking import (
    SeventeenTrackClient,
    process_tracking_numbers_in_batches,
    export_tracking_results_to_csv,
    DEFAULT_CARRIER_CODE
)

# Initialize client
client = SeventeenTrackClient()

# Process tracking numbers in batches
tracking_numbers = ["1Z005W760290052334", "1Z005W760390165201"]
results, successful, failed = process_tracking_numbers_in_batches(
    tracking_numbers, client, DEFAULT_CARRIER_CODE
)

# Export to CSV
if results:
    csv_path = export_tracking_results_to_csv(results)
    print(f"Results exported to: {csv_path}")
```

### Status Monitoring

```python
from tracking import monitor_tracking_status_changes

# Monitor status changes
results, status_summary = monitor_tracking_status_changes(
    client, tracking_numbers, DEFAULT_CARRIER_CODE
)

print(f"Status counts: {status_summary['status_counts']}")
```

## Differences from TrackingMore Integration

### Supported Features
- ✅ Single tracking queries
- ✅ Batch tracking queries (up to 40 per batch)
- ✅ CSV export with detailed tracking information
- ✅ Status monitoring and summary reports
- ✅ Progress indicators for batch processing
- ✅ Error handling and retry logic

### Unsupported Features
- ❌ Date range queries (17Track API doesn't support this)
- ❌ Carrier-wide queries (17Track API doesn't support this)
- ❌ Courier listing (17Track uses carrier codes instead)

### API Differences
- **Authentication**: Uses `17token` header instead of API key
- **Carrier Codes**: Uses numeric codes (100002 for UPS) instead of strings
- **Response Structure**: Different JSON structure with `accepted`/`rejected` arrays
- **Field Names**: Different field names for tracking data

## Testing

Run the test scripts to verify functionality:

```bash
# Basic API integration test
python test_17track_integration.py

# Complete pipeline test
python test_17track_pipeline.py
```

## File Structure

```
gsr_automation/
├── tracking.py                          # Main 17Track integration
├── test_17track_integration.py          # Basic API tests
├── test_17track_pipeline.py             # Complete pipeline tests
├── README_17Track_Integration.md        # This documentation
└── data/output/                         # CSV exports and batch results
    ├── test_17track_results_*.csv       # Test CSV exports
    └── tracking_*.json                  # Batch processing results
```

## Migration Notes

The new `tracking.py` file is designed as a drop-in replacement for the original TrackingMore-based implementation. The main differences are:

1. **Client Class**: `SeventeenTrackClient` instead of `TrackingMoreClient`
2. **Parameter Names**: `carrier_code` (int) instead of `courier_code` (str)
3. **API Token**: Uses 17Track token instead of TrackingMore API key
4. **Data Structure**: Handles 17Track's different response format internally

All public functions maintain the same interface and return compatible data structures for downstream processing.

## Performance

- **Batch Size**: Up to 40 tracking numbers per API call
- **Rate Limiting**: 1-second delay between API calls
- **Memory Usage**: Efficient processing with streaming CSV export
- **Error Recovery**: Continues processing even if individual batches fail

## Support

For issues or questions about the 17Track integration, check:

1. Test scripts for usage examples
2. API response logs for debugging
3. CSV export files for data verification
4. Original TrackingMore implementation for comparison
