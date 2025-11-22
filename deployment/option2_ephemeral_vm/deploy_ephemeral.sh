#!/bin/bash
# GSR Automation - Complete Ephemeral VM Deployment Script
# This script sets up everything needed for Option 2 deployment
#
# Author: Gabriel Jerdhy Lapuz
# Project: gsr_automation

set -e

# ============================================================================
# Configuration - UPDATE THESE VALUES
# ============================================================================

PROJECT_ID="void-automation"
REGION="us-central1"
ZONE="us-central1-a"
SERVICE_ACCOUNT_NAME="gsr-automation-runner"
SECRET_NAME="gsr-automation-env"
BUCKET_NAME="void_automation"
FUNCTION_NAME="trigger-gsr-automation"
SCHEDULER_JOB_NAME="gsr-automation-scheduler"
REPO_URL="https://github.com/Business-Facilitating/void_credit_retrieval_project.git"
REPO_BRANCH="dev"

# Schedule: Every other day at 2:00 AM
SCHEDULE="0 2 */2 * *"
TIMEZONE="America/New_York"

# ============================================================================
# Colors
# ============================================================================

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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
    echo ""
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}============================================================${NC}"
}

# ============================================================================
# Deployment Steps
# ============================================================================

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI not found. Please install it first."
        exit 1
    fi
    log_success "gcloud CLI found"
    
    # Check if logged in
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
        log_error "Not logged in to gcloud. Run: gcloud auth login"
        exit 1
    fi
    log_success "Authenticated with gcloud"
    
    # Check .env file
    if [ ! -f ".env" ]; then
        log_error ".env file not found. Please create it first."
        exit 1
    fi
    log_success ".env file found"
    
    # Set project
    gcloud config set project "$PROJECT_ID"
    log_success "Project set to: $PROJECT_ID"
}

enable_apis() {
    print_header "Enabling Required APIs"
    
    log_info "This may take a few minutes..."
    
    gcloud services enable compute.googleapis.com \
        cloudscheduler.googleapis.com \
        cloudfunctions.googleapis.com \
        secretmanager.googleapis.com \
        storage.googleapis.com \
        cloudbuild.googleapis.com \
        --project="$PROJECT_ID"
    
    log_success "All required APIs enabled"
}

create_service_account() {
    print_header "Creating Service Account"
    
    # Check if service account exists
    if gcloud iam service-accounts describe "${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --project="$PROJECT_ID" &> /dev/null; then
        log_warning "Service account already exists"
    else
        gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
            --display-name="GSR Automation Runner" \
            --project="$PROJECT_ID"
        log_success "Service account created"
    fi
    
    # Grant permissions
    log_info "Granting permissions..."
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/compute.instanceAdmin.v1" \
        --quiet
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/storage.objectAdmin" \
        --quiet
    
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/iam.serviceAccountUser" \
        --quiet
    
    log_success "Permissions granted"
}

create_secret() {
    print_header "Creating Secret in Secret Manager"
    
    # Check if secret exists
    if gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &> /dev/null; then
        log_warning "Secret already exists. Updating..."
        gcloud secrets versions add "$SECRET_NAME" \
            --data-file=.env \
            --project="$PROJECT_ID"
    else
        gcloud secrets create "$SECRET_NAME" \
            --data-file=.env \
            --project="$PROJECT_ID"
        log_success "Secret created"
    fi
    
    # Grant access to service account
    gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
        --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor" \
        --project="$PROJECT_ID" \
        --quiet
    
    log_success "Secret configured"
}

create_storage_bucket() {
    print_header "Creating Cloud Storage Bucket"
    
    # Check if bucket exists
    if gsutil ls -b "gs://${BUCKET_NAME}" &> /dev/null; then
        log_warning "Bucket already exists"
    else
        gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://${BUCKET_NAME}"
        log_success "Bucket created: gs://${BUCKET_NAME}"
    fi
    
    # Set lifecycle policy
    log_info "Setting lifecycle policy (delete after 90 days)..."
    cat > /tmp/lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF
    
    gsutil lifecycle set /tmp/lifecycle.json "gs://${BUCKET_NAME}"
    rm /tmp/lifecycle.json
    
    log_success "Lifecycle policy configured"
}

deploy_cloud_function() {
    print_header "Deploying Cloud Function"
    
    # Update .env.yaml with actual values
    log_info "Configuring Cloud Function environment..."
    cat > cloud_function/.env.yaml << EOF
GCP_PROJECT_ID: "$PROJECT_ID"
GCP_ZONE: "$ZONE"
MACHINE_TYPE: "e2-medium"
REPO_URL: "$REPO_URL"
REPO_BRANCH: "$REPO_BRANCH"
SECRET_ENV_FILE: "$SECRET_NAME"
RESULTS_BUCKET: "$BUCKET_NAME"
EOF
    
    log_info "Deploying function (this may take 2-3 minutes)..."
    
    gcloud functions deploy "$FUNCTION_NAME" \
        --gen2 \
        --runtime=python311 \
        --region="$REGION" \
        --source=cloud_function \
        --entry-point=trigger_pipeline \
        --trigger-http \
        --allow-unauthenticated \
        --service-account="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
        --timeout=540s \
        --memory=512MB \
        --env-vars-file=cloud_function/.env.yaml \
        --project="$PROJECT_ID" \
        --quiet
    
    log_success "Cloud Function deployed"
    
    # Get function URL
    FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" \
        --gen2 \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(serviceConfig.uri)")
    
    log_success "Function URL: $FUNCTION_URL"
}

