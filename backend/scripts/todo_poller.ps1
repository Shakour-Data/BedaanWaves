$scriptPath = "E:\Shakour\BedaanProjects\OldFils\BedaanWaves\backend\scripts\auto_check_todo.py"
$logDir = "E:\Shakour\BedaanProjects\OldFils\BedaanWaves\backend\scripts\logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }

while ($true) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logFile = Join-Path $logDir "todo_check_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
    Write-Host "[$timestamp] Running TODO auto-check..."
    python $scriptPath >> $logFile 2>&1
    Add-Content $logFile "[$timestamp] Cycle complete.`n"
    Start-Sleep -Seconds 3600
}