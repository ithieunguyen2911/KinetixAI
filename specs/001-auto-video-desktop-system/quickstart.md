# Quickstart & Validation Guide: KinetixAI (FlowVids-AI) v2.0 Professional NLE

## Prerequisites

- **Python**: 3.11+ with `uv` (`uv --version`)
- **Node.js**: 20+ (`node --version`)
- **FFmpeg**: 6.0+ in system PATH (`ffmpeg -version`, `ffprobe -version`)
- **.NET SDK**: 8.0+ / 10.0 (`dotnet --version`) for building the native Windows WPF NLE Workstation
- **GitHub Spec Kit**: `specify-cli` (`specify version`)

## 1. Run Full Unit & Integration Test Suite

```powershell
uv run pytest -v
```

## 2. Verify MCP Server (`kinetix-ai`) Self-Test

```powershell
uv run python -m src.presentation.mcp.mcp_server --self-test
```

## 3. Run Automated Pipeline via CLI (4 Templates x 2 Render Engines)

```powershell
# HyperFrames Engine with TechCalloutHUD template
uv run python -m src.presentation.cli.main --project-id nle_hf --source "demo://sample" --engine hyperframes --template TechCalloutHUD

# Remotion Engine with KineticTitleCard template
uv run python -m src.presentation.cli.main --project-id nle_remotion --source "demo://sample" --engine remotion --template KineticTitleCard
```

## 4. Build & Launch the Native Windows C# WPF NLE Workstation

```powershell
dotnet build desktop_app/KinetixAI.Desktop/KinetixAI.Desktop.csproj
dotnet run --project desktop_app/KinetixAI.Desktop/KinetixAI.Desktop.csproj
```