create_scheduler_job() {
    print_header "Creating Cloud Scheduler Job"
    
    # Get function URL
    FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" \
        --gen2 \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(serviceConfig.uri)")
    
    # Check if job exists
    if gcloud scheduler jobs describe "$SCHEDULER_JOB_NAME" \
        --location="$REGION" \
        --project="$PROJECT_ID" &> /dev/null; then
        log_warning "Scheduler job already exists. Updating..."
        gcloud scheduler jobs delete "$SCHEDULER_JOB_NAME" \
            --location="$REGION" \
            --project="$PROJECT_ID" \
            --quiet
    fi
    
    gcloud scheduler jobs create http "$SCHEDULER_JOB_NAME" \
        --location="$REGION" \
        --schedule="$SCHEDULE" \
        --uri="$FUNCTION_URL" \
        --http-method=POST \
        --time-zone="$TIMEZONE" \
        --project="$PROJECT_ID"
    
    log_success "Scheduler job created"
    log_info "Schedule: $SCHEDULE ($TIMEZONE)"
}

test_deployment() {
    print_header "Testing Deployment"
    
    log_info "Triggering a test run..."
    log_warning "This will create a VM and run the pipeline (takes ~5-15 minutes)"
    
    read -p "Do you want to run a test now? (y/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gcloud scheduler jobs run "$SCHEDULER_JOB_NAME" \
            --location="$REGION" \
            --project="$PROJECT_ID"
        
        log_success "Test triggered!"
        log_info "Monitor progress:"
        echo "  - Cloud Function logs: gcloud functions logs read $FUNCTION_NAME --gen2 --region=$REGION --limit=50"
        echo "  - Compute Engine VMs: gcloud compute instances list --project=$PROJECT_ID"
        echo "  - Results: gsutil ls gs://${BUCKET_NAME}/runs/"
    else
        log_info "Skipping test run"
    fi
}

print_summary() {
    print_header "Deployment Complete! 🎉"
    
    echo ""
    log_success "GSR Automation is now deployed with ephemeral VMs!"
    echo ""
    echo "📊 Configuration:"
    echo "  - Project: $PROJECT_ID"
    echo "  - Region: $REGION"
    echo "  - Schedule: $SCHEDULE ($TIMEZONE)"
    echo "  - Results: gs://${BUCKET_NAME}/"
    echo ""
    echo "🔧 Useful Commands:"
    echo ""
    echo "  # Trigger manual run"
    echo "  gcloud scheduler jobs run $SCHEDULER_JOB_NAME --location=$REGION"
    echo ""
    echo "  # View function logs"
    echo "  gcloud functions logs read $FUNCTION_NAME --gen2 --region=$REGION --limit=50"
    echo ""
    echo "  # List running VMs"
    echo "  gcloud compute instances list --filter='name~gsr-automation'"
    echo ""
    echo "  # View results"
    echo "  gsutil ls gs://${BUCKET_NAME}/runs/"
    echo ""
    echo "  # Download latest results"
    echo "  gsutil -m cp -r gs://${BUCKET_NAME}/runs/\$(gsutil ls gs://${BUCKET_NAME}/runs/ | tail -1) ./results/"
    echo ""
    echo "  # Update secret (.env)"
    echo "  gcloud secrets versions add $SECRET_NAME --data-file=.env"
    echo ""
    echo "  # Pause scheduler"
    echo "  gcloud scheduler jobs pause $SCHEDULER_JOB_NAME --location=$REGION"
    echo ""
    echo "  # Resume scheduler"
    echo "  gcloud scheduler jobs resume $SCHEDULER_JOB_NAME --location=$REGION"
    echo ""
    log_info "Next scheduled run: Check with 'gcloud scheduler jobs describe $SCHEDULER_JOB_NAME --location=$REGION'"
    echo ""
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    print_header "GSR Automation - Ephemeral VM Deployment"
    
    log_info "This script will set up everything for Option 2 deployment"
    log_warning "Make sure you've updated the configuration at the top of this script!"
    echo ""
    
    read -p "Continue with deployment? (y/n) " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Deployment cancelled"
        exit 0
    fi
    
    check_prerequisites
    enable_apis
    create_service_account
    create_secret
    create_storage_bucket
    deploy_cloud_function
    create_scheduler_job
    test_deployment
    print_summary
}

# Trap errors
trap 'log_error "Deployment failed at line $LINENO"; exit 1' ERR

# Run main
main "$@"

