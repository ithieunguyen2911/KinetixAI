# Quickstart & Validation Guide: KinetixAI (FlowVids-AI)

## Prerequisites

- **Python**: 3.11+ with `uv` (`uv --version`)
- **Node.js**: 20+ (`node --version`)
- **FFmpeg**: 6.0+ in system PATH (`ffmpeg -version`)
- **.NET SDK**: 8.0+ (`dotnet --version`) for building/running the native Windows WPF Desktop App
- **GitHub Spec Kit**: `specify-cli` (`specify check`)

## 1. Run Automated Unit & Integration Tests

```powershell
uv run pytest -v
```

Expected outcome: All unit tests (domain entities, `RendererFactory`, 5 adapters, `AutoVideoPipeline`) and integration tests (end-to-end video pipeline with both `remotion` and `hyperframes`, plus FastAPI REST endpoints) pass (`0 failed`).

## 2. Run End-to-End Pipeline via CLI

```powershell
# Run with HyperFrames Engine
uv run python -m src.presentation.cli.main --project-id demo_hf --source "demo://sample" --engine hyperframes

# Run with Remotion Engine
uv run python -m src.presentation.cli.main --project-id demo_remotion --source "demo://sample" --engine remotion
```

Expected outcome: Generates `workspace/demo_hf/demo_hf_final.mp4` and `workspace/demo_remotion/demo_remotion_final.mp4` with extracted audio, transcribed JSON subtitles, rendered visual overlay, and merged MP4 video.

## 3. Start the FastAPI Core Orchestrator Backend

```powershell
uv run uvicorn src.presentation.api.main:app --host 127.0.0.1 --port 8000
```

## 4. Launch the Native Windows C# WPF Desktop Application

```powershell
dotnet run --project desktop_app/KinetixAI.Desktop/KinetixAI.Desktop.csproj
```

*(Note: The WPF Desktop Application automatically checks if the FastAPI backend is running on port 8000 and starts it in the background if needed.)*

## 5. Alternative: Launch the Streamlit Web Studio

```powershell
uv run streamlit run src/presentation/ui/streamlit_app.py
```
