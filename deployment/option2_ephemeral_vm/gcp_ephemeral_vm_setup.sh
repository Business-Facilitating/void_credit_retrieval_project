#!/bin/bash
# GSR Automation - GCP Ephemeral VM Setup
# This script creates a VM, runs the 4-step pipeline, and destroys the VM
# Pipeline: ClickHouse extraction → PeerDB extraction → Label filter → UPS void automation
# Designed to be triggered by Cloud Scheduler every other day
#
# Author: Gabriel Jerdhy Lapuz
# Project: gsr_automation

set -e  # Exit on error

# ============================================================================
# Configuration - UPDATE THESE VALUES
# ============================================================================

PROJECT_ID="your-gcp-project-id"              # Your GCP project ID
ZONE="us-central1-a"                          # GCP zone
VM_NAME="gsr-automation-runner-$(date +%Y%m%d-%H%M%S)"
MACHINE_TYPE="e2-medium"                      # 2 vCPU, 4GB RAM
BOOT_DISK_SIZE="20GB"
IMAGE_FAMILY="ubuntu-2204-lts"
IMAGE_PROJECT="ubuntu-os-cloud"

# Repository configuration
REPO_URL="https://github.com/YOUR_USERNAME/gsr_automation.git"
REPO_BRANCH="main"

# Secrets (stored in Google Secret Manager)
SECRET_ENV_FILE="gsr-automation-env"          # Name of secret containing .env file

# Notification email (optional)
NOTIFICATION_EMAIL="your-email@example.com"

# ============================================================================
# Colors for output
# ============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

send_notification() {
    local subject="$1"
    local message="$2"
    
    if [ -n "$NOTIFICATION_EMAIL" ]; then
        echo "$message" | gcloud compute instances send-email \
            --to="$NOTIFICATION_EMAIL" \
            --subject="$subject" \
            --project="$PROJECT_ID" 2>/dev/null || true
    fi
}

# ============================================================================
# Main Functions
# ============================================================================

create_startup_script() {
    log_info "Creating startup script..."
    
    cat > /tmp/startup-script.sh << 'STARTUP_SCRIPT_EOF'
#!/bin/bash
set -e

# Logging
exec > >(tee -a /var/log/gsr-automation-startup.log)
exec 2>&1

echo "=========================================="
echo "GSR Automation Pipeline - Startup Script"
echo "Started at: $(date)"
echo "=========================================="

# Update system
echo "Updating system packages..."
apt-get update -qq

# Install GUI/Desktop environment for headed browser automation
echo "Installing GUI components for headed mode..."
DEBIAN_FRONTEND=noninteractive apt-get install -y \
    xserver-xorg \
    x11-xserver-utils \
    xfce4 \
    xfce4-terminal \
    dbus-x11 \
    x11vnc \
    xvfb \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget

# Install system dependencies for Playwright
echo "Installing Playwright dependencies..."
apt-get install -y \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite0 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \
    libasound2 libatspi2.0-0 libxshmfence1

# Configure X11 display server
echo "Configuring X11 display server..."
export DISPLAY=:0
mkdir -p /tmp/.X11-unix
chmod 1777 /tmp/.X11-unix

# Start Xvfb (virtual framebuffer) for headed mode
echo "Starting Xvfb display server..."
Xvfb :0 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset > /var/log/xvfb.log 2>&1 &
XVFB_PID=$!
sleep 3

# Verify display is available
if xdpyinfo -display :0 >/dev/null 2>&1; then
    echo "✅ X11 display server started successfully (PID: $XVFB_PID)"
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
git clone REPO_URL_PLACEHOLDER gsr_automation
cd gsr_automation
git checkout REPO_BRANCH_PLACEHOLDER

# Get .env from Secret Manager
echo "Fetching .env from Secret Manager..."
gcloud secrets versions access latest --secret="SECRET_ENV_FILE_PLACEHOLDER" > .env
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

# Run the pipeline
echo "=========================================="
echo "Running GSR Automation Pipeline"
echo "=========================================="

if poetry run python -c "import os; from dotenv import load_dotenv; load_dotenv(); exit(0 if all([os.getenv(k) for k in ['CLICKHOUSE_HOST', 'CLICKHOUSE_USERNAME', 'CLICKHOUSE_PASSWORD']]) else 1)"; then
    echo "✅ Environment validation passed"
    
    # Run the full pipeline
    make pipeline-full
    
    PIPELINE_EXIT_CODE=$?
    
    if [ $PIPELINE_EXIT_CODE -eq 0 ]; then
        echo "=========================================="
        echo "✅ Pipeline completed successfully!"
        echo "Completed at: $(date)"
        echo "=========================================="
        
        # Upload results to Cloud Storage (optional)
        # gsutil -m cp -r data/output/* gs://YOUR_BUCKET/gsr-automation/$(date +%Y%m%d)/
        # gsutil -m cp -r logs/* gs://YOUR_BUCKET/gsr-automation/logs/$(date +%Y%m%d)/
        
        exit 0
    else
        echo "=========================================="
        echo "❌ Pipeline failed with exit code: $PIPELINE_EXIT_CODE"
        echo "Failed at: $(date)"
        echo "=========================================="
        exit 1
    fi
else
    echo "❌ Environment validation failed"
    exit 1
fi
STARTUP_SCRIPT_EOF

    # Replace placeholders
    sed -i "s|REPO_URL_PLACEHOLDER|$REPO_URL|g" /tmp/startup-script.sh
    sed -i "s|REPO_BRANCH_PLACEHOLDER|$REPO_BRANCH|g" /tmp/startup-script.sh
    sed -i "s|SECRET_ENV_FILE_PLACEHOLDER|$SECRET_ENV_FILE|g" /tmp/startup-script.sh
    
    log_success "Startup script created"
}

