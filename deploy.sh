#!/bin/bash
# Deployment script for Raman Spectrum Fitting App to Google Cloud Run

# Configuration - edit these
PROJECT_ID="your-project-id"
SERVICE_NAME="raman-fitting"
REGION="us-central1"

echo "=== Raman Spectrum Fitting App - Cloud Run Deployment ==="
echo ""
echo "Prerequisites:"
echo "1. Google Cloud SDK installed (gcloud)"
echo "2. Docker installed"
echo "3. A GCP project with billing enabled"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI not found. Install from https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Authenticate and set project
echo "Step 1: Setting up GCP project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Step 2: Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create Artifact Registry repository (if not exists)
echo "Step 3: Creating Artifact Registry repository..."
gcloud artifacts repositories create docker-repo \
    --repository-format=docker \
    --location=$REGION \
    --description="Docker repository" 2>/dev/null || true

# Configure Docker for Artifact Registry
echo "Step 4: Configuring Docker authentication..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# Build and push image
IMAGE_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/docker-repo/${SERVICE_NAME}:latest"

echo "Step 5: Building container image..."
docker build -t $IMAGE_URI .

echo "Step 6: Pushing to Artifact Registry..."
docker push $IMAGE_URI

# Deploy to Cloud Run
echo "Step 7: Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_URI \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10

echo ""
echo "=== Deployment Complete ==="
echo "Your app is now available at the URL shown above!"
