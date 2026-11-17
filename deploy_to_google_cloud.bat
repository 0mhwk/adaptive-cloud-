@echo off
title Deploy AdaptiveCloud to Google Cloud Platform
cd /d "%~dp0"
echo ======================================================================
echo    Deploying AdaptiveCloud Dashboard & Backend to Google Cloud (GCP)
echo ======================================================================
echo.

echo [*] Checking Google Cloud SDK (gcloud)...
where gcloud >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Google Cloud SDK (gcloud) is not installed or not in PATH!
    echo Please install it from: https://cloud.google.com/sdk/docs/install
    echo.
    pause
    exit /b 1
)

echo.
echo [*] Step 1: Setting up active Google Cloud project...
set GCP_PROJECT=adaptive-learning-ml
call gcloud config set project %GCP_PROJECT%
call gcloud config set compute/region us-central1

echo.
echo [*] Step 2: Enabling Google Cloud APIs (Cloud Run, Cloud Build, Compute)...
call gcloud services enable run.googleapis.com cloudbuild.googleapis.com compute.googleapis.com iam.googleapis.com --quiet

echo.
echo [*] Step 3: Deploying Backend to Google Cloud Run...
cd backend
call gcloud run deploy adaptivecloud-backend --source . --region us-central1 --platform managed --allow-unauthenticated --set-env-vars ENVIRONMENT=production,DEBUG=false,PROJECT_ID=%GCP_PROJECT% --quiet
cd ..

for /f "delims=" %%i in ('gcloud run services describe adaptivecloud-backend --region us-central1 --format "value(status.url)"') do set BACKEND_URL=%%i

echo.
echo [*] Backend Live URL: %BACKEND_URL%

echo.
echo [*] Step 4: Deploying Frontend Dashboard to Google Cloud Run...
cd frontend
call gcloud run deploy adaptivecloud-frontend --source . --region us-central1 --platform managed --allow-unauthenticated --set-env-vars VITE_API_URL=%BACKEND_URL% --quiet
cd ..

for /f "delims=" %%i in ('gcloud run services describe adaptivecloud-frontend --region us-central1 --format "value(status.url)"') do set FRONTEND_URL=%%i

echo.
echo ======================================================================
echo    CONGRATULATIONS! YOUR SYSTEM IS LIVE ON GOOGLE CLOUD:
echo ======================================================================
echo.
echo    [+] LIVE CLOUD DASHBOARD : %FRONTEND_URL%
echo    [+] LIVE CLOUD BACKEND   : %BACKEND_URL%
echo    [+] CLOUD PROJECT        : %GCP_PROJECT%
echo.
echo ======================================================================
echo You can now open %FRONTEND_URL% from any computer or browser!
echo.
pause
