# PeerDB Industry Index Logins Pipeline

## Overview

This pipeline extracts data from the PeerDB `industry_index_logins` table using DLT (Data Load Tool) and exports it to both DuckDB and CSV formats.

## 🎯 Purpose

Extract and analyze industry index login data from PeerDB for:
- User activity analysis
- Login pattern monitoring
- Data export for further processing
- Historical data archival

## 🏗️ Architecture

```
PeerDB (ClickHouse) → DLT Pipeline → DuckDB + CSV Export
```

**Source**: PeerDB `industry_index_logins` table  
**Destination**: DuckDB database + CSV file  
**Processing**: Batch extraction with configurable batch sizes

## 📋 Prerequisites

### 1. Environment Setup

Ensure your `.env` file contains PeerDB connection details:

```bash
# ClickHouse Database Configuration (PeerDB)
CLICKHOUSE_HOST=your_peerdb_host_here
CLICKHOUSE_PORT=8443
CLICKHOUSE_USERNAME=your_username_here
CLICKHOUSE_PASSWORD=your_password_here
CLICKHOUSE_DATABASE=peerdb
CLICKHOUSE_SECURE=true

# Optional: Pipeline Configuration
DLT_WRITE_DISPOSITION=replace
DLT_CLICKHOUSE_BATCH_SIZE=50000
OUTPUT_DIR=data/output
```

### 2. Dependencies

The pipeline requires:
- `dlt` - Data Load Tool
- `clickhouse-connect` - ClickHouse client
- `duckdb` - DuckDB database
- `pandas` - Data manipulation (for CSV export)

Install with Poetry:
```bash
poetry install
```

## 🚀 Usage

### Step 1: Test Connection

First, verify your PeerDB connection and explore the table:

```bash
poetry run python tests/test_peerdb_connection.py
```

This will:
- Test connection to PeerDB
- Show table schema
- Display sample data
- Show record counts

### Step 2: Run the Pipeline

Extract data from PeerDB:

```bash
poetry run python src/src/peerdb_pipeline.py
```

## 📊 Output

The pipeline generates:

### 1. DuckDB Database
- **File**: `peerdb_industry_index_logins.duckdb`
- **Table**: `peerdb_data.industry_index_logins`
- **Format**: Structured database for SQL queries

### 2. CSV Export
- **File**: `data/output/peerdb_industry_index_logins_YYYYMMDD_HHMMSS.csv`
- **Format**: Comma-separated values for spreadsheet analysis
- **Timestamp**: Includes extraction timestamp in filename

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLICKHOUSE_HOST` | Required | PeerDB ClickHouse host |
| `CLICKHOUSE_PORT` | `8443` | PeerDB ClickHouse port |
| `CLICKHOUSE_USERNAME` | Required | PeerDB username |
| `CLICKHOUSE_PASSWORD` | Required | PeerDB password |
| `CLICKHOUSE_DATABASE` | `peerdb` | Database name |
| `CLICKHOUSE_SECURE` | `true` | Use SSL connection |
| `DLT_WRITE_DISPOSITION` | `replace` | How to handle existing data |
| `DLT_CLICKHOUSE_BATCH_SIZE` | `50000` | Records per batch |
| `OUTPUT_DIR` | `data/output` | CSV output directory |

### Write Dispositions

- `replace`: Overwrite existing data (recommended)
- `append`: Add to existing data
- `merge`: Update existing records

## 🔍 Data Analysis

### Using DuckDB

```python
import duckdb

# Connect to the extracted data
conn = duckdb.connect('peerdb_industry_index_logins.duckdb')

# Query the data
result = conn.execute("""
    SELECT * FROM peerdb_data.industry_index_logins 
    LIMIT 10
""").fetchdf()

print(result)
```

### Using CSV

```python
import pandas as pd

# Load the CSV file
df = pd.read_csv('data/output/peerdb_industry_index_logins_20241002_143022.csv')

# Basic analysis
print(f"Records: {len(df):,}")
print(f"Columns: {len(df.columns)}")
print(df.head())
```

## 🛠️ Troubleshooting

### Connection Issues

1. **"ClickHouse library not available"**
   ```bash
   poetry add clickhouse-connect
   ```

2. **"Connection failed"**
   - Verify host, port, username, password in `.env`
   - Check network connectivity
   - Ensure SSL settings are correct

3. **"Table not found"**
   - Run the test script to see available tables
   - Verify table name `industry_index_logins` exists

### Pipeline Issues

1. **"No data found"**
   - Check if table has records
   - Verify permissions to read the table

2. **"Memory issues"**
   - Reduce `DLT_CLICKHOUSE_BATCH_SIZE`
   - Monitor system memory usage

## 📁 File Structure

```
gsr_automation/
├── src/src/
│   └── peerdb_pipeline.py          # Main pipeline script
├── tests/
│   └── test_peerdb_connection.py   # Connection test script
├── docs/
│   └── README_PeerDB_Pipeline.md   # This documentation
├── data/output/
│   └── peerdb_industry_index_logins_*.csv  # CSV exports
└── peerdb_industry_index_logins.duckdb     # DuckDB output
```

## 🔄 Integration with Existing Workflows

This pipeline follows the same patterns as other GSR automation pipelines:

1. **Environment-based configuration** (`.env` file)
2. **DLT framework** for data extraction
3. **DuckDB + CSV outputs** for flexibility
4. **Batch processing** for large datasets
5. **Error handling and logging**

## 📈 Next Steps

After running the pipeline, you can:

1. **Analyze the data** using DuckDB or pandas
2. **Integrate with other pipelines** in the GSR automation suite
3. **Schedule regular extractions** using cron or task schedulers
4. **Build dashboards** using the exported CSV data

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Run the test script to diagnose connection issues
3. Review the pipeline logs for detailed error messages
