@echo off
echo =====================================================================
echo Removing Secrets & Pushing Clean Repo to GitHub
echo =====================================================================
cd /d "%~dp0"

echo 1. Creating clean orphan branch without secret history...
git checkout --orphan clean_main

echo 2. Removing sensitive credentials from git index...
git rm --cached backend/gcp_credentials.json 2>nul

echo 3. Staging all clean files (dashboard, 238 dataset, playbooks, paper)...
git add -A

echo 4. Creating fresh commit...
git commit -m "Initial commit: AdaptiveCloud autonomous self-healing cloud security framework"

echo 5. Setting main branch...
git branch -D main 2>nul
git branch -m main

echo 6. Pushing cleanly to your GitHub repository...
git push -u origin main --force

echo =====================================================================
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Pushed cleanly without any secret warnings!
) else (
    echo [NOTICE] If still blocked, use the unblock URL in your browser.
)
echo =====================================================================
pause
