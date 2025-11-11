# Quick Start: 85-89 Days Tracking Workflow

## TL;DR

```bash
# Step 1: Extract tracking numbers (85-89 days ago)
poetry run python src/src/dlt_pipeline_examples.py

# Step 2: Query UPS API
poetry run python src/src/ups_api.py
```

## What This Does

1. **Step 1** extracts tracking numbers from ClickHouse where `transaction_date` is **85-89 days ago**
2. **Step 2** queries UPS Tracking API for the current status of those tracking numbers

## Example Timeline

**Today: October 1, 2025**

- **89 days ago**: July 4, 2025 (start)
- **85 days ago**: July 8, 2025 (end)
- **Filter**: All tracking numbers with transaction dates between July 4-8, 2025

## Output Files

### After Step 1:
```
data/output/carrier_invoice_tracking_range_20250704_to_20250708_20251001_143022.duckdb
```

### After Step 2:
```
data/output/ups_tracking_1Z6A2V900332443747_20251001_143500.json  (individual)
data/output/ups_tracking_batch_20251001_143500.json               (batch)
```

## Customize Date Range

Edit `.env` file:

```bash
# Default: 85-89 days ago
DLT_TRANSACTION_START_CUTOFF_DAYS=89
DLT_TRANSACTION_END_CUTOFF_DAYS=85

# Example: Change to 90-95 days ago
# DLT_TRANSACTION_START_CUTOFF_DAYS=95
# DLT_TRANSACTION_END_CUTOFF_DAYS=90
```

## Prerequisites

1. ✅ ClickHouse database access configured in `.env`
2. ✅ UPS API credentials configured in `.env`
3. ✅ Poetry dependencies installed: `poetry install`

## Full Documentation

📖 See [WORKFLOW_85_89_DAYS.md](WORKFLOW_85_89_DAYS.md) for complete details.

