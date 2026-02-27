@echo off
echo Starting MCP Service on Port 8000...
start cmd /k ".\venv\Scripts\activate & python run_mcp.py"

timeout /t 3 /nobreak >nul

echo Starting SaaS Core API and Dashboard on Port 8001...
call .\venv\Scripts\activate
python main.py
