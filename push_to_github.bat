@echo off
echo =====================================================================
echo    AdaptiveCloud - Standalone Clean Push to GitHub (No GCP Secrets)
echo    Repo: https://github.com/pradnyandongre24-creator/adaptivecloud-security.git
echo =====================================================================
echo.
cd /d "%~dp0"

echo [1/6] Disconnecting old commit history containing secrets...
git checkout --orphan standalone_main

echo.
echo [2/6] Unstaging any GCP credentials or deploy files...
git rm --cached -r -f backend/gcp_credentials.json 2>nul
git rm --cached -r -f deploy/gcp 2>nul
git rm --cached -r -f deploy_to_google_cloud.bat 2>nul
git rm --cached -r -f deploy_to_google_cloud.ps1 2>nul

echo.
echo [3/6] Staging all clean project files...
git add -A

echo.
echo [4/6] Committing clean project...
git commit -m "feat: AdaptiveCloud autonomous self-healing cloud security & RCA framework (standalone release)"

echo.
echo [5/6] Resetting main branch...
git branch -D main 2>nul
git branch -m main

echo.
echo [6/6] Pushing cleanly to your GitHub repository...
git push -u origin main --force

echo.
echo =====================================================================
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Your project has been pushed cleanly to GitHub!
    echo Visit: https://github.com/pradnyandongre24-creator/adaptivecloud-security
) else (
    echo [ERROR] Push failed. Check your network or GitHub login.
)
echo =====================================================================
pause
