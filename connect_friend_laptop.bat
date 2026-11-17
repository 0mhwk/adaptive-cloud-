@echo off
TITLE Connect Friend's Physical Laptop to AdaptiveCloud
cls
echo ======================================================================
echo       ADAPTIVECLOUD - CONNECT FRIEND'S PHYSICAL LAPTOP
echo ======================================================================
echo.
echo Make sure you are connected to the SAME Wi-Fi network as the server!
echo.
set /p SERVER_IP="Enter the Server Laptop IP Address (e.g. 192.168.1.15): "
echo.
echo Select Card Slot on Dashboard:
echo [2] Physical Laptop #2 (Default)
echo [3] Physical Laptop #3
echo [4] Physical Laptop #4
set /p CARD_CHOICE="Enter 2, 3, or 4 (Press Enter for 2): "
if "%CARD_CHOICE%"=="" set CARD_CHOICE=2

echo.
echo Connecting to http://%SERVER_IP%:8001 as Physical Laptop #%CARD_CHOICE%...
python "%~dp0agent\friend_laptop_agent.py" --server "http://%SERVER_IP%:8001" --card %CARD_CHOICE%
pause
