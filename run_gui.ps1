$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppDir = Join-Path $ScriptDir "applications\logistics\vehicle_routing_problem"
$VenvPython = "c:\Users\vladimir.dobrouchkin\.gemini\antigravity-ide\scratch\classiq_env\Scripts\python.exe"

if (Test-Path $VenvPython) {
    $PyCmd = $VenvPython
} else {
    $PyCmd = "python"
}

Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "  Starting Quantum Multi-Depot Field-Technician Dispatch (MDFTD-VRP) GUI" -ForegroundColor Cyan
Write-Host "  Classiq Quantum Synthesis Engine | 3-Tier Quantum Fuzzy Optimizer" -ForegroundColor Cyan
Write-Host "==============================================================================" -ForegroundColor Cyan
Write-Host "[*] Python Executable: $PyCmd" -ForegroundColor Gray
Write-Host "[*] Launching Desktop GUI..." -ForegroundColor Green

Start-Process -FilePath $PyCmd -ArgumentList (Join-Path $AppDir "gui_multi_depot_dispatch.py") -WorkingDirectory $AppDir
Write-Host "[SUCCESS] Desktop GUI application launched!" -ForegroundColor Green
