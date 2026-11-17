# push_to_github.ps1
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Pushing AdaptiveCloud to YOUR GitHub Repository" -ForegroundColor Cyan
Write-Host "Repo: https://github.com/pradnyandongre24-creator/adaptivecloud-security.git" -ForegroundColor Cyan
Write-Host "Branch: main" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan

Set-Location -Path $PSScriptRoot

Write-Host "`n1. Staging all files..." -ForegroundColor Yellow
git add -A

Write-Host "`n2. Committing changes..." -ForegroundColor Yellow
git commit -m "feat: complete AdaptiveCloud with 238-attack taxonomy, dynamic RCA engine, self-healing playbooks, and research paper"

Write-Host "`n3. Setting main branch..." -ForegroundColor Yellow
git branch -M main

Write-Host "`n4. Pushing to origin main..." -ForegroundColor Yellow
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Successfully pushed all updates to GitHub!" -ForegroundColor Green
} else {
    Write-Host "`n[NOTICE] If GitHub authentication is required, complete the browser login prompt." -ForegroundColor Yellow
}
