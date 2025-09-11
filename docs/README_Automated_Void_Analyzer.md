# Automated Void Analyzer for 17Track Results

## Overview

The Automated Void Analyzer is a comprehensive tool for processing existing 17Track JSON output files to identify packages with "label created" status that need voiding. It analyzes tracking data without requiring new API calls, making it perfect for batch processing of previously collected tracking information.

## Key Features

### 🔍 **Intelligent File Processing**
- **Multiple JSON Structures**: Handles various output formats from `tracking_17_demo.py` and `tracking_17.py`
- **Batch Results**: Processes batch tracking results with multiple tracking numbers
- **Direct API Responses**: Handles raw 17Track API response format
- **Wrapped Results**: Supports wrapped result structures with metadata
- **Nested Data**: Recursively searches for tracking information in complex structures

### 📅 **Advanced Date Analysis**
- **Timezone Support**: Robust date parsing with timezone awareness using `python-dateutil`
- **Configurable Range**: Customizable age range for void candidates (default: 15-20 days)
- **Precise Calculation**: Accurate day calculation from label creation to current date
- **Multiple Date Sources**: Checks both event timestamps and milestone data

### 🎯 **Comprehensive Detection**
- **Event Stage Analysis**: Identifies `stage == "InfoReceived"` in tracking events
- **Sub-Status Matching**: Detects `sub_status == "InfoReceived"`
- **Description Parsing**: Searches for keywords like "label", "shipper created"
- **Milestone Analysis**: Examines milestone data for `key_stage == "InfoReceived"`
- **Fallback Methods**: Multiple detection strategies ensure no void candidates are missed

### 📊 **Rich Export Options**
- **CSV Export**: Detailed spreadsheet format with all candidate information
- **JSON Export**: Structured data with metadata for programmatic processing
- **Summary Reports**: Statistical analysis with breakdowns by status and age
- **Timestamped Files**: Automatic filename generation with timestamps
- **Empty File Handling**: Proper headers even when no candidates are found

## Installation and Setup

The automated void analyzer is included in the main project. Ensure you have the required dependencies:

```bash
poetry install  # Installs python-dateutil and other dependencies
```

## Usage

### 1. **Command Line Interface**

#### Analyze Single File
```bash
python src/src/automated_void_analyzer.py --file tracking_results.json
```

#### Analyze Directory
```bash
python src/src/automated_void_analyzer.py --directory data/output --pattern "*tracking*.json"
```

#### Custom Age Range
```bash
python src/src/automated_void_analyzer.py --directory data/output --min-days 10 --max-days 25
```

#### Export Options
```bash
# Skip CSV export
python src/src/automated_void_analyzer.py --file results.json --no-csv

# Skip JSON export
python src/src/automated_void_analyzer.py --file results.json --no-json

# Custom output directory
python src/src/automated_void_analyzer.py --file results.json --output-dir custom/path
```

### 2. **Programmatic Usage**

#### Simple File Analysis
```python
from automated_void_analyzer import analyze_tracking_files

# Analyze single file
result = analyze_tracking_files("tracking_results.json")

# Analyze multiple files
result = analyze_tracking_files([
    "file1.json", 
    "file2.json", 
    "file3.json"
])

print(f"Found {len(result['void_candidates'])} void candidates")
```

#### Directory Analysis
```python
from automated_void_analyzer import analyze_tracking_directory

result = analyze_tracking_directory(
    directory_path="data/output",
    file_pattern="*tracking*.json",
    min_days=15,
    max_days=20
)

for candidate in result['void_candidates']:
    print(f"{candidate['tracking_number']}: {candidate['days_since_label_created']} days old")
```

#### Advanced Usage with VoidAnalyzer Class
```python
from automated_void_analyzer import VoidAnalyzer

# Initialize analyzer
analyzer = VoidAnalyzer(output_dir="custom/output")

# Analyze files
void_candidates = analyzer.analyze_multiple_files([
    "tracking_batch_1.json",
    "tracking_batch_2.json"
])

# Generate detailed summary
summary = analyzer.generate_summary_report(void_candidates)

# Export with custom filenames
csv_path = analyzer.export_to_csv(void_candidates, "weekly_void_analysis.csv")
json_path = analyzer.export_to_json(void_candidates, "weekly_void_analysis.json")
```

### 3. **Example Scripts**

#### Basic Analysis
```bash
python examples/automated_void_analyzer_example.py single --file tracking_results.json
```

#### Multiple Files
```bash
python examples/automated_void_analyzer_example.py multiple --files file1.json file2.json file3.json
```

#### Directory Scan
```bash
python examples/automated_void_analyzer_example.py directory --path data/output --pattern "*tracking*.json"
```

#### Batch Analysis
```bash
python examples/automated_void_analyzer_example.py batch
```

## Supported JSON Structures

### 1. **Batch Results Format** (from `tracking_17_demo.py`)
```json
[
  {
    "batch_number": 1,
    "tracking_result": {
      "data": {
        "accepted": [
          {
            "number": "1Z123456789",
            "track_info": {
              "tracking": {
                "providers": [
                  {
                    "events": [
                      {
                        "time_iso": "2025-08-20T10:30:00-04:00",
                        "stage": "InfoReceived",
                        "description": "Shipper created a label"
                      }
                    ]
                  }
                ]
              }
            }
          }
        ]
      }
    }
  }
]
```

