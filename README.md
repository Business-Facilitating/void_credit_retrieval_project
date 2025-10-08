# GSR Automation Project

A comprehensive data pipeline and tracking automation system for carrier invoice processing and package tracking.

## 🔐 Security Setup (IMPORTANT - READ FIRST)

**⚠️ This project now uses environment variables for all sensitive credentials. You must set up your `.env` file before running any code.**

### Quick Security Setup

1. **Copy the environment template:**

   ```bash
   cp .env.example .env
   ```

2. **Fill in your actual credentials in the `.env` file:**

   - 17Track API token
   - TrackingMore API key
   - ClickHouse database credentials

3. **Or use the interactive setup script:**

   ```bash
   poetry run python tests/setup_env.py
   ```

4. **Validate your setup:**
   ```bash
   poetry run python tests/setup_env.py validate
   ```

📖 **For detailed security setup instructions, see [docs/SECURITY_SETUP.md](docs/SECURITY_SETUP.md)**

## 🚀 Features

- **Data Pipeline**: Extract carrier invoice data from ClickHouse using DLT
- **85-89 Days Tracking Workflow**: Automated 2-step process to extract and track shipments from 85-89 days ago
- **Package Tracking**: Integration with UPS Tracking API, 17Track and TrackingMore APIs
- **UPS Web Automation**: Automated login to UPS website using Playwright
- **Batch Processing**: Efficient handling of large datasets with configurable batch sizes
- **Date Standardization**: Consistent date formatting across all data sources
- **CSV/JSON Export**: Export results to CSV and JSON formats for analysis
- **Incremental Loading**: Smart incremental data loading with time-based filtering
- **Security**: Environment variable-based credential management

## 📋 Prerequisites

- Python 3.10+
- Poetry for dependency management
- Access to ClickHouse database
- API keys for 17Track and/or TrackingMore services

## 🛠️ Installation

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd gsr_automation
   ```

2. **Install dependencies:**

   ```bash
   poetry install
   ```

3. **Set up environment variables (REQUIRED):**
   ```bash
   poetry run python tests/setup_env.py
   ```

## 🔧 Configuration

All configuration is managed through environment variables in your `.env` file:

- **API Configuration**: Batch sizes, delays, endpoints
- **Database Configuration**: ClickHouse connection settings
- **Pipeline Configuration**: DLT settings, cutoff dates, batch sizes
- **Output Configuration**: File paths and formats

## 📊 Usage

### 🎯 Main Workflow: 85-89 Days Tracking (Recommended)

This is the primary workflow for tracking shipments from 85-89 days ago:

**Step 1: Extract tracking numbers from ClickHouse**

```bash
poetry run python src/src/dlt_pipeline_examples.py
```

**Step 2A: Query UPS Tracking API (All Statuses)**

```bash
poetry run python src/src/ups_api.py
```

**Step 2B: Filter for Label-Only Tracking Numbers (Alternative)**

```bash
poetry run python src/src/ups_label_only_filter.py
```

📖 **For detailed workflow documentation:**

- **Main Workflow**: [docs/WORKFLOW_85_89_DAYS.md](docs/WORKFLOW_85_89_DAYS.md)
- **Label-Only Filter**: [docs/UPS_LABEL_ONLY_FILTER.md](docs/UPS_LABEL_ONLY_FILTER.md)

---

### Data Pipeline

Extract carrier invoice data from ClickHouse:

```bash
poetry run python src/src/dlt_pipeline_examples.py
```

### Package Tracking

Track packages using UPS Tracking API:

```bash
poetry run python src/src/ups_api.py
```

Track packages using 17Track API:

```bash
poetry run python src/src/tracking_17.py
```

Track packages using TrackingMore API:

```bash
poetry run python src/src/tracking.py
```

### UPS Web Automation

Automate login to UPS website:

```bash
# Install Playwright first (one-time setup)
poetry add playwright
poetry run playwright install chromium

# Run the automation
poetry run python src/src/ups_web_login.py
```

See [UPS Web Login Documentation](docs/README_UPS_Web_Login.md) for detailed usage.

### Testing

Run connection tests:

```bash
poetry run python tests/test_clickhouse_connection.py
poetry run python tests/test_17track_integration.py
poetry run python tests/test_ups_web_login.py
```

## 📁 Project Structure

```
gsr_automation/
├── src/src/                    # Main source code
│   ├── dlt_pipeline_examples.py   # DLT pipeline implementation
│   ├── tracking_17.py             # 17Track API integration
│   ├── tracking.py                # TrackingMore API integration
│   ├── ups_web_login.py           # UPS web automation
│   └── tracking_17_demo.py        # Demo scripts
├── tests/                      # Test scripts and utilities
│   ├── setup_env.py               # Interactive environment setup
│   ├── test_ups_web_login.py      # UPS web login tests
│   ├── switch-git-account.ps1     # Git account switcher utility
├── data/                       # Data directories
│   ├── input/                     # Input data
│   ├── output/                    # Generated outputs (screenshots, etc.)
│   └── notebooks/                 # Jupyter notebooks
├── docs/                       # Documentation
│   ├── SECURITY_SETUP.md          # Security setup guide
│   └── README_UPS_Web_Login.md    # UPS web automation guide
├── .env.example               # Environment variable template
└── README.md                 # This file
```

## 🔒 Security Features

- **Environment Variables**: All credentials stored in `.env` file
- **Gitignore Protection**: Sensitive files automatically excluded from version control
- **Validation**: Required environment variables validated at runtime
- **Secure Defaults**: SSL enabled by default for database connections
- **Permission Management**: Secure file permissions on Unix-like systems

## 📖 Documentation

- [Security Setup Guide](docs/SECURITY_SETUP.md) - Detailed security configuration
- [UPS Web Login](docs/README_UPS_Web_Login.md) - UPS website automation guide
- [17Track Integration](docs/README_17Track_Integration.md) - 17Track API documentation
- [Date Standardization](docs/DATE_STANDARDIZATION_SUMMARY.md) - Date format handling
- [Workflow Documentation](docs/WORKFLOW_DOCUMENTATION.md) - Process workflows

## 🤝 Contributing

1. Ensure your `.env` file is properly configured
2. Never commit credentials or sensitive information
3. Run tests before submitting changes
4. Follow the existing code style and patterns

## ⚠️ Important Notes

- **Never commit your `.env` file** - it contains sensitive credentials
- **Always validate your environment setup** before running pipelines
- **Use the provided test scripts** to verify connections before production use
- **Keep your API keys secure** and rotate them regularly

## 📞 Support

For issues related to:

- **Environment setup**: Check [docs/SECURITY_SETUP.md](docs/SECURITY_SETUP.md)
- **API connections**: Run the test scripts in the `tests/` directory
- **Data pipeline**: Review the DLT documentation and configuration
