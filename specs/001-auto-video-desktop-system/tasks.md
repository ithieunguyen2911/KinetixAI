---
description: "Actionable, dependency-ordered task list for KinetixAI (FlowVids-AI) Automated Video Production, Desktop Studio & Antigravity MCP"
---

# Tasks: KinetixAI (FlowVids-AI) Automated Video Production, Desktop Studio & Antigravity MCP

**Input**: Design documents from `/specs/001-auto-video-desktop-system/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/api-and-render-contracts.md`, `quickstart.md`

**Tests**: Automated `pytest` unit and integration tests are MANDATORY per Constitution Principle V.

**Organization**: Tasks are grouped by Phase (Setup -> Foundational Domain & ABCs -> User Story 1 Core Pipeline & Adapters -> User Story 2 Dual Visual Render Engines -> User Story 3 FastAPI + Native Windows Desktop App + Streamlit UI + Antigravity MCP Server -> Polish & Verification).

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create Clean Architecture directory hierarchy (`src/domain`, `src/application`, `src/infrastructure`, `src/presentation`, `render_engines/remotion_engine`, `render_engines/hyperframes_engine`, `desktop_app/KinetixAI.Desktop`, `tests/unit`, `tests/integration`) and `.gitignore` at repository root
- [X] T002 Initialize Python project with `uv` (`pyproject.toml`) and install core dependencies (`yt-dlp`, `faster-whisper`, `ffmpeg-python`, `fastapi`, `uvicorn`, `pydantic`, `httpx`, `streamlit`, `mcp`, `pytest`)
- [X] T003 [P] Initialize Node.js visual renderer workspace and install Remotion & HyperFrames packages in `render_engines/remotion_engine/package.json` and `render_engines/hyperframes_engine/package.json`

---

## Phase 2: Foundational (Domain Entities & Abstract Interfaces)

- [X] T004 [P] Implement `RenderEngineType` (`remotion`, `hyperframes`) and `JobStatus` enums in `src/domain/entities/enums.py`
- [X] T005 [P] Implement `WordTimestamp` and `SubtitleSegment` (`start_time >= 0.0`, `end_time > start_time`, non-empty stripped `text`) dataclasses in `src/domain/entities/subtitle_segment.py`
- [X] T006 [P] Implement `MediaAsset` and `RenderJob` (`0 <= progress_percent <= 100`) dataclasses in `src/domain/entities/media_asset.py` and `src/domain/entities/render_job.py`
- [X] T007 Implement `VideoProject` entity dataclass in `src/domain/entities/video_project.py` and export all domain entities in `src/domain/entities/__init__.py`
- [X] T008 [P] Define abstract interfaces `IMediaDownloader`, `ITranscriber`, `IVisualRenderer`, and `IVideoProcessor` using `abc.ABC` and `@abstractmethod` in `src/domain/interfaces/` (`media_downloader.py`, `transcriber.py`, `visual_renderer.py`, `video_processor.py`, `__init__.py`)
- [X] T009 Write unit tests for all domain entities, validation constraints, and abstract interface contracts in `tests/unit/test_domain_entities.py`

---

## Phase 3: User Story 1 - End-to-End Automated Video Production Pipeline (Priority: P1) 🎯 MVP

- [X] T010 [P] [US1] Write unit tests for `YtDlpAdapter`, `FfmpegAdapter`, `WhisperAdapter`, and `AutoVideoPipeline` in `tests/unit/test_adapters.py` and `tests/unit/test_auto_video_pipeline.py`
- [X] T011 [P] [US1] Implement `YtDlpAdapter(IMediaDownloader)` supporting live `yt-dlp` URL downloads, local file ingestion, and deterministic `demo://sample` test video generation via FFmpeg in `src/infrastructure/downloaders/ytdlp_adapter.py`
- [X] T012 [P] [US1] Implement `FfmpegAdapter(IVideoProcessor)` for 16kHz mono WAV audio extraction (`extract_audio`) and hardware/software overlay compositing + subtitle export (`merge_and_export`) in `src/infrastructure/processors/ffmpeg_adapter.py`
- [X] T013 [P] [US1] Implement `WhisperAdapter(ITranscriber)` supporting `faster-whisper`, `openai-whisper`, and deterministic script/audio fallback transcription with accurate timestamps in `src/infrastructure/transcribers/whisper_adapter.py`
- [X] T014 [US1] Implement `AutoVideoPipeline` orchestrator with Dependency Injection and step-by-step progress callbacks in `src/application/pipelines/auto_video_pipeline.py`

