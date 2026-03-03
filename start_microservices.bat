@echo off
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

:: Set main window title
title CIF-AI Main Controller

echo ====================================================
echo STARTING CIF-AI MICROSERVICE ARCHITECTURE
echo ====================================================

echo [1/3] Starting Agent Core Service (Layer 2) on Port 8002...
start "CIF-AI - Agent Core" cmd /k "title CIF-AI - Agent Core & set PYTHONPATH=%ROOT_DIR% & .\.venv\Scripts\activate & python -m agent_core.service"

timeout /t 3 /nobreak >nul

echo [2/3] Starting Email Service (Layer 1) on Port 8003...
start "CIF-AI - Email Service" cmd /k "title CIF-AI - Email Service & set PYTHONPATH=%ROOT_DIR% & .\.venv\Scripts\activate & python -m communication.email_service"

timeout /t 3 /nobreak >nul

echo [3/3] Starting App Service (Dashboard + KB API) on Port 8000...
start "CIF-AI - App Service" cmd /k "title CIF-AI - App Service & set PYTHONPATH=%ROOT_DIR% & .\.venv\Scripts\activate & python app-service.py"

echo ====================================================
echo All 3 microservices are running in separate windows.
echo ====================================================
echo Press 'Q' to stop all microservices and close...

:input_loop
choice /c q /n 
if errorlevel 1 goto shutdown

:shutdown
echo.
echo Stopping all microservices...
taskkill /fi "WINDOWTITLE eq CIF-AI - Agent Core*" /t /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq CIF-AI - Email Service*" /t /f >nul 2>&1
taskkill /fi "WINDOWTITLE eq CIF-AI - App Service*" /t /f >nul 2>&1
echo All services stopped successfully.
timeout /t 2 /nobreak >nul

