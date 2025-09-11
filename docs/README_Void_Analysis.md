# Void Analysis Feature for 17Track Integration

## Overview

The void analysis feature identifies tracking numbers that have a "label created" status that is between 15-20 days old (configurable). These packages typically need to be voided because they indicate labels that were created but the packages were never shipped.

## Features

### 🔍 **Automatic Detection**
- Analyzes 17Track API responses to find "label created" events
- Calculates days since label creation using current date
- Identifies packages within configurable age range (default: 15-20 days)
- Supports multiple detection methods:
  - `InfoReceived` stage in tracking events
  - `InfoReceived` sub_status in tracking events
  - Text matching for "label" or "shipper created" in descriptions
  - Milestone data analysis

### 📊 **Comprehensive Analysis**
- Processes batch tracking results from 17Track API
- Extracts current package status for context
- Provides detailed void candidate information:
  - Tracking number
  - Days since label creation
  - Label creation timestamp
  - Current delivery status
  - Void reason description

### 📄 **Export Capabilities**
- CSV export with all void candidate details
- JSON export for programmatic processing
- Timestamped filenames for tracking analysis runs
- Empty file handling with proper headers

## Usage

### 1. **Integrated Pipeline Analysis**

Use the enhanced demo pipeline with built-in void analysis:

```python
from tracking_17_demo import demo_tracking_pipeline

# Run pipeline with void analysis enabled
result = demo_tracking_pipeline(
    tracking_numbers=["1Z123456789", "1Z987654321"],
    analyze_void_candidates=True,
    void_min_days=15,
    void_max_days=20,
    export_json=True,
    export_csv=True
)

# Check for void candidate files in results
if result and any("void" in key for key in result.keys()):
    print("🚨 Void candidates found! Check the exported files.")
```

### 2. **Analyze Existing Data**

Analyze previously collected tracking data without making new API calls:

```python
from tracking_17_demo import analyze_existing_tracking_data_for_voids

# Analyze existing JSON file
void_candidates = analyze_existing_tracking_data_for_voids(
    json_file_path="data/output/tracking_results_20250904_143022.json",
    min_days=15,
    max_days=20,
    export_results=True
)

if void_candidates:
    print(f"Found {len(void_candidates)} packages that need voiding")
```

### 3. **Standalone Analysis**

Use individual analysis functions for custom workflows:

```python
from tracking_17_demo import (
    analyze_tracking_for_void_candidates,
    export_void_candidates_to_csv
)

# Analyze tracking results
void_candidates = analyze_tracking_for_void_candidates(
    results=tracking_results,
    min_days=15,
    max_days=20
)

# Export results
if void_candidates:
    csv_path = export_void_candidates_to_csv(void_candidates)
    print(f"Exported void candidates to: {csv_path}")
```

## Command Line Usage

Use the example script for easy command-line operation:

```bash
# Run full pipeline with void analysis
python examples/void_analysis_example.py --mode pipeline

# Analyze existing data file
python examples/void_analysis_example.py --mode analyze --file data/output/tracking_results.json

# Test with sample data
python examples/void_analysis_example.py --mode test

# Custom void age range
python examples/void_analysis_example.py --mode pipeline --min-days 10 --max-days 25
```

## Output Files

### CSV Export (`void_candidates_YYYYMMDD_HHMMSS.csv`)
```csv
tracking_number,batch_number,days_since_label_created,label_created_date,label_event_description,current_status,current_sub_status,void_reason,analysis_timestamp,needs_void
1Z123456789,1,18,2025-08-17T10:30:00-04:00,Shipper created a label,InfoReceived,InfoReceived,Label created 18 days ago,2025-09-04T14:30:00,True
```

### JSON Export (`void_candidates_YYYYMMDD_HHMMSS.json`)
```json
[
  {
    "tracking_number": "1Z123456789",
    "batch_number": 1,
    "days_since_label_created": 18,
    "label_created_date": "2025-08-17T10:30:00-04:00",
    "label_event_description": "Shipper created a label, UPS has not received the package yet.",
    "current_status": "InfoReceived",
    "current_sub_status": "InfoReceived",
    "void_reason": "Label created 18 days ago",
    "analysis_timestamp": "2025-09-04T14:30:00",
    "needs_void": true
  }
]
```

## Configuration

### Default Settings
- **Minimum Days**: 15 days since label creation
- **Maximum Days**: 20 days since label creation
- **Export Format**: Both CSV and JSON
- **Output Directory**: `data/output/`

### Customization
```python
# Custom age range
void_candidates = analyze_tracking_for_void_candidates(
    results=tracking_results,
    min_days=10,  # Custom minimum
    max_days=30   # Custom maximum
)

# Custom export filenames
csv_path = export_void_candidates_to_csv(
    void_candidates, 
    "custom_void_analysis_2025.csv"
)
```

## Detection Logic

The void analysis uses multiple methods to identify "label created" events:

1. **Event Stage Analysis**: Looks for `stage == "InfoReceived"`
2. **Sub-Status Analysis**: Checks for `sub_status == "InfoReceived"`
3. **Description Matching**: Searches for keywords like "label" or "shipper created"
4. **Milestone Data**: Examines milestone events for `key_stage == "InfoReceived"`

## Error Handling

- **Missing Data**: Gracefully handles missing tracking information
- **Date Parsing**: Robust timestamp parsing with timezone support
- **API Errors**: Continues processing other packages if individual items fail
- **File Operations**: Creates directories and handles file permissions

## Testing

Run the test suite to verify functionality:

```bash
python tests/test_void_analysis.py
```

The test creates sample data with different label creation dates and verifies:
- Correct identification of void candidates
- Proper date calculations
- Export functionality
- Edge case handling

## Integration with Existing Workflow

The void analysis feature integrates seamlessly with the existing 17Track workflow:

1. **Registration**: Tracking numbers are registered with 17Track API
2. **Processing Wait**: 5-minute wait for API processing
3. **Retrieval**: Tracking information is retrieved
4. **Analysis**: Void candidates are automatically identified
5. **Export**: Results are exported to CSV and JSON formats

## Dependencies

The void analysis feature requires:
- `python-dateutil` for robust date parsing
- `pandas` for CSV export functionality
- `json` for JSON export (built-in)

Install the new dependency:
```bash
poetry install  # Will install python-dateutil from pyproject.toml
```

## Best Practices

1. **Regular Analysis**: Run void analysis on a regular schedule (daily/weekly)
2. **Age Range Tuning**: Adjust min/max days based on your business requirements
3. **Data Retention**: Keep void analysis results for audit trails
4. **Integration**: Integrate with your void processing workflow
5. **Monitoring**: Set up alerts when void candidates are found

## Troubleshooting

### Common Issues

**No void candidates found when expected:**
- Check if tracking data contains "InfoReceived" events
- Verify date range settings (min_days/max_days)
- Ensure tracking data is recent enough

**Date parsing errors:**
- Check timestamp format in tracking data
- Verify timezone information is present
- Review log messages for specific parsing issues

**Export failures:**
- Ensure `data/output/` directory exists and is writable
- Check available disk space
- Verify file permissions
