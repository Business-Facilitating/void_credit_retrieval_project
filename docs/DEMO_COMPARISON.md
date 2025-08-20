# Comparison: tracking_17.py vs tracking_17_demo.py

## Overview

This document compares the main production module (`tracking_17.py`) with the demo version (`tracking_17_demo.py`) to help you choose the right version for your needs.

## Key Differences

| Feature | tracking_17.py | tracking_17_demo.py |
|---------|----------------|---------------------|
| **Data Source** | DuckDB database extraction | Manual tracking number input |
| **Dependencies** | Requires DuckDB + database file | No database dependencies |
| **Main Function** | `main_duckdb_tracking_pipeline()` | `demo_tracking_pipeline()` |
| **Use Case** | Production data processing | Demos, presentations, testing |
| **Setup Complexity** | Requires database setup | Plug-and-play |
| **Data Volume** | Handles large datasets | Best for small demo sets |

## Functional Comparison

### Data Input

**tracking_17.py:**
```python
# Extracts from DuckDB automatically
result = main_duckdb_tracking_pipeline(
    limit=30,  # Extract 30 numbers from database
    export_json=True,
    export_csv=True
)
```

**tracking_17_demo.py:**
```python
# Accepts manual input
tracking_numbers = ["1Z005W760290052334", "1Z005W760390165201"]
result = demo_tracking_pipeline(
    tracking_numbers=tracking_numbers,
    export_json=True,
    export_csv=True
)
```

### Dependencies

**tracking_17.py:**
- Requires DuckDB installation
- Needs carrier_invoice_extraction.duckdb file
- Database connection and table access

**tracking_17_demo.py:**
- No database requirements
- Only needs standard Python libraries
- Completely standalone

### Output Files

Both versions produce identical output formats:

**JSON Files:**
- `duckdb_17track_raw_*.json` (production)
- `demo_17track_raw_*.json` (demo)

**CSV Files:**
- `duckdb_17track_consolidated_*.csv` (production)
- `demo_17track_consolidated_*.csv` (demo)

## When to Use Each Version

### Use tracking_17.py when:
- ✅ Processing production data from DuckDB
- ✅ Handling large volumes of tracking numbers
- ✅ Automated pipeline execution
- ✅ Integration with existing database workflows
- ✅ Regular scheduled processing

### Use tracking_17_demo.py when:
- ✅ Giving presentations or demos
- ✅ Testing specific tracking numbers
- ✅ No database access available
- ✅ Quick proof-of-concept work
- ✅ Training or educational purposes
- ✅ Standalone testing

## Shared Features

Both versions include:

- ✅ Complete 17Track API workflow (register → wait → retrieve)
- ✅ 5-minute processing wait compliance
- ✅ Batch processing with progress tracking
- ✅ Real-time countdown during waits
- ✅ Comprehensive error handling
- ✅ JSON and CSV export capabilities
- ✅ Same output file formats
- ✅ Rate limiting and API compliance
- ✅ Detailed logging and progress updates

## Code Examples

### Production Pipeline (tracking_17.py)
```python
from src.src.tracking_17 import main_duckdb_tracking_pipeline

# Extract from database and process
result = main_duckdb_tracking_pipeline(
    limit=50,  # Extract 50 tracking numbers
    export_json=True,
    export_csv=True
)
```

### Demo Pipeline (tracking_17_demo.py)
```python
from src.src.tracking_17_demo import demo_tracking_pipeline

# Process specific tracking numbers
tracking_numbers = [
    "1Z005W760290052334",
    "1Z005W760390165201",
    "1Z005W760390197089"
]

result = demo_tracking_pipeline(
    tracking_numbers=tracking_numbers,
    export_json=True,
    export_csv=True
)
```

## Migration Between Versions

### From Production to Demo
```python
# Instead of extracting from database
# result = main_duckdb_tracking_pipeline(limit=30)

# Use manual input
tracking_numbers = ["number1", "number2", "number3"]
result = demo_tracking_pipeline(tracking_numbers)
```

### From Demo to Production
```python
# Instead of manual input
# result = demo_tracking_pipeline(tracking_numbers)

# Use database extraction
result = main_duckdb_tracking_pipeline(limit=30)
```

## Performance Considerations

### Execution Time
Both versions have identical execution times:
- **5+ minutes per batch** due to required API processing wait
- **Same API call patterns** and rate limiting
- **Identical workflow steps** and timing

### Resource Usage
- **tracking_17.py**: Higher memory usage due to database connections
- **tracking_17_demo.py**: Lower memory footprint, no database overhead

## Conclusion

Choose the version that best fits your use case:
- **Production workflows** → `tracking_17.py`
- **Demos and testing** → `tracking_17_demo.py`

Both versions maintain the same high-quality 17Track API integration with full compliance to their documentation requirements.
