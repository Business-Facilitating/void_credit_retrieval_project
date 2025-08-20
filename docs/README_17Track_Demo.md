# 17Track API Demo Module

## Overview

`tracking_17_demo.py` is a standalone demo version of the 17Track API integration that accepts manually provided tracking numbers instead of extracting them from DuckDB. This version is perfect for presentations, demonstrations, and testing without requiring database access.

## Key Features

- **No Database Dependencies**: Eliminates DuckDB requirements
- **Manual Input**: Accepts tracking numbers as function parameters
- **Complete 17Track Workflow**: Implements the full registration → wait → retrieval process
- **5-Minute Processing Wait**: Complies with 17Track documentation requirements
- **Batch Processing**: Handles multiple tracking numbers efficiently
- **Export Capabilities**: Generates both JSON and CSV output files
- **Progress Tracking**: Real-time countdown during processing waits
- **Demo-Friendly**: Easy to use for presentations and demonstrations

## Quick Start

### Basic Usage

```python
from src.src.tracking_17_demo import demo_tracking_pipeline

# Define your tracking numbers
tracking_numbers = [
    "1Z005W760290052334",
    "1Z005W760390165201",
    "1Z005W760390197089",
]

# Run the demo pipeline
result = demo_tracking_pipeline(
    tracking_numbers=tracking_numbers,
    export_json=True,
    export_csv=True
)

if result:
    print("Demo completed successfully!")
    for file_type, path in result.items():
        print(f"{file_type.upper()}: {path}")
```

### Command Line Demo

```bash
# Run the built-in demo with sample tracking numbers
poetry run python src/src/tracking_17_demo.py
```

## API Workflow

The demo follows the complete 17Track API workflow:

### Step 1: Registration (1 second)
- Registers tracking numbers with 17Track API
- Uses endpoint: `https://api.17track.net/track/v2.2/register`

### Step 2: Processing Wait (5 minutes)
- Waits for 17Track to process registered numbers
- Shows real-time countdown progress
- Required by 17Track documentation

### Step 3: Retrieval (1 second)
- Retrieves tracking information for registered numbers
- Uses endpoint: `https://api.17track.net/track/v2.4/gettrackinfo`

### Step 4: Export
- Exports raw JSON with complete API responses
- Exports consolidated CSV with flattened tracking data

## Expected Timeline

### For 5 tracking numbers (1 batch):
```
00:00 - Start demo pipeline
00:01 - Registration complete
00:01 - Start 5-minute processing wait
⏰ 5m 0s remaining for processing...
⏰ 4m 0s remaining for processing...
⏰ 3m 0s remaining for processing...
⏰ 2m 0s remaining for processing...
⏰ 1m 0s remaining for processing...
05:01 - Retrieval complete
05:02 - Export files complete
```

## Function Reference

### `demo_tracking_pipeline(tracking_numbers, ...)`

Main demo function that processes manually provided tracking numbers.

**Parameters:**
- `tracking_numbers: List[str]` - List of tracking numbers to process
- `api_token: Optional[str]` - 17Track API token (uses default if None)
- `carrier_code: int` - Carrier code (default: 100002 for UPS)
- `export_json: bool` - Whether to export raw JSON (default: True)
- `export_csv: bool` - Whether to export CSV (default: True)

**Returns:**
- `Dict[str, str]` - Dictionary with paths to exported files
- `None` - If processing failed

### `DEMO_TRACKING_NUMBERS`

Predefined list of sample UPS tracking numbers for quick testing:
```python
DEMO_TRACKING_NUMBERS = [
    "1Z005W760290052334",
    "1Z005W760390165201", 
    "1Z005W760390197089",
    "1Z005W760390184084",
    "1Z005W760390160779",
]
```

## Output Files

### JSON Export
- **Filename**: `demo_17track_raw_YYYYMMDD_HHMMSS.json`
- **Content**: Complete API responses including registration and tracking data
- **Use**: Debugging, API analysis, complete audit trail

### CSV Export
- **Filename**: `demo_17track_consolidated_YYYYMMDD_HHMMSS.csv`
- **Content**: Flattened tracking data with key fields
- **Columns**: batch_number, tracking_number, delivery_status, location, timestamps, etc.
- **Use**: Analysis, reporting, spreadsheet import

## Example Usage Scenarios

### 1. Presentation Demo
```python
# Quick demo for presentations
from src.src.tracking_17_demo import demo_tracking_pipeline, DEMO_TRACKING_NUMBERS

result = demo_tracking_pipeline(DEMO_TRACKING_NUMBERS)
```

### 2. Custom Tracking Numbers
```python
# Demo with specific tracking numbers
custom_numbers = ["1Z005W760290052334", "1Z005W760390165201"]
result = demo_tracking_pipeline(custom_numbers)
```

### 3. Testing Different Carriers
```python
# Demo with different carrier (if needed)
result = demo_tracking_pipeline(
    tracking_numbers=["tracking_number"],
    carrier_code=100001  # Different carrier code
)
```

## Differences from Main Module

| Feature | tracking_17.py | tracking_17_demo.py |
|---------|----------------|---------------------|
| Data Source | DuckDB extraction | Manual input |
| Dependencies | Requires DuckDB | No database required |
| Main Function | `main_duckdb_tracking_pipeline()` | `demo_tracking_pipeline()` |
| Use Case | Production pipeline | Demos & presentations |
| Database Config | Required | Not needed |

## Notes

- **Execution Time**: Plan for 5+ minutes per batch due to required processing wait
- **API Compliance**: Follows 17Track documentation requirements exactly
- **Rate Limiting**: Includes appropriate delays between batches
- **Error Handling**: Comprehensive error handling for both registration and retrieval
- **Progress Visibility**: Real-time progress updates during wait periods

## Troubleshooting

### Common Issues

1. **No results exported**: Check if tracking numbers are valid and properly formatted
2. **API errors**: Verify API token is correct and has sufficient quota
3. **Long execution time**: This is expected due to the 5-minute processing requirement
4. **Import errors**: Ensure you're importing from the correct path (`src.src.tracking_17_demo`)

### Getting Help

Check the log output for detailed error messages and processing status. The demo includes comprehensive logging for troubleshooting.
