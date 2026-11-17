# push_to_github.ps1
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "Removing Research Paper & Updating GitHub Repository" -ForegroundColor Cyan
Write-Host "Repo: https://github.com/pradnyandongre24-creator/adaptivecloud-security.git" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan

Set-Location -Path $PSScriptRoot

Write-Host "`n1. Removing research paper..." -ForegroundColor Yellow
git rm -f AdaptiveCloud_Research_Paper.md 2>$null
Remove-Item -Path "AdaptiveCloud_Research_Paper.md" -Force -ErrorAction SilentlyContinue

Write-Host "2. Staging changes..." -ForegroundColor Yellow
git add -A

Write-Host "3. Committing removal..." -ForegroundColor Yellow
git commit -m "chore: remove research paper from repository"

Write-Host "4. Pushing updates to origin main..." -ForegroundColor Yellow
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Research paper removed successfully from your GitHub repository!" -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Git push failed." -ForegroundColor Red
}
