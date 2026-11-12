---
description: "Actionable, dependency-ordered task list for KinetixAI (FlowVids-AI) Automated Video Production, Desktop Studio & Antigravity MCP"
---

# Tasks: KinetixAI (FlowVids-AI) Automated Video Production, Desktop Studio & Antigravity MCP

**Input**: Design documents from `/specs/001-auto-video-desktop-system/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/api-and-render-contracts.md`, `quickstart.md`

**Tests**: Automated `pytest` unit and integration tests are MANDATORY per Constitution Principle V.

**Organization**: Tasks are grouped by Phase (Phase 1 Setup -> Phase 2 Foundational Domain & ABCs -> Phase 3 User Story 1 Core Pipeline & Adapters -> Phase 4 User Story 2 Dual Visual Render Engines -> Phase 5 User Story 3 FastAPI + Native Windows Desktop App + Streamlit UI + Antigravity MCP Server -> Phase 6 Polish -> Phase 7 Deep Feature Audit & End-to-End Remediation).

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Create Clean Architecture directory hierarchy (`src/domain`, `src/application`, `src/infrastructure`, `src/presentation`, `render_engines/remotion_engine`, `render_engines/hyperframes_engine`, `desktop_app/KinetixAI.Desktop`, `tests/unit`, `tests/integration`) and `.gitignore` at repository root
- [X] T002 Initialize Python project with `uv` (`pyproject.toml`) and install core dependencies (`yt-dlp`, `faster-whisper`, `ffmpeg-python`, `fastapi`, `uvicorn`, `pydantic`, `httpx`, `streamlit`, `mcp`, `pytest`)
- [X] T003 [P] Initialize Node.js visual renderer workspace and install Remotion & HyperFrames packages in `render_engines/remotion_engine/package.json` and `render_engines/hyperframes_engine/package.json`

---

## Phase 2: Foundational (Domain Entities & Abstract Interfaces)

- [X] T004 [P] Implement `RenderEngineType` (`remotion`, `hyperframes`) and `JobStatus` enums in `src/domain/entities/enums.py`
- [X] T005 [P] Implement `WordTimestamp` and `SubtitleSegment` (`start_time >= 0.0`, `end_time > start_time`, non-empty stripped `text`, automatic `sync_words()`) dataclasses in `src/domain/entities/subtitle_segment.py`
- [X] T006 [P] Implement `MediaAsset` and `RenderJob` (`0 <= progress_percent <= 100`) dataclasses in `src/domain/entities/media_asset.py` and `src/domain/entities/render_job.py`
- [X] T007 Implement `VideoProject` entity dataclass in `src/domain/entities/video_project.py` and export all domain entities in `src/domain/entities/__init__.py`
- [X] T008 [P] Define abstract interfaces `IMediaDownloader`, `ITranscriber`, `IVisualRenderer`, and `IVideoProcessor` using `abc.ABC` and `@abstractmethod` in `src/domain/interfaces/` (`media_downloader.py`, `transcriber.py`, `visual_renderer.py`, `video_processor.py`, `__init__.py`)
- [X] T009 Write unit tests for all domain entities, validation constraints, and abstract interface contracts in `tests/unit/test_domain_entities.py`

---

## Phase 3: User Story 1 - End-to-End Automated Video Production Pipeline (Priority: P1) 🎯 MVP

- [X] T010 [P] [US1] Write unit tests for `YtDlpAdapter`, `FfmpegAdapter`, `WhisperAdapter`, and `AutoVideoPipeline` in `tests/unit/test_adapters.py` and `tests/unit/test_auto_video_pipeline.py`
- [X] T011 [P] [US1] Implement `YtDlpAdapter(IMediaDownloader)` supporting live `yt-dlp` URL downloads, `extract_metadata`, `download_ranges` clipping, local file ingestion, and spoken `demo://sample` synthesis in `src/infrastructure/downloaders/ytdlp_adapter.py`
- [X] T012 [P] [US1] Implement `FfmpegAdapter(IVideoProcessor)` for `probe_media` (`ffprobe`), 16kHz mono WAV extraction (`extract_audio`), `trim_video`, `mix_audio_tracks`, and overlay compositing + `.srt`/`.vtt` export (`merge_and_export`) in `src/infrastructure/processors/ffmpeg_adapter.py`
- [X] T013 [P] [US1] Implement `WhisperAdapter(ITranscriber)` supporting `faster-whisper` (with VAD), `openai-whisper`, Windows offline Speech Recognition, script alignment, and `.transcript.json` export in `src/infrastructure/transcribers/whisper_adapter.py`
- [X] T014 [US1] Implement `AutoVideoPipeline` orchestrator with Dependency Injection and step-by-step progress callbacks in `src/application/pipelines/auto_video_pipeline.py`

---

## Phase 4: User Story 2 - Dynamic Visual Render Engine Switching (Remotion vs HyperFrames) (Priority: P2)

