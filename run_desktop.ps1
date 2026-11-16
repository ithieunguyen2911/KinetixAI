# Launch KinetixAI (FlowVids-AI) Native Windows WPF Desktop Application (NLE v3.0)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Stopping any previous KinetixAI.Desktop & Core API instances..." -ForegroundColor DarkGray
Stop-Process -Name "KinetixAI.Desktop" -Force -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process -Filter "CommandLine LIKE '%src.presentation.api.main%'" -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Milliseconds 400

Write-Host "Building KinetixAI Desktop Studio (WPF NLE v3.0)..." -ForegroundColor Cyan
dotnet build desktop_app/KinetixAI.Desktop/KinetixAI.Desktop.csproj --nologo -v q
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

$exePath = Join-Path $PSScriptRoot "desktop_app\KinetixAI.Desktop\bin\Debug\net10.0-windows\KinetixAI.Desktop.exe"
$proc = Start-Process -FilePath $exePath -WorkingDirectory $PSScriptRoot -PassThru
Write-Host "Kinetix Studio v3.0 NLE Workstation is now running (PID: $($proc.Id))." -ForegroundColor Green
