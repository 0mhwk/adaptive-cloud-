# setup_my_github_repo.ps1
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "      AdaptiveCloud - Connect & Push to YOUR Personal GitHub" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location -Path $PSScriptRoot

Write-Host "STEP 1: If you haven't created your repository on GitHub yet:" -ForegroundColor Yellow
Write-Host "  1. Go to: https://github.com/new" -ForegroundColor Yellow
Write-Host "  2. Repository name: AdaptiveCloud (or any name you like)" -ForegroundColor Yellow
Write-Host "  3. Choose Public or Private" -ForegroundColor Yellow
Write-Host "  4. Leave 'Add a README' UNCHECKED" -ForegroundColor Yellow
Write-Host "  5. Click [Create repository]`n" -ForegroundColor Yellow

$repoUrl = Read-Host "Paste your GitHub Repository URL (e.g., https://github.com/USERNAME/AdaptiveCloud.git)"

if ([string]::IsNullOrWhiteSpace($repoUrl)) {
    Write-Host "[ERROR] No URL entered. Aborting." -ForegroundColor Red
    exit 1
}

Write-Host "`nSetting remote origin to: $repoUrl" -ForegroundColor Cyan
git remote set-url origin $repoUrl 2>$null
if ($LASTEXITCODE -ne 0) {
    git remote add origin $repoUrl
}

Write-Host "`nStaging all updated files..." -ForegroundColor Cyan
git add -A

Write-Host "Committing all changes..." -ForegroundColor Cyan
git commit -m "Initial commit: AdaptiveCloud autonomous self-healing cloud security framework"

Write-Host "Ensuring main branch..." -ForegroundColor Cyan
git branch -M main

Write-Host "Pushing to your GitHub repository..." -ForegroundColor Cyan
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Your project is now live on your personal GitHub!" -ForegroundColor Green
} else {
    Write-Host "`n[NOTICE] If GitHub asked for authentication, sign in via the browser popup or personal access token." -ForegroundColor Yellow
}
