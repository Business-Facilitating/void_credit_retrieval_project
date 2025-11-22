#!/bin/bash
# Create Test VM for Steps 0-3 Testing
# This script creates an ephemeral VM that runs only Steps 0-3 for testing purposes

set -e

PROJECT_ID="void-automation"
ZONE="us-central1-a"
MACHINE_TYPE="e2-medium"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
VM_NAME="gsr-automation-test-${TIMESTAMP}"
SERVICE_ACCOUNT="gsr-automation-runner@void-automation.iam.gserviceaccount.com"

echo "=========================================="
echo "Creating Test VM: ${VM_NAME}"
echo "=========================================="

# Read the test startup script
STARTUP_SCRIPT=$(cat test_vm_setup.sh)

# Create the VM
gcloud compute instances create "${VM_NAME}" \
    --project="${PROJECT_ID}" \
    --zone="${ZONE}" \
    --machine-type="${MACHINE_TYPE}" \
    --network-interface=network-tier=PREMIUM,stack-type=IPV4_ONLY,subnet=default \
    --metadata=startup-script="${STARTUP_SCRIPT}",enable-oslogin=true \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account="${SERVICE_ACCOUNT}" \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --create-disk=auto-delete=yes,boot=yes,device-name="${VM_NAME}",image=projects/ubuntu-os-cloud/global/images/ubuntu-2204-jammy-v20241115,mode=rw,size=30,type=pd-balanced \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=purpose=gsr-automation-test,managed-by=manual \
    --reservation-affinity=any

echo ""
echo "=========================================="
echo "✅ Test VM Created Successfully!"
echo "=========================================="
echo "VM Name: ${VM_NAME}"
echo "Zone: ${ZONE}"
echo "Project: ${PROJECT_ID}"
echo ""
echo "To monitor the VM:"
echo "  gcloud compute instances get-serial-port-output ${VM_NAME} --zone=${ZONE} --project=${PROJECT_ID}"
echo ""
echo "To SSH into the VM:"
echo "  gcloud compute ssh ${VM_NAME} --zone=${ZONE} --project=${PROJECT_ID}"
echo ""
echo "To delete the VM when done:"
echo "  gcloud compute instances delete ${VM_NAME} --zone=${ZONE} --project=${PROJECT_ID} --quiet"
echo ""
echo "=========================================="

