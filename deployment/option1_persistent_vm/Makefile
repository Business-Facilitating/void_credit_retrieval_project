# GSR Automation - Makefile for GCP Linux VM Deployment
# Author: Gabriel Jerdhy Lapuz
# Project: gsr_automation
#
# This Makefile provides commands for running the data pipeline on a GCP Linux VM.
# The pipeline consists of five sequential jobs:
# 0. Whitelist VM IP address via Slack (slack_whitelist_ip.py)
# 1. Extract carrier invoice data from ClickHouse (dlt_pipeline_examples.py)
# 2. Extract industry index logins from PeerDB (peerdb_pipeline.py)
# 3. Filter tracking numbers with label-only status (ups_label_only_filter.py)
# 4. Perform automated UPS shipment void (ups_shipment_void_automation.py)

# ============================================================================
# Configuration
# ============================================================================

# Python and Poetry
PYTHON := python3
POETRY := poetry
POETRY_RUN := $(POETRY) run python

# Project paths
PROJECT_ROOT := $(shell cd ../.. && pwd)
SRC_DIR := $(PROJECT_ROOT)/src/src
DATA_OUTPUT_DIR := $(PROJECT_ROOT)/data/output
LOG_DIR := $(PROJECT_ROOT)/logs

# Export environment variables for scripts
export OUTPUT_DIR := $(DATA_OUTPUT_DIR)
export DUCKDB_PATH := $(DATA_OUTPUT_DIR)/carrier_invoice_extraction.duckdb

# Scripts
SCRIPT_SLACK_WHITELIST := $(SRC_DIR)/slack_whitelist_ip.py
SCRIPT_DLT_PIPELINE := $(SRC_DIR)/dlt_pipeline_examples.py
SCRIPT_PEERDB_PIPELINE := $(SRC_DIR)/peerdb_pipeline.py
SCRIPT_LABEL_FILTER := $(SRC_DIR)/ups_label_only_filter.py
SCRIPT_VOID_AUTOMATION := $(SRC_DIR)/ups_shipment_void_automation.py
SCRIPT_GCS_UPLOAD := $(SRC_DIR)/gcs_upload.py

# Display configuration for headed browser automation
# Note: Xvfb should be started by the deployment script before running the pipeline
# The browser will run in headed mode with visible windows on the virtual display
DISPLAY_NUM := 0
SCREEN_RESOLUTION := 1920x1080x24

# Timing configuration (in seconds)
DELAY_AFTER_WHITELIST := 300  # 5 minutes for IP whitelist to propagate
DELAY_AFTER_PIPELINE := 60
DELAY_AFTER_PEERDB := 60
DELAY_AFTER_FILTER := 120

# Timestamp for logs
TIMESTAMP := $(shell date +%Y%m%d_%H%M%S)

