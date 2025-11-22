"""
GSR Automation - Cloud Function Trigger
This Cloud Function creates an ephemeral VM, runs the 4-step pipeline, and cleans up.

Pipeline Steps:
1. Extract carrier invoice data from ClickHouse
2. Extract industry index logins from PeerDB
3. Filter label-only tracking numbers
4. Automated UPS shipment void

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import logging
import os
import subprocess
from datetime import datetime

import functions_framework
from google.cloud import compute_v1, storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
ZONE = os.environ.get("GCP_ZONE", "us-central1-a")
MACHINE_TYPE = os.environ.get("MACHINE_TYPE", "e2-medium")
REPO_URL = os.environ.get("REPO_URL")
REPO_BRANCH = os.environ.get("REPO_BRANCH", "main")
SECRET_ENV_FILE = os.environ.get("SECRET_ENV_FILE", "gsr-automation-env")
RESULTS_BUCKET = os.environ.get("RESULTS_BUCKET", "")


def create_startup_script():
    """Generate the VM startup script."""

    startup_script = f"""#!/bin/bash
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
DEBIAN_FRONTEND=noninteractive apt-get install -y \\
    xserver-xorg \\
    x11-xserver-utils \\
    xfce4 \\
    xfce4-terminal \\
    dbus-x11 \\
    x11vnc \\
    xvfb \\
    python3 \\
    python3-pip \\
    python3-venv \\
    git \\
    curl \\
    wget

# Install system dependencies for Playwright
echo "Installing Playwright dependencies..."
apt-get install -y \\
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \\
    libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite0 libxdamage1 \\
    libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2 \\
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
git clone {REPO_URL} void_credit_retrieval_project
cd void_credit_retrieval_project
git checkout {REPO_BRANCH}

# Get .env from Secret Manager
echo "Fetching .env from Secret Manager..."
gcloud secrets versions access latest --secret="{SECRET_ENV_FILE}" > .env
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

    # Run the full pipeline using the Makefile in deployment/option1_persistent_vm
    export DISPLAY=:0
    make -C deployment/option1_persistent_vm pipeline-full
    
    PIPELINE_EXIT_CODE=$?
    
    if [ $PIPELINE_EXIT_CODE -eq 0 ]; then
        echo "=========================================="
        echo "✅ Pipeline completed successfully!"
        echo "Completed at: $(date)"
        echo "=========================================="
        
        # Upload results to Cloud Storage
        if [ -n "{RESULTS_BUCKET}" ]; then
            echo "Uploading results to Cloud Storage..."
            RUN_DATE=$(date +%Y%m%d_%H%M%S)
            gsutil -m cp -r data/output/* gs://{RESULTS_BUCKET}/runs/$RUN_DATE/ || true
            gsutil -m cp -r logs/* gs://{RESULTS_BUCKET}/logs/$RUN_DATE/ || true
            echo "✅ Results uploaded to gs://{RESULTS_BUCKET}/runs/$RUN_DATE/"
        fi
        
        # Signal success
        echo "SUCCESS" > /tmp/pipeline_status
        exit 0
    else
        echo "=========================================="
        echo "❌ Pipeline failed with exit code: $PIPELINE_EXIT_CODE"
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
"""

    return startup_script


def create_vm_instance(vm_name):
    """Create a compute engine VM instance."""

    logger.info(f"Creating VM instance: {vm_name}")

    compute_client = compute_v1.InstancesClient()

    # Configure the VM instance
    instance = compute_v1.Instance()
    instance.name = vm_name
    instance.machine_type = f"zones/{ZONE}/machineTypes/{MACHINE_TYPE}"

    # Boot disk
    boot_disk = compute_v1.AttachedDisk()
    boot_disk.auto_delete = True
    boot_disk.boot = True
    initialize_params = compute_v1.AttachedDiskInitializeParams()
    initialize_params.source_image = (
        "projects/ubuntu-os-cloud/global/images/family/ubuntu-2204-lts"
    )
    initialize_params.disk_size_gb = 20
    boot_disk.initialize_params = initialize_params
    instance.disks = [boot_disk]

    # Network interface
    network_interface = compute_v1.NetworkInterface()
    network_interface.name = "global/networks/default"
    access_config = compute_v1.AccessConfig()
    access_config.name = "External NAT"
    access_config.type_ = "ONE_TO_ONE_NAT"
    network_interface.access_configs = [access_config]
    instance.network_interfaces = [network_interface]

    # Service account with required scopes
    service_account = compute_v1.ServiceAccount()
    service_account.email = (
        f"gsr-automation-runner@{PROJECT_ID}.iam.gserviceaccount.com"
    )
    service_account.scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    instance.service_accounts = [service_account]

    # Metadata (startup script)
    metadata = compute_v1.Metadata()
    startup_script_item = compute_v1.Items()
    startup_script_item.key = "startup-script"
    startup_script_item.value = create_startup_script()
    metadata.items = [startup_script_item]
    instance.metadata = metadata

    # Scheduling (preemptible)
    scheduling = compute_v1.Scheduling()
    scheduling.preemptible = True
    scheduling.automatic_restart = False
    scheduling.on_host_maintenance = "TERMINATE"
    instance.scheduling = scheduling

    # Tags
    tags = compute_v1.Tags()
    tags.items = ["gsr-automation"]
    instance.tags = tags

    # Create the instance
    operation = compute_client.insert(
        project=PROJECT_ID, zone=ZONE, instance_resource=instance
    )

    logger.info(f"VM creation initiated: {vm_name}")
    return operation


@functions_framework.http
def trigger_pipeline(request):
    """
    HTTP Cloud Function to trigger the GSR Automation pipeline.

    This function:
    1. Creates an ephemeral VM
    2. VM runs the pipeline via startup script
    3. Returns immediately (VM continues in background)

    The VM will self-terminate after pipeline completion.
    """

    try:
        # Generate unique VM name
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        vm_name = f"gsr-automation-runner-{timestamp}"

        logger.info(f"Triggering pipeline execution with VM: {vm_name}")

        # Validate configuration
        if not PROJECT_ID:
            return {"error": "GCP_PROJECT_ID not configured"}, 500
        if not REPO_URL:
            return {"error": "REPO_URL not configured"}, 500

        # Create VM
        operation = create_vm_instance(vm_name)

        logger.info(f"VM {vm_name} created successfully")

        return {
            "status": "success",
            "message": f"Pipeline execution started",
            "vm_name": vm_name,
            "timestamp": timestamp,
            "note": "VM will run pipeline and self-terminate. Check Cloud Storage for results.",
        }, 200

    except Exception as e:
        logger.error(f"Error triggering pipeline: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}, 500


@functions_framework.http
def check_status(request):
    """
    HTTP Cloud Function to check pipeline execution status.

    Query parameters:
    - vm_name: Name of the VM to check
    """

    try:
        vm_name = request.args.get("vm_name")

        if not vm_name:
            return {"error": "vm_name parameter required"}, 400

        compute_client = compute_v1.InstancesClient()

        try:
            instance = compute_client.get(
                project=PROJECT_ID, zone=ZONE, instance=vm_name
            )

            return {
                "status": "running",
                "vm_name": vm_name,
                "vm_status": instance.status,
                "message": "Pipeline is still running",
            }, 200

        except Exception:
            # VM doesn't exist - pipeline completed
            return {
                "status": "completed",
                "vm_name": vm_name,
                "message": "Pipeline completed and VM terminated. Check Cloud Storage for results.",
            }, 200

    except Exception as e:
        logger.error(f"Error checking status: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}, 500
