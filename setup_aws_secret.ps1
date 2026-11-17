# setup_aws_secret.ps1
# Securely saves your AWS Credentials locally into .env without exposing them

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "         ADAPTIVECLOUD: SECURE AWS CREDENTIALS SETUP        " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$keyId = Read-Host "Enter your AWS Access Key ID (e.g. AKIA...)"
if ([string]::IsNullOrWhiteSpace($keyId)) {
    Write-Host "`n[!] No access key entered. Aborted." -ForegroundColor Red
    exit 1
}

# Securely prompt for the Secret Access Key (typing hidden)
$secKey = Read-Host "Paste your AWS Secret Access Key (typing hidden)" -AsSecureString
$bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secKey)
$plainSecret = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)

if ([string]::IsNullOrWhiteSpace($plainSecret)) {
    Write-Host "`n[!] No secret key entered. Aborted." -ForegroundColor Red
    exit 1
}

$region = Read-Host "Enter AWS Region (press Enter for ap-south-1 [Mumbai] or type us-east-1)"
if ([string]::IsNullOrWhiteSpace($region)) {
    $region = "ap-south-1"
}

$envPath = Join-Path $PSScriptRoot ".env"

@"
# AdaptiveCloud Environment Configuration
AWS_ACCESS_KEY_ID=$keyId
AWS_SECRET_ACCESS_KEY=$plainSecret
AWS_DEFAULT_REGION=$region
"@ | Out-File -FilePath $envPath -Encoding utf8

Write-Host "`n[✓] AWS Credentials securely saved to $envPath" -ForegroundColor Green
Write-Host "[*] Testing connection to AWS..." -ForegroundColor Cyan

& python "$PSScriptRoot\scripts\aws_cloud_monitor.py" --status
