@echo off
TITLE AdaptiveCloud Physical Laptop Telemetry Agent
cls
echo ======================================================================
echo          LAUNCHING ADAPTIVECLOUD PHYSICAL HOST AGENT
echo ======================================================================
echo.
cd /d "%~dp0"
python agent/run_laptop_agent.py
pause
