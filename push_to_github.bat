@echo off
echo =======================================================
echo Pushing AdaptiveCloud to YOUR GitHub Repository
echo Repo: https://github.com/pradnyandongre24-creator/adaptivecloud-security.git
echo Branch: main
echo =======================================================
cd /d "%~dp0"

echo 1. Staging all files...
git add -A

echo.
echo 2. Committing changes...
git commit -m "feat: complete AdaptiveCloud with 238-attack taxonomy, dynamic RCA engine, self-healing playbooks, and research paper"

echo.
echo 3. Setting main branch...
git branch -M main

echo.
echo 4. Pushing to https://github.com/pradnyandongre24-creator/adaptivecloud-security.git...
git push -u origin main --force

echo.
echo =======================================================
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] Successfully pushed all files to your GitHub repository!
) else (
    echo [NOTICE] If prompted by GitHub, please sign in or provide your Personal Access Token.
)
echo =======================================================
pause
