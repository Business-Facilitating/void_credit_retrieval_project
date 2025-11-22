@echo off
REM Connect to GSR Automation VM
REM This script uses gcloud to establish SSH connection

echo ========================================
echo Connecting to GSR Automation VM
echo ========================================
echo.
echo VM Details:
echo   Name: gsr-automation-vm
echo   Zone: us-central1-a
echo   External IP: 34.61.113.45
echo.
echo Connecting...
echo.

gcloud compute ssh gsr-automation-vm --zone=us-central1-a --project=void-automation

pause

