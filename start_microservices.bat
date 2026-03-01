@echo off
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo ====================================================
echo STARTING CIF-AI MICROSERVICE ARCHITECTURE
echo ====================================================

echo [1/2] Starting Agent Core Service (Layer 2) on Port 8002...
start cmd /k "set PYTHONPATH=%ROOT_DIR% & .\.venv\Scripts\activate & python -m agent_core.service"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Email Service (Layer 1) on Port 8003...
start cmd /k "set PYTHONPATH=%ROOT_DIR% & .\.venv\Scripts\activate & python -m communication.email_service"

echo ====================================================
echo Microservices are running in separate windows.
echo Dashboard/Main.py and MCP Layer are NOT started.
echo ====================================================
pause
