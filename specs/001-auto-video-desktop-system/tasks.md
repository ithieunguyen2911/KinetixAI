---
description: "Actionable, dependency-ordered task list for KinetixAI (FlowVids-AI) v2.0 Professional NLE Video Editor & Polyglot Studio"
---

# Tasks: KinetixAI (FlowVids-AI) v2.0 — Professional Non-Linear Video Editor (NLE) & Polyglot Studio

**Input**: Design documents from `/specs/001-auto-video-desktop-system/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/api-and-render-contracts.md`, `quickstart.md`)

**Tests**: Automated `pytest` unit and integration tests are MANDATORY per Constitution Principle V.

---

## Phase 1–7: Core Polyglot Pipeline, 5 Adapters, MCP Server & Base Studio UI (Completed)

- [X] T001–T003 Setup Clean Architecture hierarchy, Python `uv` environment, and Node.js Remotion/HyperFrames engines
- [X] T004–T009 Implement foundational Domain Entities (`VideoProject`, `SubtitleSegment`, `WordTimestamp`, `MediaAsset`, `RenderJob`) and ABC Interfaces (`IMediaDownloader`, `ITranscriber`, `IVisualRenderer`, `IVideoProcessor`)
- [X] T010–T014 Implement `YtDlpAdapter`, `FfmpegAdapter`, `WhisperAdapter`, and `AutoVideoPipeline`
- [X] T015–T019 Implement `RemotionAdapter`, `HyperFramesAdapter`, and `RendererFactory`
- [X] T020–T027 Implement FastAPI Server, MCP Server (`kinetix-ai`), CLI, and C# WPF Studio UI
- [X] T028–T035 Complete Deep Feature Audit (Windows Speech STT, file-lock staging, `/sources/inspect`, `/trim`, `/probe`, `/mix-audio`)

---

## Phase 8: Domain & Infrastructure NLE Expansion (Color Grading, Speed, Reframe, Silence Cut, Split, Concat, Snapshot)

- [X] T036 [P] [US3] Add `AspectRatioPreset`, `ColorLookPreset`, `TemplatePreset` enums in `src/domain/entities/enums.py` and `ColorGradeSpec` dataclass in `src/domain/entities/nle_specs.py`
- [X] T037 [P] [US3] Declare NLE abstract/default methods (`split_video`, `concat_clips`, `change_speed`, `apply_color_grade`, `reframe_aspect_ratio`, `remove_silences`, `normalize_audio`, `capture_snapshot`) on `IVideoProcessor` in `src/domain/interfaces/video_processor.py`
- [X] T038 [US3] Implement professional NLE video/audio processors (`split_video`, `concat_clips` with `xfade`, `change_speed` with `setpts`+`atempo`, `apply_color_grade` with 5 LUT/Look presets, `reframe_aspect_ratio` for `16:9`/`9:16` blur-pad/`1:1`, `remove_silences`, `normalize_audio`, `capture_snapshot`) in `src/infrastructure/processors/ffmpeg_adapter.py` and add `demo://bgm` synthesized ambient music generator + cinematic studio canvas in `src/infrastructure/downloaders/ytdlp_adapter.py`

---

## Phase 9: Multi-Template Motion Graphics Library (Remotion & HyperFrames)

- [X] T039 [P] [US2] Upgrade `render_engines/hyperframes_engine/render.mjs` and `render_engines/remotion_engine/render.mjs` (+ `CaptionTemplate.tsx`) to support 4 selectable Studio Templates (`CaptionTemplate`, `KineticTitleCard`, `SocialPopCaptions`, `TechCalloutHUD`) and custom theme accent colors

---

## Phase 10: Application Service, FastAPI NLE Endpoints & MCP Tools

- [X] T040 [US4] Add NLE use-case methods (`change_project_speed`, `apply_project_color_grade`, `reframe_project_video`, `master_project_audio`, `capture_project_snapshot`, `split_subtitle_cue`) in `src/application/services/project_service.py`
- [X] T041 [P] [US4] Add Pydantic v2 schemas (`SpeedChangeRequest`, `ColorGradeRequest`, `ReframeRequest`, `AudioMasterRequest`, `SnapshotRequest`) in `src/presentation/schemas/project_schemas.py` and expose REST endpoints (`/speed`, `/color-grade`, `/reframe`, `/audio-master`, `/snapshot`) in `src/presentation/api/main.py`
- [X] T042 [P] [US4] Register new NLE MCP tools (`kinetix_apply_color_grade`, `kinetix_change_speed`, `kinetix_reframe_video`, `kinetix_master_audio`, `kinetix_capture_snapshot`) in `src/presentation/mcp/mcp_server.py`

---

## Phase 11: Native Windows C# .NET WPF NLE Workstation v2.0 (Visual Multi-Track Timeline & Post-Production Deck)

- [X] T043 [US5] Upgrade `desktop_app/KinetixAI.Desktop/Models/ApiModels.cs`, `MainWindow.xaml`, and `MainWindow.xaml.cs` with:
  1. **Visual Multi-Track NLE Timeline (`V2 Motion Overlay`, `V1 Video Track`, `S1 Subtitle Cues`, `A1 Audio & Waveform`)** with proportional timeline blocks and click-to-seek playhead
  2. **Program Monitor Transport Deck** with Frame Step (`-1f` / `+1f`), `Set In [` / `Set Out ]` markers, `Split Cue at Playhead`, and `Snapshot PNG`
  3. **Post-Production FX & Color Grading Dock** (4 Template Presets, 5 Color Grade Looks + Brightness/Contrast/Saturation sliders, Speed Ramping `0.5x`–`2.0x`, Aspect Ratio `16:9` / `9:16` / `1:1`, Silence Jump-Cut, Loudness Normalize, BGM Ducking Mix)
- [X] T044 [US5] Write unit and integration tests for all new NLE features (`change_speed`, `apply_color_grade`, `reframe_aspect_ratio`, `remove_silences`, `normalize_audio`, `capture_snapshot`, 4 Motion Templates, FastAPI NLE endpoints, MCP NLE tools) in `tests/unit/test_adapters.py`, `tests/integration/test_fastapi_endpoints.py`, and `tests/integration/test_mcp_server.py`
- [X] T045 Verify `uv run pytest -v` (100% pass), `dotnet build` (`0 Warning(s), 0 Error(s)`), launch `KinetixAI.Desktop.exe`, and push v2.0 to GitHub
