#!/bin/bash
# GSR Automation - Pipeline Runner with Error Handling and Notifications
# Author: Gabriel Jerdhy Lapuz
# Project: gsr_automation
#
# This script runs the complete 3-step pipeline with enhanced error handling,
# logging, and optional email notifications.
#
# Usage:
#   ./scripts/run_pipeline_with_notifications.sh
#
# Features:
# - Sequential execution of all 3 pipeline steps
# - Comprehensive error handling
# - Detailed logging with timestamps
# - Email notifications on success/failure (optional)
# - Automatic cleanup of old files
# - Status reporting

# ============================================================================
# Configuration
# ============================================================================

# Project paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
OUTPUT_DIR="$PROJECT_ROOT/data/output"

# Timestamp for this run
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RUN_LOG="$LOG_DIR/pipeline_run_$TIMESTAMP.log"

# Email notification settings (optional)
ENABLE_EMAIL_NOTIFICATIONS=false
EMAIL_TO="your-email@example.com"
EMAIL_SUBJECT_PREFIX="[GSR Automation]"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$RUN_LOG"
}

log_success() {
    log "${GREEN}✅ $1${NC}"
}

log_error() {
    log "${RED}❌ $1${NC}"
}

log_warning() {
    log "${YELLOW}⚠️  $1${NC}"
}

log_info() {
    log "${BLUE}ℹ️  $1${NC}"
}

send_email_notification() {
    if [ "$ENABLE_EMAIL_NOTIFICATIONS" = true ]; then
        local subject="$EMAIL_SUBJECT_PREFIX $1"
        local body="$2"
        
        # Using mail command (requires mailutils package)
        if command -v mail &> /dev/null; then
            echo "$body" | mail -s "$subject" "$EMAIL_TO"
            log_info "Email notification sent to $EMAIL_TO"
        else
            log_warning "mail command not found. Install mailutils for email notifications."
        fi
    fi
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if we're in the project directory
    if [ ! -f "$PROJECT_ROOT/Makefile" ]; then
        log_error "Makefile not found. Are you in the correct directory?"
        return 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_error ".env file not found. Please create it with your credentials."
        return 1
    fi
    
    # Check if poetry is installed
    if ! command -v poetry &> /dev/null; then
        log_error "Poetry is not installed"
        return 1
    fi
    
    # Check if Xvfb is installed (required for Step 3)
    if ! command -v Xvfb &> /dev/null; then
        log_warning "Xvfb is not installed. Step 3 (void automation) will fail."
    fi
    
    log_success "All prerequisites met"
    return 0
}

create_directories() {
    mkdir -p "$LOG_DIR"
    mkdir -p "$OUTPUT_DIR"
    log_info "Directories created/verified"
}

run_step() {
    local step_num=$1
    local step_name=$2
    local make_target=$3
    
    log_info "============================================================"
    log_info "Step $step_num: $step_name"
    log_info "============================================================"
    
    cd "$PROJECT_ROOT" || return 1
    
    if make "$make_target" >> "$RUN_LOG" 2>&1; then
        log_success "Step $step_num completed successfully"
        return 0
    else
        log_error "Step $step_num failed"
        return 1
    fi
}

cleanup_old_files() {
    log_info "Cleaning up old files..."
    
    # Clean logs older than 7 days
    find "$LOG_DIR" -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true
    
    # Clean output files older than 30 days
    find "$OUTPUT_DIR" -name "*.csv" -type f -mtime +30 -delete 2>/dev/null || true
    find "$OUTPUT_DIR" -name "*.json" -type f -mtime +30 -delete 2>/dev/null || true
    find "$OUTPUT_DIR" -name "*.png" -type f -mtime +30 -delete 2>/dev/null || true
    
    log_success "Cleanup completed"
}

generate_summary() {
    local status=$1
    local duration=$2
    
    log_info "============================================================"
    log_info "Pipeline Summary"
    log_info "============================================================"
    log_info "Status: $status"
    log_info "Duration: $duration seconds"
    log_info "Log file: $RUN_LOG"
    
    # Count output files
    if [ -d "$OUTPUT_DIR" ]; then
        local csv_count=$(find "$OUTPUT_DIR" -name "*.csv" -type f -mtime -1 | wc -l)
        local json_count=$(find "$OUTPUT_DIR" -name "*.json" -type f -mtime -1 | wc -l)
        local png_count=$(find "$OUTPUT_DIR" -name "*.png" -type f -mtime -1 | wc -l)
        
        log_info "Output files created in last 24 hours:"
        log_info "  - CSV files: $csv_count"
        log_info "  - JSON files: $json_count"
        log_info "  - Screenshots: $png_count"
    fi
    
    log_info "============================================================"
}

# ============================================================================
# Main Pipeline Execution
# ============================================================================

main() {
    local start_time=$(date +%s)
    
    log_info "============================================================"
    log_info "GSR Automation Pipeline - Starting"
    log_info "============================================================"
    log_info "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "Log file: $RUN_LOG"
    log_info "============================================================"
    
    # Create necessary directories
    create_directories
    
    # Check prerequisites
    if ! check_prerequisites; then
        log_error "Prerequisites check failed. Aborting."
        send_email_notification "Pipeline Failed - Prerequisites" "Prerequisites check failed. See log: $RUN_LOG"
        exit 1
    fi
    
    # Step 1: Extract carrier invoice data from ClickHouse
    if ! run_step 1 "Extract Carrier Invoice Data" "pipeline-step1"; then
        log_error "Pipeline failed at Step 1"
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        generate_summary "FAILED at Step 1" "$duration"
        send_email_notification "Pipeline Failed - Step 1" "Step 1 (DLT Pipeline) failed. See log: $RUN_LOG"
        exit 1
    fi
    
    # Wait before Step 2
    log_info "Waiting 60 seconds before Step 2..."
    sleep 60
    
    # Step 2: Filter tracking numbers with label-only status
    if ! run_step 2 "Filter Label-Only Tracking Numbers" "pipeline-step2"; then
        log_error "Pipeline failed at Step 2"
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        generate_summary "FAILED at Step 2" "$duration"
        send_email_notification "Pipeline Failed - Step 2" "Step 2 (Label Filter) failed. See log: $RUN_LOG"
        exit 1
    fi
    
    # Wait before Step 3
    log_info "Waiting 120 seconds before Step 3..."
    sleep 120
    
    # Step 3: Automated UPS shipment void
    if ! run_step 3 "Automated UPS Shipment Void" "pipeline-step3"; then
        log_error "Pipeline failed at Step 3"
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        generate_summary "FAILED at Step 3" "$duration"
        send_email_notification "Pipeline Failed - Step 3" "Step 3 (Void Automation) failed. See log: $RUN_LOG"
        exit 1
    fi
    
    # All steps completed successfully
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "All pipeline steps completed successfully!"
    
    # Cleanup old files
    cleanup_old_files
    
    # Generate summary
    generate_summary "SUCCESS" "$duration"
    
    # Send success notification
    send_email_notification "Pipeline Completed Successfully" "All 3 steps completed in $duration seconds. See log: $RUN_LOG"
    
    log_info "Pipeline execution complete"
    exit 0
}

# ============================================================================
# Script Entry Point
# ============================================================================

# Trap errors and interrupts
trap 'log_error "Pipeline interrupted or failed"; exit 1' INT TERM ERR

# Run main function
main "$@"

