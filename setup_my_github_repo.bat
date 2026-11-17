@echo off
setlocal enabledelayedexpansion
echo =====================================================================
echo       AdaptiveCloud - Connect & Push to YOUR Personal GitHub
echo =====================================================================
echo.
cd /d "%~dp0"

echo Current remote origin:
git remote get-url origin 2>nul
echo.
echo ---------------------------------------------------------------------
echo STEP 1: If you haven't created your repository on GitHub yet:
echo         1. Open your browser and go to: https://github.com/new
echo         2. Name your repository (e.g. AdaptiveCloud or AdaptiveCloud-Security)
echo         3. Choose Public or Private
echo         4. IMPORTANT: DO NOT check "Add a README file"
echo         5. Click [Create repository]
echo ---------------------------------------------------------------------
echo.
set /p REPO_URL="Enter your GitHub Repository URL (e.g., https://github.com/YOUR_USERNAME/AdaptiveCloud.git): "

if "%REPO_URL%"=="" (
    echo [ERROR] No URL entered. Operation cancelled.
    pause
    exit /b 1
)

echo.
echo Changing git remote origin to: %REPO_URL%
git remote set-url origin %REPO_URL%
if %ERRORLEVEL% NEQ 0 (
    echo Remote 'origin' did not exist. Adding new origin...
    git remote add origin %REPO_URL%
)

echo.
echo Staging all project files (dashboards, 238-attack dataset, RCA engine, playbooks, paper)...
git add -A

echo.
echo Creating commit...
git commit -m "Initial commit: AdaptiveCloud autonomous self-healing cloud security framework"

echo.
echo Ensuring default branch is 'main'...
git branch -M main

echo.
echo Pushing project to your GitHub repository...
git push -u origin main

echo.
echo =====================================================================
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Your project has been pushed to your personal GitHub repository!
) else (
    echo [NOTICE] If push failed due to authentication:
    echo 1. Sign in when prompted by the GitHub dialog, or
    echo 2. Use a GitHub Personal Access Token (PAT) as password.
)
echo =====================================================================
pause
