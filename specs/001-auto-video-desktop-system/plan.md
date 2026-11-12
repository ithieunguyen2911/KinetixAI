# Implementation Plan: KinetixAI (FlowVids-AI) Automated Video Production & Desktop Studio

**Branch**: `001-auto-video-desktop-system` | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-auto-video-desktop-system/spec.md`

## Summary

Build a Polyglot Modular Monolith Desktop Application and Automated Video Production System combining 5 core media tools (`yt-dlp`, `Whisper`/`faster-whisper`, `FFmpeg`, `Remotion`, and `HyperFrames`) managed under GitHub Spec Kit (`specify-cli`) and Clean Architecture + SOLID principles. Python 3.11+ serves as the Core Orchestrator and FastAPI REST Backend (`src/domain`, `src/application`, `src/infrastructure`, `src/presentation`), Node.js 20+ / TypeScript drives the visual render engines (`render_engines/remotion_engine` and `render_engines/hyperframes_engine`), and a native Windows C# .NET WPF Desktop App (`desktop_app/KinetixAI.Desktop`) plus Streamlit/CLI presentation clients provide a responsive user experience.

## Technical Context

**Language/Version**: Python 3.11+ (managed via `uv`), Node.js 24+ / TypeScript 5+, C# 12 / .NET (WPF Windows Desktop)

**Primary Dependencies**:
- **Python Core & API**: `fastapi`, `uvicorn`, `pydantic` (v2), `yt-dlp`, `faster-whisper`, `openai-whisper`, `ffmpeg-python`, `httpx`, `streamlit`, `pytest`
- **Visual Render Engines**: `remotion`, `@remotion/cli`, `@remotion/renderer`, `react`, `react-dom`, `hyperframes` (HTML/CSS/GSAP deterministic renderer + CLI bridge)
- **Media Processing**: `FFmpeg` 8.x CLI (`ffmpeg`, `ffprobe`) + `ffmpeg-python`
- **Windows Desktop Client**: .NET WPF (`System.Net.Http.Json`, MVVM architecture, process manager for FastAPI backend)

**Storage**: File-system workspace (`workspace/` for project artifacts, raw downloads, extracted WAV audio, JSON subtitles, rendered overlay MP4s, and final composited MP4s) + JSON project state persistence (`workspace/projects.json`).

**Testing**: `pytest` (unit tests for Domain Entities, Factories, Adapters, Pipeline, and integration tests for FastAPI & end-to-end media processing) + `dotnet build` verification for the WPF Desktop Client.

**Target Platform**: Windows 10/11 Desktop (with cross-platform Python Core + Node.js Render Engines).

**Project Type**: Polyglot Desktop Application (`desktop-app` + `web-service` + `cli`).

**Performance Goals**:
- Audio extraction (`16kHz` mono WAV) via FFmpeg stream processing in < 2 seconds for short clips.
- Overlay rendering decoupling: Render lightweight caption overlays via Remotion / HyperFrames and composite over the raw video stream with FFmpeg (`overlay` / `drawtext` / hardware-accelerated H.264 encoding).

**Constraints**:
- Strict Clean Architecture dependency rule: `domain` has zero external dependencies; `application` depends only on `domain`; `infrastructure` implements `domain` ABC interfaces; `presentation` and `desktop_app` contain zero business logic.
- Must work both online (with live YouTube/video URLs and Whisper models) and offline/deterministically (with built-in FFmpeg sample media generation and script/fallback transcription).

**Scale/Scope**: Single-user / studio workstation handling multi-step automated video production projects with full job history, subtitle timeline editor/viewer, and dual render engine support.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Gate 1 - Clean Architecture & Layer Isolation (Principle I)**: PASS. `src/domain`, `src/application`, `src/infrastructure`, `src/presentation`, `render_engines/`, and `desktop_app/` are strictly separated.
- **Gate 2 - SOLID & Dependency Inversion (Principle II)**: PASS. `AutoVideoPipeline` receives `IMediaDownloader`, `IVideoProcessor`, `ITranscriber`, and `IVisualRenderer` via constructor Dependency Injection; `RendererFactory` switches between `RemotionAdapter` and `HyperFramesAdapter`.
- **Gate 3 - Adapter Pattern for 5 External Tools (Principle III)**: PASS. All 5 tools (`YtDlpAdapter`, `WhisperAdapter`, `FfmpegAdapter`, `RemotionAdapter`, `HyperFramesAdapter`) inherit from `src/domain/interfaces/` ABCs.
- **Gate 4 - Strict Type Hinting & Data Contracts (Principle IV)**: PASS. Python 3.11+ type hints and Pydantic v2 models enforce all API and subprocess JSON contracts.
- **Gate 5 - Test-Driven Quality & Pytest Coverage (Principle V)**: PASS. Unit and integration test suites under `tests/unit/` and `tests/integration/` cover all layers.

## Project Structure

### Documentation (this feature)

```text
specs/001-auto-video-desktop-system/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── api-and-render-contracts.md
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code (repository root)

