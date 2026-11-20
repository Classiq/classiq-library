$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppDir = Join-Path $ScriptDir "applications\logistics\vehicle_routing_problem"
$VenvPython = "c:\Users\vladimir.dobrouchkin\.gemini\antigravity-ide\scratch\classiq_env\Scripts\python.exe"

if (Test-Path $VenvPython) {
    $PyCmd = $VenvPython
} else {
    $PyCmd = "python"
}

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  Starting Quantum Multi-Tier Field-Technician Dispatch (SC-QFCM) Web Server" -ForegroundColor Cyan
Write-Host "  Classiq Quantum Synthesis Engine | 35,000 Technician Fleet Simulator" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "[*] Python Executable: $PyCmd" -ForegroundColor Gray
Write-Host "[*] Launching Web Server on http://localhost:8080..." -ForegroundColor Green

& $PyCmd (Join-Path $AppDir "web_gui_server.py") --port 8080
