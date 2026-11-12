# Launch KinetixAI (FlowVids-AI) FastAPI Core Orchestrator Backend
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
Write-Host "Starting KinetixAI FastAPI Core Orchestrator at http://127.0.0.1:8000 ..." -ForegroundColor Cyan
uv run uvicorn src.presentation.api.main:app --host 127.0.0.1 --port 8000 --reload
