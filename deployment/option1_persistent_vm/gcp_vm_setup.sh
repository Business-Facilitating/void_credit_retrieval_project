#!/bin/bash
# GSR Automation - GCP VM Quick Setup Script
# Author: Gabriel Jerdhy Lapuz
# Project: gsr_automation
#
# This script automates the complete setup of the GSR Automation pipeline
# on a Google Cloud Platform Linux VM.
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/gsr_automation/main/scripts/gcp_vm_setup.sh | bash
#   OR
#   ./scripts/gcp_vm_setup.sh

set -e  # Exit on error

# ============================================================================
# Configuration
# ============================================================================

PROJECT_NAME="gsr_automation"
REPO_URL="https://github.com/YOUR_USERNAME/gsr_automation.git"  # UPDATE THIS
INSTALL_DIR="$HOME/$PROJECT_NAME"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_header() {
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}============================================================${NC}"
}

# ============================================================================
# Installation Steps
# ============================================================================

install_system_dependencies() {
    print_header "Installing System Dependencies"
    
    log_info "Updating package list..."
    sudo apt-get update -qq
    
    log_info "Installing Python 3, pip, and development tools..."
    sudo apt-get install -y python3 python3-pip python3-venv git curl wget
    
    log_info "Installing Xvfb (virtual display server)..."
    sudo apt-get install -y xvfb
    
    log_info "Installing Playwright system dependencies..."
    sudo apt-get install -y \
        libnss3 \
        libnspr4 \
        libatk1.0-0 \
        libatk-bridge2.0-0 \
        libcups2 \
        libdrm2 \
        libdbus-1-3 \
        libxkbcommon0 \
        libxcomposite0 \
        libxdamage1 \
        libxfixes3 \
        libxrandr2 \
        libgbm1 \
        libpango-1.0-0 \
        libcairo2 \
        libasound2 \
        libatspi2.0-0 \
        libxshmfence1
    
    log_success "System dependencies installed"
}

install_poetry() {
    print_header "Installing Poetry"
    
    if command -v poetry &> /dev/null; then
        log_warning "Poetry is already installed"
        poetry --version
    else
        log_info "Installing Poetry..."
        curl -sSL https://install.python-poetry.org | python3 -
        
        # Add Poetry to PATH
        export PATH="$HOME/.local/bin:$PATH"
        
        # Add to .bashrc for persistence
        if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' ~/.bashrc; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        fi
        
        log_success "Poetry installed"
        poetry --version
    fi
}

clone_repository() {
    print_header "Cloning Repository"
    
    if [ -d "$INSTALL_DIR" ]; then
        log_warning "Directory $INSTALL_DIR already exists"
        log_info "Pulling latest changes..."
        cd "$INSTALL_DIR"
        git pull
    else
        log_info "Cloning repository to $INSTALL_DIR..."
        git clone "$REPO_URL" "$INSTALL_DIR"
        cd "$INSTALL_DIR"
    fi
    
    log_success "Repository ready at $INSTALL_DIR"
}

setup_project() {
    print_header "Setting Up Project"
    
    cd "$INSTALL_DIR"
    
    log_info "Installing Python dependencies with Poetry..."
    poetry install
    
    log_info "Installing Playwright browsers..."
    poetry run playwright install chromium
    
    log_info "Installing Playwright system dependencies..."
    poetry run playwright install-deps chromium
    
    log_success "Project dependencies installed"
}

setup_environment() {
    print_header "Setting Up Environment"
    
    cd "$INSTALL_DIR"
    
    if [ -f ".env" ]; then
        log_warning ".env file already exists"
        log_info "Backing up existing .env to .env.backup"
        cp .env .env.backup
    fi
    
    log_info "Creating .env file..."
    log_warning "You will need to edit .env and add your credentials"
    
    # Create basic .env template if it doesn't exist
    if [ ! -f ".env" ]; then
        cat > .env << 'EOF'
# GSR Automation Environment Variables
# IMPORTANT: Fill in your actual credentials below

# ClickHouse Database Configuration
CLICKHOUSE_HOST=your-clickhouse-host
CLICKHOUSE_PORT=8443
CLICKHOUSE_USERNAME=your-username
CLICKHOUSE_PASSWORD=your-password
CLICKHOUSE_DATABASE=peerdb
CLICKHOUSE_SECURE=True

# DLT Pipeline Configuration
DLT_TRANSACTION_START_CUTOFF_DAYS=89
DLT_TRANSACTION_END_CUTOFF_DAYS=85
DLT_CLICKHOUSE_BATCH_SIZE=50000

# UPS Web Login Configuration
UPS_WEB_USERNAME=your-ups-username
UPS_WEB_PASSWORD=your-ups-password

# Output Configuration
OUTPUT_DIR=data/output
EOF
        chmod 600 .env
        log_success ".env file created (remember to edit it with your credentials)"
    fi
}

