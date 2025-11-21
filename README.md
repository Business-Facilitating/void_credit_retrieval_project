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

- **4-Step Automated Pipeline**: Complete workflow from data extraction to shipment void automation
  1. Extract carrier invoice data from ClickHouse
  2. Extract industry index logins from PeerDB
  3. Filter label-only tracking numbers
  4. Automated UPS shipment void
- **Multi-Database Support**: ClickHouse and PeerDB integration
- **Package Tracking**: Integration with UPS Tracking API, 17Track and TrackingMore APIs
- **UPS Web Automation**: Automated login and shipment void using Playwright
- **Batch Processing**: Efficient handling of large datasets with configurable batch sizes
- **Date Standardization**: Consistent date formatting across all data sources
- **CSV/JSON Export**: Export results to CSV and JSON formats for analysis
- **Incremental Loading**: Smart incremental data loading with time-based filtering
- **Security**: Environment variable-based credential management
- **GCP Deployment**: Full support for Google Cloud Platform Linux VMs with Makefile and cron automation

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

## 🚢 Deployment Options

### Option 1: Persistent VM with Cron (Traditional)

- **Best for:** Frequent runs, complex workflows
- **Cost:** ~$25-30/month (VM running 24/7)
- **Setup:** [deployment/option1_persistent_vm/](deployment/option1_persistent_vm/)

### Option 2: Ephemeral VM with Cloud Scheduler (Recommended) ⭐

- **Best for:** Infrequent runs (every other day), cost optimization
- **Cost:** ~$0.50-1/month (VM only when running)
- **Savings:** ~95% cheaper!
- **Setup:** [deployment/option2_ephemeral_vm/](deployment/option2_ephemeral_vm/)

**👉 See [deployment/README.md](deployment/README.md) for complete deployment guide**

---

## 🚀 Quick Start - Option 2 (Ephemeral VM - Recommended)

**5-Step Setup:**

```bash
# 1. Navigate to deployment folder
cd deployment/option2_ephemeral_vm

# 2. Update configuration
nano deploy_ephemeral.sh  # Set PROJECT_ID and REPO_URL

# 3. Ensure .env file exists with credentials
ls -la ../../.env

# 4. Run deployment script
chmod +x deploy_ephemeral.sh
./deploy_ephemeral.sh

# 5. Test the setup
gcloud scheduler jobs run gsr-automation-scheduler --location=us-central1

# 6. Check results
gsutil ls gs://gsr-automation-results/runs/
```

**What you get:**

- ✅ Automated runs every other day at 2:00 AM
- ✅ Fresh VM created for each run
- ✅ Results saved to Cloud Storage
- ✅ VM auto-deletes after completion
- ✅ ~$0.50-1/month cost

**See:** [deployment/option2_ephemeral_vm/OPTION2_QUICK_START.md](deployment/option2_ephemeral_vm/OPTION2_QUICK_START.md)

---

## 🛠️ Quick Start - Option 1 (Persistent VM)

```bash
# 1. Copy Makefile to project root
cp deployment/option1_persistent_vm/Makefile .

# 2. On your GCP VM, run setup
make setup              # Install dependencies and setup
make test-step1         # Test Step 1: Extract from ClickHouse
make test-step2         # Test Step 2: Filter label-only
make test-step3         # Test Step 3: UPS web login
make pipeline-full      # Run complete pipeline

# 3. Setup automated scheduling
crontab -e              # Add cron jobs (see deployment/option1_persistent_vm/crontab.txt)
```

**Available Commands:**

```bash
make help               # Show all available commands
make pipeline-full      # Run all 4 steps sequentially
make status             # Show pipeline status
make logs               # View recent logs
```

**See:** [deployment/option1_persistent_vm/DEPLOYMENT_QUICK_REFERENCE.md](deployment/option1_persistent_vm/DEPLOYMENT_QUICK_REFERENCE.md)

## 🔧 Configuration

All configuration is managed through environment variables in your `.env` file:

- **API Configuration**: Batch sizes, delays, endpoints
- **Database Configuration**: ClickHouse connection settings
- **Pipeline Configuration**: DLT settings, cutoff dates, batch sizes
- **Output Configuration**: File paths and formats

## 📊 Usage

### 🎯 Main Automated Pipeline (Recommended)

This is the complete 4-step automated pipeline for shipment processing:

**Step 1: Extract carrier invoice data from ClickHouse**

```bash
poetry run python src/src/dlt_pipeline_examples.py
```

**Step 2: Extract industry index logins from PeerDB**

```bash
poetry run python src/src/peerdb_pipeline.py
```

**Step 3: Filter for Label-Only Tracking Numbers**

```bash
poetry run python src/src/ups_label_only_filter.py
```

**Step 4: Automated UPS Shipment Void**

```bash
poetry run python src/src/ups_shipment_void_automation.py
```

**Or run all steps together using Makefile:**

```bash
make pipeline-full  # Runs all 4 steps sequentially with proper delays
```

📖 **For detailed workflow documentation:**

- **Main Workflow**: [docs/WORKFLOW_85_89_DAYS.md](docs/WORKFLOW_85_89_DAYS.md)
- **Label-Only Filter**: [docs/UPS_LABEL_ONLY_FILTER.md](docs/UPS_LABEL_ONLY_FILTER.md)
- **PeerDB Pipeline**: [docs/README_PeerDB_Pipeline.md](docs/README_PeerDB_Pipeline.md)
- **Deployment Guide**: [deployment/README.md](deployment/README.md)

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

### Core Documentation

- [Security Setup Guide](docs/SECURITY_SETUP.md) - Detailed security configuration
- [UPS Web Login](docs/README_UPS_Web_Login.md) - UPS website automation guide
- [17Track Integration](docs/README_17Track_Integration.md) - 17Track API documentation
- [Date Standardization](docs/DATE_STANDARDIZATION_SUMMARY.md) - Date format handling
- [Workflow Documentation](docs/WORKFLOW_DOCUMENTATION.md) - Process workflows

### Deployment Documentation

- [Deployment Summary](docs/DEPLOYMENT_SUMMARY.md) - Complete deployment overview
- [Makefile & Cron Guide](docs/MAKEFILE_CRON_DEPLOYMENT.md) - Detailed deployment guide
- [Quick Reference](docs/DEPLOYMENT_QUICK_REFERENCE.md) - Quick reference card
- [GCP Deployment](docs/GOOGLE_CLOUD_DEPLOYMENT.md) - Google Cloud Platform guide
- [Linux Deployment](docs/LINUX_DEPLOYMENT_SUMMARY.md) - Linux deployment summary

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