create_vm() {
    log_info "Creating ephemeral VM: $VM_NAME"
    
    gcloud compute instances create "$VM_NAME" \
        --project="$PROJECT_ID" \
        --zone="$ZONE" \
        --machine-type="$MACHINE_TYPE" \
        --boot-disk-size="$BOOT_DISK_SIZE" \
        --image-family="$IMAGE_FAMILY" \
        --image-project="$IMAGE_PROJECT" \
        --scopes=cloud-platform \
        --metadata-from-file=startup-script=/tmp/startup-script.sh \
        --metadata=google-logging-enabled=true \
        --preemptible \
        --no-restart-on-failure \
        --tags=gsr-automation
    
    log_success "VM created: $VM_NAME"
}

monitor_vm() {
    log_info "Monitoring VM execution..."
    
    local max_wait=1800  # 30 minutes max
    local elapsed=0
    local check_interval=30
    
    while [ $elapsed -lt $max_wait ]; do
        # Check if VM still exists
        if ! gcloud compute instances describe "$VM_NAME" \
            --project="$PROJECT_ID" \
            --zone="$ZONE" &>/dev/null; then
            log_warning "VM no longer exists"
            break
        fi
        
        # Check VM status
        local status=$(gcloud compute instances describe "$VM_NAME" \
            --project="$PROJECT_ID" \
            --zone="$ZONE" \
            --format="get(status)")
        
        log_info "VM Status: $status (elapsed: ${elapsed}s)"
        
        if [ "$status" = "TERMINATED" ]; then
            log_info "VM has terminated"
            break
        fi
        
        sleep $check_interval
        elapsed=$((elapsed + check_interval))
    done
    
    if [ $elapsed -ge $max_wait ]; then
        log_error "VM execution timeout (30 minutes)"
        return 1
    fi
}

get_vm_logs() {
    log_info "Fetching VM logs..."
    
    gcloud compute instances get-serial-port-output "$VM_NAME" \
        --project="$PROJECT_ID" \
        --zone="$ZONE" > "/tmp/${VM_NAME}-serial-output.log" 2>&1 || true
    
    log_success "Logs saved to: /tmp/${VM_NAME}-serial-output.log"
}

check_pipeline_success() {
    log_info "Checking pipeline execution status..."
    
    if grep -q "✅ Pipeline completed successfully!" "/tmp/${VM_NAME}-serial-output.log"; then
        log_success "Pipeline completed successfully!"
        return 0
    else
        log_error "Pipeline failed or did not complete"
        return 1
    fi
}

delete_vm() {
    log_info "Deleting VM: $VM_NAME"
    
    gcloud compute instances delete "$VM_NAME" \
        --project="$PROJECT_ID" \
        --zone="$ZONE" \
        --quiet
    
    log_success "VM deleted"
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    log_info "=========================================="
    log_info "GSR Automation - Ephemeral VM Execution"
    log_info "=========================================="
    
    # Create startup script
    create_startup_script
    
    # Create VM
    create_vm
    
    # Send start notification
    send_notification \
        "GSR Automation Started" \
        "VM $VM_NAME created and pipeline started at $(date)"
    
    # Monitor VM execution
    monitor_vm
    
    # Get logs
    get_vm_logs
    
    # Check if pipeline succeeded
    if check_pipeline_success; then
        log_success "Pipeline execution successful"
        send_notification \
            "GSR Automation Succeeded" \
            "Pipeline completed successfully at $(date). VM: $VM_NAME"
        EXIT_CODE=0
    else
        log_error "Pipeline execution failed"
        send_notification \
            "GSR Automation Failed" \
            "Pipeline failed at $(date). Check logs for VM: $VM_NAME"
        EXIT_CODE=1
    fi
    
    # Delete VM
    delete_vm
    
    # Cleanup
    rm -f /tmp/startup-script.sh
    
    log_info "=========================================="
    log_info "Execution complete"
    log_info "=========================================="
    
    exit $EXIT_CODE
}

# Trap errors
trap 'log_error "Script failed at line $LINENO"; delete_vm 2>/dev/null || true; exit 1' ERR

# Run main function
main "$@"

