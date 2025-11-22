# GSR Automation VM Setup - Step by Step
# This script runs each setup command individually on the VM

$VM_NAME = "gsr-automation-vm"
$ZONE = "us-central1-a"
$PROJECT = "void-automation"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GSR Automation VM Setup - Step by Step" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to run command on VM
function Run-VMCommand {
    param (
        [string]$Command,
        [string]$Description
    )
    
    Write-Host "Running: $Description" -ForegroundColor Yellow
    Write-Host "Command: $Command" -ForegroundColor Gray
    
    gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT --command=$Command
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Success" -ForegroundColor Green
    }
    else {
        Write-Host "✗ Failed" -ForegroundColor Red
        $continue = Read-Host "Continue anyway? (y/n)"
        if ($continue -ne "y") {
            exit 1
        }
    }
    Write-Host ""
}

# Step 1: Update system
Run-VMCommand -Command "sudo apt-get update -y" -Description "Step 1: Update package list"

# Step 2: Install Python
Run-VMCommand -Command "sudo apt-get install -y python3.10 python3.10-venv python3-pip" -Description "Step 2: Install Python 3.10"

# Step 3: Install Poetry
Run-VMCommand -Command "curl -sSL https://install.python-poetry.org | python3 -" -Description "Step 3: Install Poetry"

# Step 4: Add Poetry to PATH
Run-VMCommand -Command "echo 'export PATH=`"`$HOME/.local/bin:`$PATH`"' >> ~/.bashrc" -Description "Step 4: Add Poetry to PATH"

# Step 5: Install Git
Run-VMCommand -Command "sudo apt-get install -y git" -Description "Step 5: Install Git"

# Step 6: Install X11
Run-VMCommand -Command "sudo apt-get install -y xvfb x11vnc fluxbox" -Description "Step 6: Install X11 and Xvfb"

# Step 7: Clone repository
Run-VMCommand -Command 'cd ~ ; git clone https://github.com/Business-Facilitating/void_credit_retrieval_project.git' -Description "Step 7: Clone repository"

# Step 8: Checkout dev branch
Run-VMCommand -Command 'cd ~/void_credit_retrieval_project ; git checkout dev' -Description "Step 8: Checkout dev branch"

# Step 9: Load .env from Secret Manager
Run-VMCommand -Command 'cd ~/void_credit_retrieval_project ; gcloud secrets versions access latest --secret=gsr-automation-env > .env' -Description "Step 9: Load .env from Secret Manager"

# Step 10: Install Python dependencies
Run-VMCommand -Command 'cd ~/void_credit_retrieval_project ; ~/.local/bin/poetry install' -Description "Step 10: Install Python dependencies (this may take 5-10 minutes)"

# Step 11: Install Playwright browsers
Run-VMCommand -Command 'cd ~/void_credit_retrieval_project ; ~/.local/bin/poetry run playwright install chromium' -Description "Step 11: Install Playwright Chromium"

Run-VMCommand -Command 'cd ~/void_credit_retrieval_project ; ~/.local/bin/poetry run playwright install-deps' -Description "Step 12: Install Playwright dependencies"

# Step 13: Set up X11 display
Run-VMCommand -Command 'echo export DISPLAY=:99 >> ~/.bashrc' -Description "Step 13: Set DISPLAY environment variable"

Run-VMCommand -Command 'nohup Xvfb :99 -screen 0 1920x1080x24 >/dev/null 2>&1 &' -Description "Step 14: Start Xvfb"

# Step 14: Create directories
Run-VMCommand -Command 'cd ~/void_credit_retrieval_project ; mkdir -p data/output logs' -Description "Step 15: Create necessary directories"

# Step 15: Test GCS access
Run-VMCommand -Command 'gsutil ls gs://void_automation/' -Description "Step 16: Test GCS access"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ VM Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Connect to VM: gcloud compute ssh $VM_NAME --zone=$ZONE --project=$PROJECT"
Write-Host "2. Navigate to project: cd ~/void_credit_retrieval_project"
Write-Host "3. Test pipeline: make test-step0"
Write-Host "4. Run full pipeline: make pipeline-full"
Write-Host ""

