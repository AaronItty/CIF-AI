@echo off
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo ====================================================
echo STARTING CIF-AI MICROSERVICE ARCHITECTURE
echo ====================================================

echo [1/3] Starting Agent Core Service (Layer 2) on Port 8002...
start cmd /k "set PYTHONPATH=%ROOT_DIR% & .\.venv\Scripts\activate & python -m agent_core.service"

timeout /t 3 /nobreak >nul

echo [2/3] Starting Email Service (Layer 1) on Port 8003...
start cmd /k "set PYTHONPATH=%ROOT_DIR% & .\.venv\Scripts\activate & python -m communication.email_service"

timeout /t 3 /nobreak >nul

echo [3/3] Starting App Service (Dashboard + KB API) on Port 8000...
start cmd /k "set PYTHONPATH=%ROOT_DIR% & .\.venv\Scripts\activate & python app-service.py"

echo ====================================================
echo All 3 microservices are running in separate windows.
echo ====================================================
pause
