# Launch KinetixAI (FlowVids-AI) Native Windows WPF Desktop Application (NLE v6.0)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Stopping any previous KinetixAI.Desktop & Core API instances..." -ForegroundColor DarkGray
Stop-Process -Name "KinetixAI.Desktop" -Force -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process -Filter "CommandLine LIKE '%src.presentation.api.main%'" -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Milliseconds 400

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "Starting FastAPI Core Orchestrator (.venv\Scripts\python.exe) on http://127.0.0.1:8000..." -ForegroundColor Cyan
    $apiProc = Start-Process -FilePath $venvPython `
        -ArgumentList "-m", "uvicorn", "src.presentation.api.main:app", "--host", "127.0.0.1", "--port", "8000" `
        -WorkingDirectory $PSScriptRoot `
        -WindowStyle Hidden `
        -PassThru
} else {
    Write-Host "Starting FastAPI Core Orchestrator (uv) on http://127.0.0.1:8000..." -ForegroundColor Cyan
    $apiProc = Start-Process -FilePath "uv" `
        -ArgumentList "run", "uvicorn", "src.presentation.api.main:app", "--host", "127.0.0.1", "--port", "8000" `
        -WorkingDirectory $PSScriptRoot `
        -WindowStyle Hidden `
        -PassThru
}

$backendReady = $false
for ($i = 1; $i -le 30; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
        if ($resp.status -eq "ok") {
            $backendReady = $true
            Write-Host "FastAPI Core Orchestrator is ONLINE (PID: $($apiProc.Id), projects synced ready)." -ForegroundColor Green
            break
        }
    } catch {
        # Retry until FastAPI finishes startup
    }
}

if (-not $backendReady) {
    Write-Warning "FastAPI Core Orchestrator did not respond within 15s; Desktop app will retry connection on load."
}

Write-Host "Building KinetixAI Desktop Studio (WPF NLE v6.0)..." -ForegroundColor Cyan
dotnet build desktop_app/KinetixAI.Desktop/KinetixAI.Desktop.csproj --nologo -v q
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

$exePath = Join-Path $PSScriptRoot "desktop_app\KinetixAI.Desktop\bin\Debug\net10.0-windows\KinetixAI.Desktop.exe"
$proc = Start-Process -FilePath $exePath -WorkingDirectory $PSScriptRoot -PassThru
Write-Host "Kinetix Studio v6.0 NLE Workstation is now running (PID: $($proc.Id))." -ForegroundColor Green
