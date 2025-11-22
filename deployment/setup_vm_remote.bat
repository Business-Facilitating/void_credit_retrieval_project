@echo off
REM Setup GSR Automation VM remotely
REM This script runs setup commands on the VM without interactive SSH

echo ========================================
echo GSR Automation VM Remote Setup
echo ========================================
echo.

REM Step 1: Copy setup script to VM
echo Step 1: Copying setup script to VM...
gcloud compute scp deployment/vm_setup.sh gsr-automation-vm:~/ --zone=us-central1-a --project=void-automation
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy setup script
    pause
    exit /b 1
)
echo ✓ Setup script copied
echo.

REM Step 2: Make script executable and run it
echo Step 2: Running setup script on VM...
gcloud compute ssh gsr-automation-vm --zone=us-central1-a --project=void-automation --command="chmod +x ~/vm_setup.sh && ~/vm_setup.sh"
if %errorlevel% neq 0 (
    echo ERROR: Setup script failed
    pause
    exit /b 1
)
echo.

echo ========================================
echo ✓ VM Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Connect to VM: deployment\connect_to_vm.bat
echo 2. Test pipeline: make test-step0
echo 3. Run full pipeline: make pipeline-full
echo.

pause

