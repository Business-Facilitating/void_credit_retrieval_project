@echo off
REM GSR Automation VM Setup - Run Commands Sequentially
REM This script runs each setup command one by one

SET VM_NAME=gsr-automation-vm
SET ZONE=us-central1-a
SET PROJECT=void-automation

echo ========================================
echo GSR Automation VM Setup
echo ========================================
echo.

echo Step 1: Update system packages...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="sudo apt-get update -y"
echo.

echo Step 2: Install Python 3.10...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="sudo apt-get install -y python3.10 python3.10-venv python3-pip"
echo.

echo Step 3: Install Poetry...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="curl -sSL https://install.python-poetry.org | python3 -"
echo.

echo Step 4: Install Git...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="sudo apt-get install -y git"
echo.

echo Step 5: Install X11 and Xvfb...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="sudo apt-get install -y xvfb x11vnc fluxbox"
echo.

echo Step 6: Clone repository...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="git clone https://github.com/Business-Facilitating/void_credit_retrieval_project.git"
echo.

echo Step 7: Checkout dev branch...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="cd void_credit_retrieval_project && git checkout dev"
echo.

echo Step 8: Load .env from Secret Manager...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="cd void_credit_retrieval_project && gcloud secrets versions access latest --secret=gsr-automation-env > .env"
echo.

echo Step 9: Install Python dependencies (this may take 5-10 minutes)...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="cd void_credit_retrieval_project && ~/.local/bin/poetry install"
echo.

echo Step 10: Install Playwright Chromium...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="cd void_credit_retrieval_project && ~/.local/bin/poetry run playwright install chromium"
echo.

echo Step 11: Install Playwright dependencies...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="cd void_credit_retrieval_project && ~/.local/bin/poetry run playwright install-deps"
echo.

echo Step 12: Set up X11 display...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="echo 'export DISPLAY=:99' >> ~/.bashrc"
echo.

echo Step 13: Start Xvfb...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="nohup Xvfb :99 -screen 0 1920x1080x24 >/dev/null 2>&1 &"
echo.

echo Step 14: Create directories...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="cd void_credit_retrieval_project && mkdir -p data/output logs"
echo.

echo Step 15: Test GCS access...
gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="gsutil ls gs://void_automation/"
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Connect to VM: gcloud compute ssh %VM_NAME% --zone=%ZONE% --project=%PROJECT%
echo 2. Navigate to project: cd void_credit_retrieval_project
echo 3. Test pipeline: make test-step0
echo 4. Run full pipeline: make pipeline-full
echo.

pause

