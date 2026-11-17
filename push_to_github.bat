@echo off
echo =====================================================================
echo Removing Research Paper & Updating GitHub Repository
echo Repo: https://github.com/pradnyandongre24-creator/adaptivecloud-security.git
echo =====================================================================
cd /d "%~dp0"

echo 1. Removing research paper from git repository...
git rm -f AdaptiveCloud_Research_Paper.md 2>nul
del /f /q AdaptiveCloud_Research_Paper.md 2>nul

echo.
echo 2. Staging changes...
git add -A

echo.
echo 3. Committing removal...
git commit -m "chore: remove research paper from repository"

echo.
echo 4. Pushing updates to GitHub...
git push origin main

echo.
echo =====================================================================
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Research paper removed successfully from your GitHub repository!
) else (
    echo [ERROR] Push failed. Check your network or GitHub login.
)
echo =====================================================================
pause