### 2. **Direct API Response Format**
```json
{
  "code": 0,
  "data": {
    "accepted": [
      {
        "number": "1Z123456789",
        "track_info": {
          "milestone": [
            {
              "key_stage": "InfoReceived",
              "time_iso": "2025-08-20T10:30:00-04:00"
            }
          ]
        }
      }
    ]
  }
}
```

### 3. **Wrapped Result Format**
```json
{
  "result": {
    "data": {
      "accepted": [
        {
          "number": "1Z123456789",
          "track_info": {
            "tracking": {
              "providers": [
                {
                  "events": [
                    {
                      "time_iso": "2025-08-20T10:30:00-04:00",
                      "sub_status": "InfoReceived",
                      "description": "Label created by shipper"
                    }
                  ]
                }
              ]
            }
          }
        }
      ]
    }
  }
}
```

## Output Files

### CSV Export (`automated_void_analysis_YYYYMMDD_HHMMSS.csv`)
```csv
tracking_number,source_file,batch_number,days_since_label_created,label_created_date,label_event_description,current_status,current_sub_status,void_reason,analysis_timestamp,needs_void
1Z123456789,tracking_results.json,1,18,2025-08-17T10:30:00-04:00,Shipper created a label,InfoReceived,InfoReceived,Label created 18 days ago,2025-09-04T14:30:00,True
```

### JSON Export (`automated_void_analysis_YYYYMMDD_HHMMSS.json`)
```json
{
  "analysis_metadata": {
    "total_candidates": 1,
    "analysis_timestamp": "2025-09-04T14:30:00",
    "analyzer_version": "1.0.0"
  },
  "void_candidates": [
    {
      "tracking_number": "1Z123456789",
      "source_file": "tracking_results.json",
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
}
```

## Configuration Options

### Default Settings
- **Minimum Days**: 15 days since label creation
- **Maximum Days**: 20 days since label creation
- **File Pattern**: `*tracking*.json`
- **Output Directory**: `data/output/`
- **Export Formats**: Both CSV and JSON

### Customization Examples
```python
# Custom age range
analyzer = VoidAnalyzer()
candidates = analyzer.analyze_directory(
    "data/output", 
    min_days=10, 
    max_days=30
)

# Custom file pattern
candidates = analyzer.analyze_directory(
    "data/output", 
    file_pattern="*17track*.json"
)

# Custom output directory
analyzer = VoidAnalyzer(output_dir="void_analysis_results")
```

## Error Handling and Edge Cases

### Robust File Processing
- **Missing Files**: Gracefully handles non-existent files with warnings
- **Malformed JSON**: Continues processing other files if one fails
- **Empty Files**: Handles empty or incomplete JSON structures
- **Permission Errors**: Provides clear error messages for file access issues

### Data Validation
- **Missing Timestamps**: Skips items without valid date information
- **Invalid Dates**: Robust date parsing with fallback methods
- **Incomplete Tracking Info**: Continues processing even with partial data
- **Timezone Issues**: Handles various timezone formats and missing timezone info

### Memory Management
- **Large Files**: Processes files efficiently without loading everything into memory
- **Batch Processing**: Handles large numbers of files without memory issues
- **Resource Cleanup**: Proper file handle management and resource cleanup

## Integration Examples

### Daily Void Analysis Script
```python
#!/usr/bin/env python3
"""Daily void analysis automation"""

from automated_void_analyzer import analyze_tracking_directory
from datetime import datetime

def daily_void_check():
    result = analyze_tracking_directory(
        directory_path="data/output",
        file_pattern="*tracking*.json",
        min_days=15,
        max_days=20
    )
    
    if result['void_candidates']:
        # Send alert or integrate with void processing system
        send_void_alert(result['void_candidates'])
    
    return result

if __name__ == "__main__":
    daily_void_check()
```

### Integration with Void Processing System
```python
from automated_void_analyzer import VoidAnalyzer

def process_voids_for_system():
    analyzer = VoidAnalyzer()
    
    # Analyze recent tracking files
    void_candidates = analyzer.analyze_directory("data/output")
    
    # Group by urgency (days since creation)
    urgent = [c for c in void_candidates if c['days_since_label_created'] >= 18]
    standard = [c for c in void_candidates if c['days_since_label_created'] < 18]
    
    # Process urgent voids first
    for candidate in urgent:
        void_processing_system.queue_urgent_void(candidate['tracking_number'])
    
    # Process standard voids
    for candidate in standard:
        void_processing_system.queue_standard_void(candidate['tracking_number'])
    
    return len(urgent), len(standard)
```

## Best Practices

1. **Regular Analysis**: Run void analysis daily or weekly on accumulated tracking data
2. **File Organization**: Keep tracking files organized by date for easier processing
3. **Backup Results**: Archive void analysis results for audit trails
4. **Integration**: Integrate with existing void processing workflows
5. **Monitoring**: Set up alerts when void candidates are found
6. **Validation**: Verify void candidates before processing to avoid false positives

## Troubleshooting

### Common Issues

**No void candidates found when expected:**
- Check file paths and patterns
- Verify JSON file structure matches supported formats
- Ensure date range settings are appropriate
- Review log messages for parsing errors

**File processing errors:**
- Check file permissions and accessibility
- Verify JSON syntax is valid
- Ensure sufficient disk space for output files
- Review file encoding (should be UTF-8)

**Date calculation issues:**
- Verify timestamp formats in source files
- Check timezone information in tracking data
- Review system clock and timezone settings
- Examine log messages for date parsing warnings

### Debug Mode
Enable detailed logging for troubleshooting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run analysis with debug output
analyzer = VoidAnalyzer()
candidates = analyzer.analyze_file("problematic_file.json")
```
