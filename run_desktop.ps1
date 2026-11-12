# Launch KinetixAI (FlowVids-AI) Native Windows WPF Desktop Application
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "Building & Launching KinetixAI Desktop Studio (WPF)..." -ForegroundColor Cyan
dotnet run --project desktop_app/KinetixAI.Desktop/KinetixAI.Desktop.csproj
