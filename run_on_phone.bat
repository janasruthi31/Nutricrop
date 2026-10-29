@echo off
echo ========================================================
echo   TN Soil Optimizer - Launch on Connected Phone
echo ========================================================
echo.

:: 1. Verify ADB Device
adb devices
echo.

:: 2. Set up ADB Reverse Port Forwarding
echo Setting up USB reverse port forwarding (port 8000)...
adb reverse tcp:8000 tcp:8000
echo.

:: 3. Launch Backend in new window if not running
netstat -ano | findstr :8000 >nul 2>&1
if %errorlevel% neq 0 (
    echo Starting Python Backend Server...
    start "TN Agri Backend" cmd /k ".\venv\Scripts\activate.bat && python -m uvicorn phase3_soil.main:app --host 0.0.0.0 --port 8000 --reload"
    timeout /t 3 /nobreak >nul
) else (
    echo Backend is already running on port 8000.
)
echo.

:: 4. Launch Flutter App on phone with Hot Reload
echo Launching Flutter App on phone with Hot Reload...
cd flutter_app
flutter run -d DMT4DYYLIN8XIRV8
