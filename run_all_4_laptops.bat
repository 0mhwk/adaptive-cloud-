@echo off
TITLE AdaptiveCloud Multi-Laptop Fleet Runner
cls
echo ======================================================================
echo       ADAPTIVECLOUD - RUN ALL 4 PHYSICAL LAPTOPS AT ONCE
echo ======================================================================
echo.
echo Starting multi-laptop telemetry simulator...
echo Laptop #1: Real Local Hardware (Your Laptop)
echo Laptop #2: Lab Workstation A (Port Scan)
echo Laptop #3: Dev Workstation B (Cryptominer)
echo Laptop #4: Field Workstation C (PrivEsc)
echo.
python "%~dp0agent\simulate_all_laptops.py"
pause
