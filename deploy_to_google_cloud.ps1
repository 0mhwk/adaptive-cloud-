# deploy_to_google_cloud.ps1
# 1-Click Automated Deployment of AdaptiveCloud to Google Cloud Platform (GCP)
param(
    [string]$ProjectId = "adaptive-learning-ml",
    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Stop"

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "    Deploying AdaptiveCloud Dashboard & Backend to Google Cloud (GCP) " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Check gcloud CLI
Write-Host "`n[*] Verifying Google Cloud SDK..." -ForegroundColor Yellow
try {
    $ver = & gcloud --version 2>&1
    Write-Host "  ✅ gcloud detected." -ForegroundColor Green
} catch {
    Write-Host "  ❌ Google Cloud SDK (gcloud) is not installed." -ForegroundColor Red
    Write-Host "     Please install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Yellow
    exit 1
}

# 2. Set Project
Write-Host "`n[*] Setting active project: $ProjectId ($Region)..." -ForegroundColor Yellow
& gcloud config set project $ProjectId
& gcloud config set compute/region $Region

# 3. Enable APIs
Write-Host "`n[*] Enabling Google Cloud Services (Cloud Run, Cloud Build, Compute)..." -ForegroundColor Yellow
& gcloud services enable run.googleapis.com cloudbuild.googleapis.com compute.googleapis.com iam.googleapis.com --quiet
Write-Host "  ✅ GCP Services enabled." -ForegroundColor Green

# 4. Deploy Backend
Write-Host "`n[*] Deploying Backend to Google Cloud Run..." -ForegroundColor Yellow
Push-Location "$PSScriptRoot\backend"
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

$backendUrl = (& gcloud run services describe adaptivecloud-backend --region $Region --format "value(status.url)").Trim()
Write-Host "  ✅ Backend Live on GCP: $backendUrl" -ForegroundColor Green

# 5. Deploy Frontend
Write-Host "`n[*] Deploying Frontend Dashboard to Google Cloud Run..." -ForegroundColor Yellow
Push-Location "$PSScriptRoot\frontend"
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

$frontendUrl = (& gcloud run services describe adaptivecloud-frontend --region $Region --format "value(status.url)").Trim()

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host "   🎉 CONGRATULATIONS! YOUR DASHBOARD IS LIVE ON GOOGLE CLOUD:         " -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "   [+] LIVE CLOUD DASHBOARD : $frontendUrl" -ForegroundColor Cyan
Write-Host "   [+] LIVE CLOUD BACKEND   : $backendUrl" -ForegroundColor Cyan
Write-Host "   [+] GCP PROJECT          : $ProjectId" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "Open $frontendUrl in any browser or phone without needing localhost!" -ForegroundColor White