# Colors for output
GREEN := \033[0;32m
RED := \033[0;31m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# ============================================================================
# Default target
# ============================================================================

.PHONY: help
help:
	@echo "$(GREEN)============================================================$(NC)"
	@echo "$(GREEN)GSR Automation - GCP Linux VM Deployment$(NC)"
	@echo "$(GREEN)============================================================$(NC)"
	@echo ""
	@echo "$(YELLOW)Available targets:$(NC)"
	@echo ""
	@echo "  $(BLUE)setup$(NC)              - Install dependencies and setup environment"
	@echo "  $(BLUE)check-deps$(NC)         - Check if all dependencies are installed"
	@echo ""
	@echo "  $(BLUE)pipeline-step0$(NC)     - Run Step 0: Whitelist VM IP address via Slack"
	@echo "  $(BLUE)pipeline-step1$(NC)     - Run Step 1: Extract carrier invoice data from ClickHouse"
	@echo "  $(BLUE)pipeline-step2$(NC)     - Run Step 2: Extract industry index logins from PeerDB"
	@echo "  $(BLUE)pipeline-step3$(NC)     - Run Step 3: Filter tracking numbers with label-only status"
	@echo "  $(BLUE)pipeline-step4$(NC)     - Run Step 4: Automated UPS shipment void (headed mode with GUI)"
	@echo ""
	@echo "  $(BLUE)pipeline-full$(NC)      - Run all five pipeline steps sequentially"
	@echo "  $(BLUE)pipeline-full-bg$(NC)   - Run full pipeline in background with logging"
	@echo ""
	@echo "  $(BLUE)test-step0$(NC)         - Test Step 0 (IP whitelisting)"
	@echo "  $(BLUE)test-step1$(NC)         - Test Step 1 (DLT pipeline)"
	@echo "  $(BLUE)test-step2$(NC)         - Test Step 2 (PeerDB pipeline)"
	@echo "  $(BLUE)test-step3$(NC)         - Test Step 3 (Label filter)"
	@echo "  $(BLUE)test-step4$(NC)         - Test Step 4 (Void automation in headed mode)"
	@echo ""
	@echo "  $(BLUE)logs$(NC)               - View recent pipeline logs"
	@echo "  $(BLUE)clean-logs$(NC)         - Clean old log files (>7 days)"
	@echo "  $(BLUE)clean-output$(NC)       - Clean old output files (>30 days)"
	@echo "  $(BLUE)clean-all$(NC)          - Clean all logs and output files"
	@echo ""
	@echo "  $(BLUE)status$(NC)             - Show pipeline status and recent runs"
	@echo "  $(BLUE)help$(NC)               - Show this help message"
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make setup              # First-time setup"
	@echo "  make pipeline-full      # Run complete pipeline"
	@echo "  make pipeline-step1     # Run only Step 1"
	@echo "  make logs               # View recent logs"
	@echo ""

# ============================================================================
# Setup and dependency checking
# ============================================================================

.PHONY: setup
setup: check-deps
	@echo "$(GREEN)Setting up GSR Automation...$(NC)"
	@mkdir -p $(LOG_DIR)
	@mkdir -p $(DATA_OUTPUT_DIR)
	@echo "$(GREEN)✅ Directories created$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)⚠️  .env file not found. Please create it with your credentials.$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ Environment file found$(NC)"
	@$(POETRY) install
	@echo "$(GREEN)✅ Dependencies installed$(NC)"
	@echo "$(GREEN)✅ Setup complete!$(NC)"

.PHONY: check-deps
check-deps:
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@command -v $(PYTHON) >/dev/null 2>&1 || { echo "$(RED)❌ Python 3 is not installed$(NC)"; exit 1; }
	@echo "$(GREEN)✅ Python 3 found$(NC)"
	@command -v $(POETRY) >/dev/null 2>&1 || { echo "$(RED)❌ Poetry is not installed$(NC)"; exit 1; }
	@echo "$(GREEN)✅ Poetry found$(NC)"
	@command -v Xvfb >/dev/null 2>&1 || { echo "$(YELLOW)⚠️  Xvfb not found (required for X11 display)$(NC)"; }
	@echo "$(GREEN)✅ All required dependencies found$(NC)"

# ============================================================================
# Pipeline Steps
# ============================================================================

.PHONY: pipeline-step0
pipeline-step0:
	@echo "$(GREEN)============================================================$(NC)"
	@echo "$(GREEN)🔐 Pipeline Step 0: Whitelist VM IP Address via Slack$(NC)"
	@echo "$(GREEN)============================================================$(NC)"
	@mkdir -p $(LOG_DIR)
	@$(POETRY_RUN) $(SCRIPT_SLACK_WHITELIST) 2>&1 | tee $(LOG_DIR)/step0_slack_whitelist_$(TIMESTAMP).log
	@if [ $$? -eq 0 ]; then \
		echo "$(GREEN)✅ Step 0 completed successfully$(NC)"; \
	else \
		echo "$(RED)❌ Step 0 failed - IP whitelisting unsuccessful$(NC)"; \
		exit 1; \
	fi

.PHONY: pipeline-step1
pipeline-step1:
	@echo "$(GREEN)============================================================$(NC)"
	@echo "$(GREEN)🚀 Pipeline Step 1: Extract Carrier Invoice Data$(NC)"
	@echo "$(GREEN)============================================================$(NC)"
	@mkdir -p $(LOG_DIR)
	@OUTPUT_DIR=$(DATA_OUTPUT_DIR) $(POETRY_RUN) $(SCRIPT_DLT_PIPELINE) 2>&1 | tee $(LOG_DIR)/step1_dlt_pipeline_$(TIMESTAMP).log
	@if [ $$? -eq 0 ]; then \
		echo "$(GREEN)✅ Step 1 completed successfully$(NC)"; \
		echo "$(BLUE)📤 Uploading Step 1 outputs to GCS...$(NC)"; \
		if [ -f $(DATA_OUTPUT_DIR)/carrier_invoice_extraction.duckdb ]; then \
			$(POETRY_RUN) $(SCRIPT_GCS_UPLOAD) --step 1 --files $(DATA_OUTPUT_DIR)/carrier_invoice_extraction.duckdb || echo "$(YELLOW)⚠️  GCS upload failed (continuing pipeline)$(NC)"; \
		else \
			echo "$(YELLOW)⚠️  No Step 1 output files found to upload$(NC)"; \
		fi; \
	else \
		echo "$(RED)❌ Step 1 failed$(NC)"; \
		exit 1; \
	fi

.PHONY: pipeline-step2
pipeline-step2:
	@echo "$(GREEN)============================================================$(NC)"
	@echo "$(GREEN)📊 Pipeline Step 2: Extract Industry Index Logins from PeerDB$(NC)"
	@echo "$(GREEN)============================================================$(NC)"
	@mkdir -p $(LOG_DIR)
	@OUTPUT_DIR=$(DATA_OUTPUT_DIR) $(POETRY_RUN) $(SCRIPT_PEERDB_PIPELINE) 2>&1 | tee $(LOG_DIR)/step2_peerdb_pipeline_$(TIMESTAMP).log
	@if [ $$? -eq 0 ]; then \
		echo "$(GREEN)✅ Step 2 completed successfully$(NC)"; \
		echo "$(BLUE)📤 Uploading Step 2 outputs to GCS...$(NC)"; \
		FILES=$$(ls $(DATA_OUTPUT_DIR)/peerdb_industry_index_logins_*.csv 2>/dev/null); \
		if [ -n "$$FILES" ]; then \
			$(POETRY_RUN) $(SCRIPT_GCS_UPLOAD) --step 2 --files $$FILES || echo "$(YELLOW)⚠️  GCS upload failed (continuing pipeline)$(NC)"; \
		else \
			echo "$(YELLOW)⚠️  No Step 2 output files found to upload$(NC)"; \
		fi; \
	else \
		echo "$(YELLOW)⚠️  Step 2 failed - continuing with pipeline (login credentials may not be available)$(NC)"; \
	fi

.PHONY: pipeline-step3
pipeline-step3:
	@echo "$(GREEN)============================================================$(NC)"
	@echo "$(GREEN)🔍 Pipeline Step 3: Filter Label-Only Tracking Numbers$(NC)"
	@echo "$(GREEN)============================================================$(NC)"
	@mkdir -p $(LOG_DIR)
	@OUTPUT_DIR=$(DATA_OUTPUT_DIR) DUCKDB_PATH=$(DATA_OUTPUT_DIR)/carrier_invoice_extraction.duckdb $(POETRY_RUN) $(SCRIPT_LABEL_FILTER) 2>&1 | tee $(LOG_DIR)/step3_label_filter_$(TIMESTAMP).log
	@if [ $$? -eq 0 ]; then \
		echo "$(GREEN)✅ Step 3 completed successfully$(NC)"; \
		echo "$(BLUE)📤 Uploading Step 3 outputs to GCS...$(NC)"; \
		FILES=$$(ls $(DATA_OUTPUT_DIR)/ups_label_only_tracking_range_*.csv $(DATA_OUTPUT_DIR)/ups_label_only_filter_range_*.json 2>/dev/null); \
		if [ -n "$$FILES" ]; then \
			$(POETRY_RUN) $(SCRIPT_GCS_UPLOAD) --step 3 --files $$FILES || echo "$(YELLOW)⚠️  GCS upload failed (continuing pipeline)$(NC)"; \
		else \
			echo "$(YELLOW)⚠️  No Step 3 output files found to upload$(NC)"; \
		fi; \
	else \
		echo "$(RED)❌ Step 3 failed$(NC)"; \
		exit 1; \
	fi

.PHONY: pipeline-step4
pipeline-step4:
	@echo "$(GREEN)============================================================$(NC)"
	@echo "$(GREEN)🌐 Pipeline Step 4: Automated UPS Shipment Void$(NC)"
	@echo "$(GREEN)============================================================$(NC)"
	@mkdir -p $(LOG_DIR)
	@echo "$(BLUE)Running UPS void automation in headed mode...$(NC)"
	@echo "$(YELLOW)Note: Using headed mode with visible browser (requires X11 display)$(NC)"
	@if [ -z "$$DISPLAY" ]; then \
		echo "$(YELLOW)⚠️  DISPLAY not set, defaulting to :0$(NC)"; \
		export DISPLAY=:0; \
	fi; \
	echo "$(GREEN)✅ Using display: $$DISPLAY$(NC)"; \
	OUTPUT_DIR=$(DATA_OUTPUT_DIR) DUCKDB_PATH=$(DATA_OUTPUT_DIR)/carrier_invoice_extraction.duckdb PEERDB_DUCKDB_PATH=$(PROJECT_ROOT)/peerdb_industry_index_logins.duckdb $(POETRY_RUN) $(SCRIPT_VOID_AUTOMATION) --headed 2>&1 | tee $(LOG_DIR)/step4_void_automation_$(TIMESTAMP).log; \
	EXIT_CODE=$$?; \
	if [ $$EXIT_CODE -eq 0 ]; then \
		echo "$(GREEN)✅ Step 4 completed successfully$(NC)"; \
		echo "$(BLUE)📤 Uploading Step 4 outputs to GCS (including screenshots)...$(NC)"; \
		FILES=$$(ls $(DATA_OUTPUT_DIR)/ups_void_automation_results_*.csv $(DATA_OUTPUT_DIR)/*.png 2>/dev/null); \
		if [ -n "$$FILES" ]; then \
			$(POETRY_RUN) $(SCRIPT_GCS_UPLOAD) --step 4 --files $$FILES || echo "$(YELLOW)⚠️  GCS upload failed (continuing pipeline)$(NC)"; \
		else \
			echo "$(YELLOW)⚠️  No Step 4 output files found to upload$(NC)"; \
		fi; \
	else \
		echo "$(RED)❌ Step 4 failed$(NC)"; \
		exit 1; \
	fi

# ============================================================================
# Full Pipeline Execution
# ============================================================================

.PHONY: pipeline-full
pipeline-full:
	@echo "$(GREEN)============================================================$(NC)"
	@echo "$(GREEN)🚀 Running Full Pipeline (5 Steps)$(NC)"
	@echo "$(GREEN)============================================================$(NC)"
	@echo "$(BLUE)Step 0/5: Whitelisting VM IP address via Slack...$(NC)"
	@$(MAKE) pipeline-step0
	@echo "$(YELLOW)⏳ Waiting $(DELAY_AFTER_WHITELIST) seconds before Step 1...$(NC)"
	@sleep $(DELAY_AFTER_WHITELIST)
	@echo "$(BLUE)Step 1/5: Extracting carrier invoice data from ClickHouse...$(NC)"
	@$(MAKE) pipeline-step1
	@echo "$(YELLOW)⏳ Waiting $(DELAY_AFTER_PIPELINE) seconds before Step 2...$(NC)"
	@sleep $(DELAY_AFTER_PIPELINE)
	@echo "$(BLUE)Step 2/5: Extracting industry index logins from PeerDB...$(NC)"
	@$(MAKE) pipeline-step2
	@echo "$(YELLOW)⏳ Waiting $(DELAY_AFTER_PEERDB) seconds before Step 3...$(NC)"
	@sleep $(DELAY_AFTER_PEERDB)
	@echo "$(BLUE)Step 3/5: Filtering label-only tracking numbers...$(NC)"
	@$(MAKE) pipeline-step3
	@echo "$(YELLOW)⏳ Waiting $(DELAY_AFTER_FILTER) seconds before Step 4...$(NC)"
	@sleep $(DELAY_AFTER_FILTER)
	@echo "$(BLUE)Step 4/5: Running automated UPS shipment void...$(NC)"
	@$(MAKE) pipeline-step4
	@echo "$(GREEN)============================================================$(NC)"
	@echo "$(GREEN)✅ Full pipeline completed successfully!$(NC)"
	@echo "$(GREEN)============================================================$(NC)"
	@$(MAKE) status

.PHONY: pipeline-full-bg
pipeline-full-bg:
	@echo "$(GREEN)Starting full pipeline in background...$(NC)"
	@mkdir -p $(LOG_DIR)
	@nohup $(MAKE) pipeline-full > $(LOG_DIR)/pipeline_full_$(TIMESTAMP).log 2>&1 &
	@echo "$(GREEN)✅ Pipeline started in background$(NC)"
	@echo "$(YELLOW)📁 Log file: $(LOG_DIR)/pipeline_full_$(TIMESTAMP).log$(NC)"
	@echo "$(YELLOW)💡 Use 'make logs' to view progress$(NC)"

# ============================================================================
# Testing
# ============================================================================

.PHONY: test-step0
test-step0:
	@echo "$(BLUE)Testing Step 0: IP Whitelisting$(NC)"
	@$(MAKE) pipeline-step0

.PHONY: test-step1
test-step1:
	@echo "$(BLUE)Testing Step 1: DLT Pipeline$(NC)"
	@$(MAKE) pipeline-step1

.PHONY: test-step2
test-step2:
	@echo "$(BLUE)Testing Step 2: PeerDB Pipeline$(NC)"
	@$(MAKE) pipeline-step2

.PHONY: test-step3
test-step3:
	@echo "$(BLUE)Testing Step 3: Label Filter$(NC)"
	@$(MAKE) pipeline-step3

.PHONY: test-step4
test-step4:
	@echo "$(BLUE)Testing Step 4: Void Automation$(NC)"
	@$(MAKE) pipeline-step4

# ============================================================================
# Logging and Monitoring
# ============================================================================

.PHONY: logs
logs:
	@echo "$(BLUE)Recent pipeline logs:$(NC)"
	@if [ -d $(LOG_DIR) ]; then \
		ls -lt $(LOG_DIR)/*.log 2>/dev/null | head -10; \
		echo ""; \
		echo "$(YELLOW)To view a specific log:$(NC)"; \
		echo "  tail -f $(LOG_DIR)/<logfile>"; \
	else \
		echo "$(YELLOW)No logs found$(NC)"; \
	fi

.PHONY: status
status:
	@echo "$(GREEN)============================================================$(NC)"
	@echo "$(GREEN)📊 Pipeline Status$(NC)"
	@echo "$(GREEN)============================================================$(NC)"
	@echo ""
	@echo "$(BLUE)Recent Logs:$(NC)"
	@if [ -d $(LOG_DIR) ]; then \
		ls -lth $(LOG_DIR)/*.log 2>/dev/null | head -5 | awk '{print "  " $$9 " (" $$6 " " $$7 " " $$8 ")"}'; \
	else \
		echo "  No logs found"; \
	fi
	@echo ""
	@echo "$(BLUE)Recent Output Files:$(NC)"
	@if [ -d $(DATA_OUTPUT_DIR) ]; then \
		ls -lth $(DATA_OUTPUT_DIR)/*.{csv,json,duckdb} 2>/dev/null | head -5 | awk '{print "  " $$9 " (" $$5 ", " $$6 " " $$7 " " $$8 ")"}'; \
	else \
		echo "  No output files found"; \
	fi
	@echo ""
	@echo "$(BLUE)Disk Usage:$(NC)"
	@du -sh $(LOG_DIR) 2>/dev/null || echo "  Logs: 0 bytes"
	@du -sh $(DATA_OUTPUT_DIR) 2>/dev/null || echo "  Output: 0 bytes"
	@echo ""

# ============================================================================
# Cleanup
# ============================================================================

.PHONY: clean-logs
clean-logs:
	@echo "$(YELLOW)Cleaning old log files (>7 days)...$(NC)"
	@find $(LOG_DIR) -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Old logs cleaned$(NC)"

.PHONY: clean-output
clean-output:
	@echo "$(YELLOW)Cleaning old output files (>30 days)...$(NC)"
	@find $(DATA_OUTPUT_DIR) -name "*.csv" -type f -mtime +30 -delete 2>/dev/null || true
	@find $(DATA_OUTPUT_DIR) -name "*.json" -type f -mtime +30 -delete 2>/dev/null || true
	@find $(DATA_OUTPUT_DIR) -name "*.png" -type f -mtime +30 -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Old output files cleaned$(NC)"

.PHONY: clean-all
clean-all: clean-logs clean-output
	@echo "$(GREEN)✅ All cleanup complete$(NC)"

# ============================================================================
# Utility targets
# ============================================================================

.PHONY: env-check
env-check:
	@echo "$(BLUE)Checking environment configuration...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(RED)❌ .env file not found$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ .env file exists$(NC)"
	@grep -q "CLICKHOUSE_HOST" .env && echo "$(GREEN)✅ ClickHouse configured$(NC)" || echo "$(YELLOW)⚠️  ClickHouse not configured$(NC)"
	@grep -q "UPS_WEB_USERNAME" .env && echo "$(GREEN)✅ UPS credentials configured$(NC)" || echo "$(YELLOW)⚠️  UPS credentials not configured$(NC)"

.DEFAULT_GOAL := help