---

## Phase 4: User Story 2 - Dynamic Visual Render Engine Switching (Remotion vs HyperFrames) (Priority: P2)

- [X] T015 [P] [US2] Write unit and integration tests for `RendererFactory`, `RemotionAdapter`, and `HyperFramesAdapter` in `tests/unit/test_renderer_factory.py` and `tests/integration/test_end_to_end_pipeline.py`
- [X] T016 [P] [US2] Create Remotion React composition template (`CaptionTemplate.tsx`, `Root.tsx`, `index.ts`) and deterministic HUD + timed caption render runner in `render_engines/remotion_engine/`
- [X] T017 [P] [US2] Create HyperFrames HTML/CSS/GSAP composition template (`CaptionTemplate.html`, `hyperframes.config.json`) and deterministic HUD + timed caption render runner in `render_engines/hyperframes_engine/`
- [X] T018 [P] [US2] Implement `RemotionAdapter(IVisualRenderer)` and `HyperFramesAdapter(IVisualRenderer)` with JSON props serialization in `src/infrastructure/renderers/remotion_adapter.py` and `src/infrastructure/renderers/hyperframes_adapter.py`
- [X] T019 [US2] Implement `RendererFactory` in `src/application/factories/renderer_factory.py` to instantiate `RemotionAdapter` or `HyperFramesAdapter` from `RenderEngineType`

---

## Phase 5: User Story 3 - Native Windows Desktop App, REST API & Antigravity MCP Server (Priority: P3)

- [X] T020 [P] [US3] Write FastAPI and MCP integration tests in `tests/integration/test_fastapi_endpoints.py` and `tests/integration/test_mcp_server.py`
- [X] T021 [P] [US3] Implement `JsonProjectRepository` in `src/infrastructure/repositories/json_project_repository.py` and `ProjectService` in `src/application/services/project_service.py`
- [X] T022 [P] [US3] Implement Pydantic v2 data contract schemas in `src/presentation/schemas/project_schemas.py`
- [X] T023 [US3] Implement FastAPI REST API server (`/api/v1/health`, `/api/v1/projects`, `/api/v1/mcp/command`, `/api/v1/mcp/tools`, `/api/v1/projects/{project_id}/subtitles`) in `src/presentation/api/main.py`
- [X] T024 [P] [US3] Implement CLI entrypoint in `src/presentation/cli/main.py`, Streamlit Studio UI in `src/presentation/ui/streamlit_app.py`, and Model Context Protocol (MCP) Server (`kinetix-ai`) in `src/presentation/mcp/mcp_server.py`
- [X] T025 [US3] Build Native Windows C# .NET WPF Desktop Application (`KinetixAI.Desktop.csproj`, `MainWindow.xaml`, `MainWindow.xaml.cs`) in `desktop_app/KinetixAI.Desktop/` with AI MCP Command Bar, 3-second real-time MCP Live Watcher, engine selector (Remotion vs HyperFrames), subtitle editor, and one-click MP4 playback

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T026 [P] Register `kinetix-ai` MCP Server in `~/.gemini/config/mcp_config.json`, `.agents/mcp_config.json`, `.agents/skills/kinetix-video-producer/SKILL.md`, `AGENTS.md`, and update launcher scripts (`run_desktop.ps1`, `run_api.ps1`, `README.md`)
- [X] T027 Run full `pytest` suite (`15 passed`), rebuild `KinetixAI.Desktop`, execute live AI Antigravity MCP video production command, and verify `/speckit-converge`
