#!/bin/bash
# Test VM Setup Script - Runs Steps 0-3 Only
# This script is for manual testing purposes only
# The scheduled run will use the full pipeline

set -e

# Logging
exec > >(tee -a /var/log/gsr-automation-startup.log)
exec 2>&1

echo "=========================================="
echo "GSR Automation TEST Pipeline - Startup Script"
echo "Started at: $(date)"
echo "=========================================="

# Update system
echo "Updating system packages..."
apt-get update
apt-get upgrade -y

# Install required packages
echo "Installing required packages..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    make \
    xvfb \
    x11vnc \
    xfce4 \
    xfce4-terminal \
    dbus-x11 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxshmfence1 \
    libpango-1.0-0 \
    libcairo2 \
    fonts-liberation \
    libnss3 \
    libnspr4

echo "✅ System packages installed"

# Start Xvfb for headed browser automation
echo "Starting Xvfb virtual display..."
Xvfb :0 -screen 0 1920x1080x24 &
export DISPLAY=:0
echo "DISPLAY set to :0"

# Wait for X server to be ready
sleep 2
if xdpyinfo -display :0 >/dev/null 2>&1; then
    echo "✅ X11 display server is running"
else
    echo "⚠️  Warning: X11 display server may not be fully initialized"
fi

# Start window manager (XFCE) for proper window handling
echo "Starting XFCE window manager..."
startxfce4 > /var/log/xfce4.log 2>&1 &
sleep 2

# Install Poetry
echo "Installing Poetry..."
curl -sSL https://install.python-poetry.org | python3 -
export PATH="/root/.local/bin:$PATH"

# Clone repository
echo "Cloning repository..."
cd /root
git clone https://github.com/Business-Facilitating/void_credit_retrieval_project.git void_credit_retrieval_project
cd void_credit_retrieval_project
git checkout dev

# Get .env from Secret Manager
echo "Fetching .env from Secret Manager..."
gcloud secrets versions access latest --secret="gsr-automation-env" > .env
chmod 600 .env

# Install dependencies
echo "Installing Python dependencies..."
poetry install

# Install Playwright browsers
echo "Installing Playwright browsers..."
poetry run playwright install chromium
poetry run playwright install-deps chromium

# Make scripts executable
chmod +x run_with_xvfb.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true

# Run the TEST pipeline (Steps 0-3 only)
echo "=========================================="
echo "Running GSR Automation TEST Pipeline (Steps 0-3)"
echo "=========================================="

if poetry run python -c "import os; from dotenv import load_dotenv; load_dotenv(); exit(0 if all([os.getenv(k) for k in ['CLICKHOUSE_HOST', 'CLICKHOUSE_USERNAME', 'CLICKHOUSE_PASSWORD']]) else 1)"; then
    echo "✅ Environment validation passed"

    # Run the test pipeline using the Makefile
    export DISPLAY=:0
    make -C deployment/option1_persistent_vm pipeline-test-steps0-3
    
    PIPELINE_EXIT_CODE=$?
    
    if [ $PIPELINE_EXIT_CODE -eq 0 ]; then
        echo "=========================================="
        echo "✅ TEST Pipeline completed successfully!"
        echo "Completed at: $(date)"
        echo "=========================================="
        
        # Signal success
        echo "SUCCESS" > /tmp/pipeline_status
        exit 0
    else
        echo "=========================================="
        echo "❌ TEST Pipeline failed with exit code: $PIPELINE_EXIT_CODE"
        echo "Failed at: $(date)"
        echo "=========================================="
        
        # Signal failure
        echo "FAILED" > /tmp/pipeline_status
        exit 1
    fi
else
    echo "❌ Environment validation failed"
    echo "FAILED" > /tmp/pipeline_status
    exit 1
fi

