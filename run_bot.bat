@echo off
echo ----------------------------------------
echo     STARTING BOT
echo ----------------------------------------

SET PROJECT_DIR=%cd%

echo Starting Appium server...
start "" appium

echo Waiting for Appium to initialize...
timeout /t 3 >nul

echo Running Python bot...
python pes.py

echo Stopping Appium...
taskkill /IM node.exe /F >nul 2>&1

echo ----------------------------------------
echo BOT FINISHED EXECUTION
echo ----------------------------------------
pause
