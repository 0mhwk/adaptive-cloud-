# deploy/gcp/deploy_to_cloud_run.ps1
# Automates deployment of AdaptiveCloud to Google Cloud Platform (GCP)
# Creates serverless, auto-scaling instances on Google Cloud Run with production HTTPS URLs.

param(
    [string]$ProjectId = "adaptive-learning-ml",
    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "     AdaptiveCloud — Google Cloud Platform (GCP) Deployment          " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Verify gcloud CLI
Write-Host "`n[*] Verifying Google Cloud SDK (gcloud)..." -ForegroundColor Yellow
try {
    $gcloudVer = & gcloud --version 2>&1
    Write-Host "  ✅ gcloud CLI detected." -ForegroundColor Green
} catch {
    Write-Host "  ❌ gcloud CLI not found. Please install Google Cloud SDK from:" -ForegroundColor Red
    Write-Host "     https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# 2. Set active GCP project
Write-Host "`n[*] Setting active Google Cloud project to: $ProjectId" -ForegroundColor Yellow
& gcloud config set project $ProjectId
& gcloud config set compute/region $Region

# 3. Enable necessary Google Cloud Services
Write-Host "`n[*] Enabling required Google Cloud APIs..." -ForegroundColor Yellow
$services = @(
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "compute.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "iam.googleapis.com"
)
foreach ($srv in $services) {
    Write-Host "  - Enabling $srv..."
    & gcloud services enable $srv --quiet
}
Write-Host "  ✅ All GCP APIs enabled." -ForegroundColor Green

# 4. Deploy Backend to Google Cloud Run
Write-Host "`n[*] Building and deploying Backend API to Google Cloud Run..." -ForegroundColor Yellow
Push-Location "$PSScriptRoot\..\..\backend"
try {
    & gcloud run deploy adaptivecloud-backend `
        --source . `
        --region $Region `
        --platform managed `
        --allow-unauthenticated `
        --set-env-vars "ENVIRONMENT=production,DEBUG=false,PROJECT_ID=$ProjectId" `
        --quiet
} finally {
    Pop-Location
}

# Fetch Backend URL
$backendUrl = (& gcloud run services describe adaptivecloud-backend --region $Region --format "value(status.url)").Trim()
Write-Host "  ✅ Backend successfully deployed to GCP:" -ForegroundColor Green
Write-Host "     $backendUrl" -ForegroundColor Cyan

# 5. Deploy Frontend to Google Cloud Run
Write-Host "`n[*] Building and deploying React Frontend to Google Cloud Run..." -ForegroundColor Yellow
Push-Location "$PSScriptRoot\..\..\frontend"
try {
    & gcloud run deploy adaptivecloud-frontend `
        --source . `
        --region $Region `
        --platform managed `
        --allow-unauthenticated `
        --set-env-vars "VITE_API_URL=$backendUrl" `
        --quiet
} finally {
    Pop-Location
}

# Fetch Frontend URL
$frontendUrl = (& gcloud run services describe adaptivecloud-frontend --region $Region --format "value(status.url)").Trim()

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "     🎉 GOOGLE CLOUD DEPLOYMENT COMPLETED SUCCESSFULLY!              " -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "  [+] Live GCP Frontend Dashboard : $frontendUrl" -ForegroundColor Cyan
Write-Host "  [+] Live GCP Backend API Hub    : $backendUrl" -ForegroundColor Cyan
Write-Host "  [+] Cloud Project ID            : $ProjectId" -ForegroundColor Yellow
Write-Host "  [+] Google Cloud Region         : $Region" -ForegroundColor Yellow
Write-Host "======================================================================`n"