```text
KinetixAI/
├── .specify/                         # GitHub Spec Kit configuration, constitution, templates, scripts
├── render_engines/                   # Sub-projects for Node.js Visual Renderers
│   ├── remotion_engine/              # React templates & CLI runner for Remotion
│   │   ├── package.json
│   │   ├── src/
│   │   │   ├── index.ts
│   │   │   ├── Root.tsx
│   │   │   └── CaptionTemplate.tsx
│   │   └── render.mjs                # Deterministic Remotion CLI/Node render entrypoint
│   └── hyperframes_engine/           # HTML/CSS/GSAP deterministic compositions for HyperFrames
│       ├── package.json
│       ├── templates/
│       │   └── CaptionTemplate.html
│       └── render.mjs                # Deterministic HyperFrames HTML/GSAP render entrypoint
├── src/
│   ├── domain/                       # Enterprise Business Rules (Zero external library dependencies)
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── enums.py              # RenderEngineType, JobStatus
│   │   │   ├── subtitle_segment.py   # SubtitleSegment, WordTimestamp
│   │   │   ├── media_asset.py        # MediaAsset
│   │   │   ├── render_job.py         # RenderJob
│   │   │   └── video_project.py      # VideoProject
│   │   └── interfaces/
│   │       ├── __init__.py
│   │       ├── media_downloader.py   # IMediaDownloader (ABC)
│   │       ├── transcriber.py        # ITranscriber (ABC)
│   │       ├── visual_renderer.py    # IVisualRenderer (ABC)
│   │       └── video_processor.py    # IVideoProcessor (ABC)
│   ├── application/                  # Application Business Rules (Use Cases & Factories)
│   │   ├── __init__.py
│   │   ├── factories/
│   │   │   ├── __init__.py
│   │   │   └── renderer_factory.py   # RendererFactory (Remotion vs HyperFrames)
│   │   ├── pipelines/
│   │   │   ├── __init__.py
│   │   │   └── auto_video_pipeline.py # AutoVideoPipeline (5-step Orchestrator)
│   │   └── services/
│   │       ├── __init__.py
│   │       └── project_service.py    # Project & Job orchestration service
│   ├── infrastructure/               # Frameworks, Drivers & 5 Tool Adapters
│   │   ├── __init__.py
│   │   ├── downloaders/
│   │   │   ├── __init__.py
│   │   │   └── ytdlp_adapter.py      # YtDlpAdapter(IMediaDownloader)
│   │   ├── transcribers/
│   │   │   ├── __init__.py
│   │   │   └── whisper_adapter.py    # WhisperAdapter(ITranscriber)
│   │   ├── processors/
│   │   │   ├── __init__.py
│   │   │   └── ffmpeg_adapter.py     # FfmpegAdapter(IVideoProcessor)
│   │   ├── renderers/
│   │   │   ├── __init__.py
│   │   │   ├── remotion_adapter.py   # RemotionAdapter(IVisualRenderer)
│   │   │   └── hyperframes_adapter.py # HyperFramesAdapter(IVisualRenderer)
│   │   └── repositories/
│   │       ├── __init__.py
│   │       └── json_project_repository.py
│   └── presentation/                 # Interface Adapters (FastAPI, CLI, Streamlit UI)
│       ├── __init__.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   └── project_schemas.py    # Pydantic v2 Request/Response contracts
│       ├── api/
│       │   ├── __init__.py
│       │   └── main.py               # FastAPI REST Server
│       ├── cli/
│       │   ├── __init__.py
│       │   └── main.py               # CLI Runner
│       └── ui/
│           ├── __init__.py
│           └── streamlit_app.py      # Streamlit Studio Dashboard
├── desktop_app/                      # Native Windows Desktop Client (.NET WPF)
│   └── KinetixAI.Desktop/
│       ├── KinetixAI.Desktop.csproj
│       ├── App.xaml
│       ├── App.xaml.cs
│       ├── MainWindow.xaml
│       ├── MainWindow.xaml.cs
│       └── Models/
│           └── ApiModels.cs
└── tests/                            # Automated Test Suite (pytest)
    ├── unit/
    │   ├── test_domain_entities.py
    │   ├── test_renderer_factory.py
    │   ├── test_adapters.py
    │   └── test_auto_video_pipeline.py
    └── integration/
        ├── test_end_to_end_pipeline.py
        └── test_fastapi_endpoints.py
```

**Structure Decision**: Adopted the exact Clean Architecture Polyglot layout from the architectural plan (`render_engines/`, `src/domain`, `src/application`, `src/infrastructure`, `src/presentation`, `tests/`) augmented with `desktop_app/KinetixAI.Desktop` for the native Windows C# WPF Desktop App.

## Complexity Tracking

No Constitution violations exist. All 5 adapters, domain interfaces, application orchestrators, and presentation clients strictly follow the ratified Constitution v1.0.0.
