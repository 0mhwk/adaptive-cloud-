@echo off
TITLE Extract Uploaded Project Document
cls
echo ======================================================================
echo          EXTRACTING UPLOADED PROJECT DOCUMENT FOR AI
echo ======================================================================
echo.
cd /d "%~dp0"
python inspect_zip.py
echo.
echo ======================================================================
echo Extraction complete! You can now ask the AI to check the extracted files.
echo ======================================================================
pause
