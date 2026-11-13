# Launch KinetixAI (FlowVids-AI) Native Windows WPF Desktop Application (NLE v2.0)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Stopping any previous KinetixAI.Desktop instance..." -ForegroundColor DarkGray
Stop-Process -Name "KinetixAI.Desktop" -Force -ErrorAction SilentlyContinue
Start-Sleep -Milliseconds 300

Write-Host "Building KinetixAI Desktop Studio (WPF NLE v2.0)..." -ForegroundColor Cyan
dotnet build desktop_app/KinetixAI.Desktop/KinetixAI.Desktop.csproj --nologo -v q
if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

$exePath = Join-Path $PSScriptRoot "desktop_app\KinetixAI.Desktop\bin\Debug\net10.0-windows\KinetixAI.Desktop.exe"
$proc = Start-Process -FilePath $exePath -WorkingDirectory $PSScriptRoot -PassThru
Write-Host "Kinetix Studio v2.0 NLE Workstation is now running (PID: $($proc.Id))." -ForegroundColor Green