- [X] T015 [P] [US2] Write unit and integration tests for `RendererFactory`, `RemotionAdapter`, and `HyperFramesAdapter` in `tests/unit/test_renderer_factory.py` and `tests/integration/test_end_to_end_pipeline.py`
- [X] T016 [P] [US2] Create Remotion React composition template (`CaptionTemplate.tsx`, `Root.tsx`, `index.ts`) and deterministic HUD + timed caption render runner in `render_engines/remotion_engine/`
- [X] T017 [P] [US2] Create HyperFrames HTML/CSS/GSAP composition template (`index.html`, `compositions/captions.html`, `hyperframes.config.json`) following the 12-Rule HyperFrames Contract in `render_engines/hyperframes_engine/`
- [X] T018 [P] [US2] Implement `RemotionAdapter(IVisualRenderer)` and `HyperFramesAdapter(IVisualRenderer)` with JSON props serialization in `src/infrastructure/renderers/remotion_adapter.py` and `src/infrastructure/renderers/hyperframes_adapter.py`
- [X] T019 [US2] Implement `RendererFactory` in `src/application/factories/renderer_factory.py` to instantiate `RemotionAdapter` or `HyperFramesAdapter` from `RenderEngineType`

---

## Phase 5: User Story 3 - Native Windows Desktop App, REST API & Antigravity MCP Server (Priority: P3)

- [X] T020 [P] [US3] Write FastAPI and MCP integration tests in `tests/integration/test_fastapi_endpoints.py` and `tests/integration/test_mcp_server.py`
- [X] T021 [P] [US3] Implement `JsonProjectRepository` in `src/infrastructure/repositories/json_project_repository.py` and `ProjectService` in `src/application/services/project_service.py`
- [X] T022 [P] [US3] Implement Pydantic v2 data contract schemas in `src/presentation/schemas/project_schemas.py`
- [X] T023 [US3] Implement FastAPI REST API server (`/api/v1/health`, `/api/v1/projects`, `/api/v1/mcp/command`, `/api/v1/mcp/tools`, `/api/v1/projects/{project_id}/subtitles`, `/probe`, `/trim`) in `src/presentation/api/main.py`
- [X] T024 [P] [US3] Implement CLI entrypoint in `src/presentation/cli/main.py`, Streamlit Studio UI in `src/presentation/ui/streamlit_app.py`, and Model Context Protocol (MCP) Server (`kinetix-ai`) in `src/presentation/mcp/mcp_server.py`
- [X] T025 [US3] Build Native Windows C# .NET WPF Desktop Application (`KinetixAI.Desktop.csproj`, `App.xaml`, `MainWindow.xaml`, `MainWindow.xaml.cs`) in `desktop_app/KinetixAI.Desktop/` with Dark Slate NLE Studio UI, 16:9 `MediaElement` video monitor, `ffprobe` inspector, and FFmpeg trim controls

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T026 [P] Register `kinetix-ai` MCP Server in `~/.gemini/config/mcp_config.json`, `.agents/mcp_config.json`, `.agents/skills/kinetix-video-producer/SKILL.md`, `AGENTS.md`, and update launcher scripts (`run_desktop.ps1`, `run_api.ps1`, `README.md`)
- [X] T027 Run full `pytest` suite, rebuild `KinetixAI.Desktop`, and push initial repository to GitHub (`https://github.com/ithieunguyen2911/KinetixAI`)

---

## Phase 7: Deep Feature Audit & End-to-End Remediation (`/speckit-implement` Verification)

- [X] T028 [P] [US1] Promote `extract_metadata` to `IMediaDownloader` (`src/domain/interfaces/media_downloader.py`) and `probe_media`, `trim_video`, `mix_audio_tracks` to `IVideoProcessor` (`src/domain/interfaces/video_processor.py`) so `ProjectService` uses pure Dependency Inversion without `isinstance` checks
- [X] T029 [P] [US1] Harden `FfmpegAdapter.merge_and_export` and `FfmpegAdapter.trim_video` (`src/infrastructure/processors/ffmpeg_adapter.py`) against Windows file locks when a video is open in WPF `MediaElement` by writing to a staging MP4 first and atomically replacing or rolling over the output filename
- [X] T030 [P] [US1] Upgrade `WhisperAdapter.transcribe` (`src/infrastructure/transcribers/whisper_adapter.py`) and `SubtitleSegment` (`src/domain/entities/subtitle_segment.py`) to support real offline Windows Speech Recognition (`System.Speech.Recognition.SpeechRecognitionEngine`) on WAV audio when `script_hint` is empty, and automatically resync `WordTimestamp` items when subtitle text or timing is edited
- [X] T031 [P] [US2] Pass actual probed `duration_seconds` from `AutoVideoPipeline` and `ProjectService` into `render_engines/remotion_engine/render.mjs` and `render_engines/hyperframes_engine/render.mjs` so overlay duration matches trimmed or arbitrary-length source videos
- [X] T032 [US3] Expose `POST /api/v1/sources/inspect` and `POST /api/v1/projects/{project_id}/mix-audio` in `src/application/services/project_service.py`, `src/presentation/schemas/project_schemas.py`, and `src/presentation/api/main.py`
- [X] T033 [P] [US3] Fix `--self-test` CLI flag handling and add `kinetix_inspect_source`, `kinetix_probe_media`, and `kinetix_trim_video` tools in `src/presentation/mcp/mcp_server.py`
- [X] T034 [US3] Fix WPF `DataGrid` cell-edit commit (`GridSubtitles.CommitEdit`), `MediaElement` file handle release before re-render/trim, add **"Inspect"** source metadata button and **"Auto-Whisper (Clear Script)"** button in `desktop_app/KinetixAI.Desktop/MainWindow.xaml` and `MainWindow.xaml.cs`
- [X] T035 Expand unit & integration test suite (`tests/unit/test_adapters.py`, `tests/integration/test_fastapi_endpoints.py`, `tests/integration/test_mcp_server.py`) to verify all 28 features, run `uv run pytest -v`, rebuild `KinetixAI.Desktop`, and push updates to GitHub
