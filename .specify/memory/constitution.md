<!--
Sync Impact Report
- Version change: 0.0.0 (template) → 1.0.0
- Modified principles:
  - [PRINCIPLE_1_NAME] → I. Clean Architecture & Layer Isolation (NON-NEGOTIABLE)
  - [PRINCIPLE_2_NAME] → II. SOLID & Dependency Inversion (NON-NEGOTIABLE)
  - [PRINCIPLE_3_NAME] → III. Adapter Pattern for Third-Party Integrations
  - [PRINCIPLE_4_NAME] → IV. Strict Type Hinting & Data Contracts
  - [PRINCIPLE_5_NAME] → V. Test-Driven Quality & Pytest Coverage (NON-NEGOTIABLE)
- Added sections:
  - Polyglot Architecture & Performance Constraints
  - Development Workflow & Quality Gates
- Removed sections: None
- Follow-up TODOs: None
-->

# KinetixAI (FlowVids-AI) Constitution

## Core Principles

### I. Clean Architecture & Layer Isolation (NON-NEGOTIABLE)
The codebase MUST strictly enforce Clean Architecture separated into four concentric, independent layers: `domain`, `application`, `infrastructure`, and `presentation` (plus isolated `render_engines/` and `desktop_app/` clients).
- The `domain` layer MUST contain only pure business entities (`VideoProject`, `SubtitleSegment`, `MediaAsset`, `RenderJob`) and abstract interfaces (`IMediaDownloader`, `ITranscriber`, `IVisualRenderer`, `IVideoProcessor`). It MUST NOT import or depend on any third-party library, framework, CLI tool, or outer layer.
- The `application` layer MUST orchestrate use cases (`AutoVideoPipeline`, `RendererFactory`) strictly through domain interfaces via Dependency Injection.
- No business logic or media orchestration logic may reside in the `presentation` layer (FastAPI routes, CLI handlers, Streamlit UI, or C# WPF Desktop UI).

### II. SOLID & Dependency Inversion (NON-NEGOTIABLE)
Every class and module MUST adhere to SOLID principles:
- **Single Responsibility Principle (SRP)**: Each class MUST have a single responsibility (e.g., downloading media, transcribing audio, rendering visuals, or processing video streams).
- **Open/Closed Principle (OCP)**: New render engines or transcription providers MUST be addable via new Adapter implementations and `RendererFactory` registration without modifying `AutoVideoPipeline`.
- **Liskov Substitution Principle (LSP)**: `RemotionAdapter` and `HyperFramesAdapter` MUST be completely interchangeable implementations of `IVisualRenderer`.
- **Interface Segregation Principle (ISP)**: Interfaces MUST remain focused and minimal (`IMediaDownloader`, `ITranscriber`, `IVisualRenderer`, `IVideoProcessor`).
- **Dependency Inversion Principle (DIP)**: High-level application pipelines MUST depend exclusively on Python `abc.ABC` interfaces with `@abstractmethod` contracts.

### III. Adapter Pattern for Third-Party Integrations
All five external tools (`yt-dlp`, `Whisper`/`faster-whisper`, `FFmpeg`, `Remotion`, and `HyperFrames`) MUST be encapsulated inside dedicated Adapter classes under `src/infrastructure/`:
- `YtDlpAdapter` (`IMediaDownloader`)
- `WhisperAdapter` (`ITranscriber`)
- `FfmpegAdapter` (`IVideoProcessor`)
- `RemotionAdapter` and `HyperFramesAdapter` (`IVisualRenderer`)
Direct calls to `yt_dlp`, `whisper`, `faster_whisper`, `ffmpeg`, or `subprocess` outside `src/infrastructure/` are strictly forbidden.

### IV. Strict Type Hinting & Data Contracts
All Python functions, methods, dataclasses, and class attributes MUST include explicit Python 3.11+ type annotations (`pathlib.Path`, `List`, `Dict`, `Any`, union types `|`). Cross-process and REST API boundaries (Python Core <-> Node.js Render Engines and Python FastAPI <-> Desktop Client) MUST use validated JSON Data Contracts defined via Pydantic v2 models or dataclasses.

### V. Test-Driven Quality & Pytest Coverage (NON-NEGOTIABLE)
Every domain entity, factory, pipeline orchestrator, adapter, and API endpoint MUST be accompanied by automated unit and integration tests written with `pytest`. External CLI/network dependencies in unit tests MUST be deterministically testable using mocks or local fixture assets, while end-to-end integration tests verify real media processing pipelines.

## Polyglot Architecture & Performance Constraints

- **Core Orchestrator**: Python 3.11+ managed via `uv`, exposing both direct Python APIs and a FastAPI REST server.
- **Visual Render Engines**: Node.js 20+ / TypeScript sub-projects under `render_engines/remotion_engine` and `render_engines/hyperframes_engine`, invoked via deterministic JSON props contracts.
- **Overlay Optimization**: Visual render engines SHOULD render subtitle/motion graphic overlays or short visual compositions rather than decoding multi-hundred-megabyte raw source videos inside headless browsers; `FfmpegAdapter` handles stream extraction, overlay compositing, and final MP4 encoding.
- **Desktop Client**: Native Windows Desktop Application (C# .NET WPF + Python Desktop/FastAPI integration) communicating exclusively with the Presentation/Application layer via REST/JSON contracts.

## Development Workflow & Quality Gates

1. **Specification First**: All features MUST be documented in `specs/<feature>/spec.md`, planned in `plan.md`, and decomposed into `tasks.md` via GitHub Spec Kit before implementation.
2. **Automated Verification**: `uv run pytest` MUST pass with zero errors before any task phase is marked complete.
3. **Convergence Audit**: `/speckit-converge` MUST verify 100% alignment between `constitution.md`, `spec.md`, `plan.md`, `tasks.md`, and the implemented codebase.

## Governance

This Constitution supersedes all ad-hoc coding practices within KinetixAI. Any architectural change requires updating `.specify/memory/constitution.md`, incrementing the semantic version, and running `/speckit-converge` to verify compliance across all layers.

**Version**: 1.0.0 | **Ratified**: 2026-11-13 | **Last Amended**: 2026-11-13
