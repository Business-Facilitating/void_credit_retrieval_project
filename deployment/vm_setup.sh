#!/bin/bash
# GSR Automation VM Setup Script
# Run this script on the GCP VM to set up the environment

set -e  # Exit on error

echo "=========================================="
echo "GSR Automation VM Setup"
echo "=========================================="
echo ""

# Step 1: Update system
echo "Step 1: Updating system packages..."
sudo apt-get update && sudo apt-get upgrade -y

# Step 2: Install Python 3.10+
echo ""
echo "Step 2: Installing Python 3.10..."
sudo apt-get install -y python3.10 python3.10-venv python3-pip

# Verify Python installation
python3 --version

# Step 3: Install Poetry
echo ""
echo "Step 3: Installing Poetry..."
curl -sSL https://install.python-poetry.org | python3 -

# Add Poetry to PATH
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"

# Verify Poetry installation
poetry --version

# Step 4: Install Git
echo ""
echo "Step 4: Installing Git..."
sudo apt-get install -y git

# Step 5: Install X11 for headed browser mode (Step 4)
echo ""
echo "Step 5: Installing X11 and Xvfb for browser automation..."
sudo apt-get install -y xvfb x11vnc fluxbox

# Step 6: Clone repository
echo ""
echo "Step 6: Cloning repository..."
cd ~
git clone https://github.com/Business-Facilitating/void_credit_retrieval_project.git
cd void_credit_retrieval_project

# Checkout dev branch
git checkout dev

# Verify branch
git branch

# Step 7: Load environment variables from Secret Manager
echo ""
echo "Step 7: Loading .env from Secret Manager..."
gcloud secrets versions access latest --secret="gsr-automation-env" > .env

# Verify .env file
echo "First 5 lines of .env:"
head -5 .env

# Step 8: Install Python dependencies
echo ""
echo "Step 8: Installing Python dependencies with Poetry..."
poetry install

# Verify installation
poetry run python --version
echo ""
echo "Installed packages:"
poetry show | head -20

# Step 9: Install Playwright browsers
echo ""
echo "Step 9: Installing Playwright browsers..."
poetry run playwright install chromium
poetry run playwright install-deps

# Step 10: Set up X11 display
echo ""
echo "Step 10: Setting up X11 display..."
echo 'export DISPLAY=:99' >> ~/.bashrc
export DISPLAY=:99

# Start Xvfb in background
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
echo "Xvfb started on display :99"

# Step 11: Create necessary directories
echo ""
echo "Step 11: Creating necessary directories..."
mkdir -p data/output
mkdir -p logs

# Step 12: Test GCS access
echo ""
echo "Step 12: Testing GCS access..."
gsutil ls gs://void_automation/

echo ""
echo "=========================================="
echo "✅ VM Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test individual pipeline steps:"
echo "   make test-step0  # IP Whitelisting"
echo "   make test-step1  # ClickHouse Extraction"
echo "   make test-step2  # PeerDB Extraction"
echo "   make test-step3  # Label Filter"
echo "   make test-step4  # Void Automation"
echo ""
echo "2. Run full pipeline:"
echo "   make pipeline-full"
echo ""
echo "3. Monitor logs:"
echo "   tail -f logs/step*.log"
echo ""
echo "4. Check GCS uploads:"
echo "   gsutil ls -r gs://void_automation/pipeline_runs/"
echo ""
echo "=========================================="

