# Quickstart & Validation Guide: KinetixAI (FlowVids-AI) v3.0 Studio

## 1. Run Full Unit & Integration Test Suite
```powershell
uv run pytest -v
```

## 2. Verify Studio Catalog & MCP Server Self-Test
```powershell
uv run python -m src.presentation.mcp.mcp_server --self-test
```

## 3. Purge Legacy SMPTE Bars & Launch Native Windows WPF Workstation v3.0
```powershell
.\run_desktop.ps1
```
