@echo off
TITLE AdaptiveCloud AWS Credentials Setup
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_aws_secret.ps1"
pause
