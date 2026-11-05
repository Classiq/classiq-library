@echo off
setlocal EnableDelayedExpansion
title Quantum Field-Technician Dispatch Web Platform Launcher

echo ==============================================================================
echo   Starting Quantum Multi-Tier Field-Technician Dispatch (SC-QFCM) Web Server
echo   Classiq Quantum Synthesis Engine ^| 35,000 Technician Fleet Simulator
echo ==============================================================================

set "ROOT_DIR=%~dp0"
set "APP_DIR=%ROOT_DIR%applications\logistics\vehicle_routing_problem"
set "VENV_PYTHON=c:\Users\vladimir.dobrouchkin\.gemini\antigravity-ide\scratch\classiq_env\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    set "PY_CMD=%VENV_PYTHON%"
) else (
    set "PY_CMD=python"
)

echo [*] Python Executable: %PY_CMD%
echo [*] Application Directory: %APP_DIR%
echo [*] Launching Web Server on http://localhost:8080...

"%PY_CMD%" "%APP_DIR%\web_gui_server.py" --port 8080