make_scripts_executable() {
    print_header "Making Scripts Executable"
    
    cd "$INSTALL_DIR"
    
    log_info "Setting execute permissions on scripts..."
    chmod +x run_with_xvfb.sh 2>/dev/null || true
    chmod +x scripts/*.sh 2>/dev/null || true
    
    log_success "Scripts are now executable"
}

run_setup() {
    print_header "Running Project Setup"
    
    cd "$INSTALL_DIR"
    
    log_info "Running make setup..."
    make setup
    
    log_success "Project setup complete"
}

test_installation() {
    print_header "Testing Installation"
    
    cd "$INSTALL_DIR"
    
    log_info "Checking dependencies..."
    make check-deps
    
    log_info "Checking environment configuration..."
    make env-check || log_warning "Environment check failed - you need to edit .env with your credentials"
    
    log_success "Installation test complete"
}

print_next_steps() {
    print_header "Installation Complete!"
    
    echo ""
    log_success "GSR Automation has been installed to: $INSTALL_DIR"
    echo ""
    log_warning "IMPORTANT: Next Steps"
    echo ""
    echo "1. Edit the .env file with your credentials:"
    echo "   ${BLUE}nano $INSTALL_DIR/.env${NC}"
    echo ""
    echo "2. Test individual pipeline steps:"
    echo "   ${BLUE}cd $INSTALL_DIR${NC}"
    echo "   ${BLUE}make test-step1${NC}  # Test ClickHouse extraction"
    echo "   ${BLUE}make test-step2${NC}  # Test label-only filter"
    echo "   ${BLUE}make test-step3${NC}  # Test UPS web login"
    echo ""
    echo "3. Run the full pipeline:"
    echo "   ${BLUE}make pipeline-full${NC}"
    echo ""
    echo "4. Setup automated scheduling:"
    echo "   ${BLUE}crontab -e${NC}"
    echo "   Add this line:"
    echo "   ${BLUE}0 2 * * * cd $INSTALL_DIR && make pipeline-full >> logs/cron_pipeline_full.log 2>&1${NC}"
    echo ""
    echo "5. View available commands:"
    echo "   ${BLUE}make help${NC}"
    echo ""
    log_info "For detailed documentation, see:"
    echo "   - Quick Reference: ${BLUE}docs/DEPLOYMENT_QUICK_REFERENCE.md${NC}"
    echo "   - Full Guide: ${BLUE}docs/MAKEFILE_CRON_DEPLOYMENT.md${NC}"
    echo "   - Cron Examples: ${BLUE}crontab.txt${NC}"
    echo ""
    print_header "Happy Automating! 🚀"
}

# ============================================================================
# Main Installation Flow
# ============================================================================

main() {
    print_header "GSR Automation - GCP VM Setup"
    
    log_info "Starting installation..."
    log_info "This will install all dependencies and setup the project"
    echo ""
    
    # Check if running on Linux
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_error "This script is designed for Linux systems"
        log_error "Current OS: $OSTYPE"
        exit 1
    fi
    
    # Run installation steps
    install_system_dependencies
    install_poetry
    clone_repository
    setup_project
    setup_environment
    make_scripts_executable
    run_setup
    test_installation
    
    # Print next steps
    print_next_steps
}

# ============================================================================
# Script Entry Point
# ============================================================================

# Trap errors
trap 'log_error "Installation failed at line $LINENO"; exit 1' ERR

# Run main function
main "$@"

