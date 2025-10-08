# Security Setup Guide

## Overview

This document outlines the security improvements implemented in the gsr_automation project to protect sensitive credentials and API keys.

## Environment Variables Setup

### 1. Create .env File

Copy the `.env.example` file to `.env` and fill in your actual credentials:

```bash
cp .env.example .env
```

Or use the interactive setup script:

```bash
poetry run python tests/setup_env.py
```

### 2. Required Environment Variables

The following environment variables must be set in your `.env` file:

#### 17Track API Configuration

- `SEVENTEEN_TRACK_API_TOKEN`: Your 17Track API token
- `SEVENTEEN_TRACK_API_URL`: 17Track API endpoint (default provided)
- `SEVENTEEN_TRACK_REGISTER_URL`: 17Track registration endpoint (default provided)
- `SEVENTEEN_TRACK_DEFAULT_CARRIER_CODE`: Default carrier code (default: 100002 for UPS)

#### TrackingMore API Configuration

- `TRACKINGMORE_API_KEY`: Your TrackingMore API key

#### UPS API Configuration

- `UPS_TOKEN_URL`: UPS OAuth token endpoint (default provided)
- `UPS_TRACKING_URL`: UPS tracking API endpoint (default provided)
- `UPS_USERNAME`: Your UPS API username
- `UPS_PASSWORD`: Your UPS API password

#### UPS Web Login Configuration

- `UPS_WEB_LOGIN_URL`: UPS website login page (default provided)
- `UPS_WEB_USERNAME`: Your UPS website username
- `UPS_WEB_PASSWORD`: Your UPS website password

#### ClickHouse Database Configuration

- `CLICKHOUSE_HOST`: Your ClickHouse server hostname
- `CLICKHOUSE_PORT`: ClickHouse port (default: 9440)
- `CLICKHOUSE_USERNAME`: Your ClickHouse username
- `CLICKHOUSE_PASSWORD`: Your ClickHouse password
- `CLICKHOUSE_DATABASE`: Your ClickHouse database name
- `CLICKHOUSE_SECURE`: Whether to use SSL (default: true)

#### Application Configuration

- `BATCH_SIZE`: API batch size (default: 40)
- `API_DELAY`: Delay between API calls in seconds (default: 1.0)
- `DUCKDB_PATH`: Path to DuckDB file (default: carrier_invoice_extraction.duckdb)
- `OUTPUT_DIR`: Output directory for results (default: data/output)

### 3. Example .env File

```env
# 17Track API Configuration
SEVENTEEN_TRACK_API_TOKEN=your_actual_17track_token_here
SEVENTEEN_TRACK_API_URL=https://api.17track.net/track/v2.4/gettrackinfo
SEVENTEEN_TRACK_REGISTER_URL=https://api.17track.net/track/v2.2/register
SEVENTEEN_TRACK_DEFAULT_CARRIER_CODE=100002

# TrackingMore API Configuration
TRACKINGMORE_API_KEY=your_actual_trackingmore_key_here

# ClickHouse Database Configuration
CLICKHOUSE_HOST=your_clickhouse_host_here
CLICKHOUSE_PORT=9440
CLICKHOUSE_USERNAME=your_username_here
CLICKHOUSE_PASSWORD=your_password_here
CLICKHOUSE_DATABASE=your_database_here
CLICKHOUSE_SECURE=true

# DLT Pipeline Configuration
DLT_WRITE_DISPOSITION=append
DLT_CLICKHOUSE_BATCH_SIZE=50000
DLT_CLICKHOUSE_WINDOW_SECONDS=3600
DLT_INVOICE_CUTOFF_DAYS=30
DLT_FORCE_FULL_LOAD=false

# Application Configuration
BATCH_SIZE=40
API_DELAY=1.0
DUCKDB_PATH=carrier_invoice_extraction.duckdb
OUTPUT_DIR=data/output
```

## Security Best Practices

### 1. Never Commit Credentials

- The `.env` file is automatically excluded by `.gitignore`
- Never commit API keys, passwords, or other sensitive information to version control
- Use environment variables for all sensitive configuration

### 2. File Exclusions

The following files and patterns are excluded from version control:

- `.env` and all `.env.*` files
- `*.key`, `*.pem`, `*.p12`, `*.pfx` files
- `credentials.json`, `secrets.json`, `config.json`
- `.secrets/` and `.credentials/` directories

### 3. Validation

All modules now validate that required environment variables are set and will raise clear error messages if credentials are missing.

## Migration from Hardcoded Credentials

The following files have been updated to use environment variables:

- `src/src/tracking_17.py`
- `src/src/tracking.py`
- `src/src/tracking_17_demo.py`
- `src/src/dlt_pipeline_examples.py`
- `src/src/ups_api.py`
- `src/src/ups_web_login.py`
- `src/src/ups_label_only_filter.py`
- `tests/test_clickhouse_connection.py`
- `tests/clickhouse_http_client.py`
- `tests/test_clickhouse_advanced.py`
- `tests/test_ups_web_login.py`

## Troubleshooting

### Missing Environment Variables

If you see errors like "environment variable is required", ensure:

1. Your `.env` file exists in the project root
2. All required variables are set with actual values
3. No extra spaces around the `=` sign in your `.env` file

### ClickHouse Connection Issues

If ClickHouse connections fail:

1. Verify your credentials are correct
2. Check that `CLICKHOUSE_SECURE=true` for cloud instances
3. Ensure the host includes the full domain name

### API Authentication Errors

If API calls fail with authentication errors:

1. Verify your API tokens are valid and active
2. Check for any trailing spaces in your `.env` file
3. Ensure you're using the correct API endpoints
