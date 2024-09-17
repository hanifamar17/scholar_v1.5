@echo off
REM Navigate to the directory where Laragon is installed
cd /d "E:\App-Development\1-Tools-Library-Environment\laragon"

REM Start all Laragon services
start laragon.exe

REM Navigate to the scholar_crawler directory
cd App-Development\scholar_v1.5

REM Run the main.py script using Python
start "" "python" "main.py"

REM Wait for main.py (adjust the timeout if necessary)
timeout /t 4

REM Open the browser to http://127.0.0.1:4040
start "" "http://127.0.0.1:4040"

REM Pause to keep the command prompt open
pause
