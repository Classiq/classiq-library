@echo off
setlocal EnableDelayedExpansion
title Quantum MDFTD-VRP Dispatch GUI Launcher

echo ==============================================================================
echo   Starting Quantum Multi-Depot Field-Technician Dispatch (MDFTD-VRP) GUI
echo   Classiq Quantum Synthesis Engine ^| 3-Tier Quantum Fuzzy Optimizer
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
echo [*] Launching Desktop GUI: gui_multi_depot_dispatch.py...

start "" /D "%APP_DIR%" "%PY_CMD%" "%APP_DIR%\gui_multi_depot_dispatch.py"

echo [SUCCESS] Desktop GUI application initialized.
