---
description: "Actionable, dependency-ordered task list for KinetixAI (FlowVids-AI) v2.0 Professional NLE Video Editor & Polyglot Studio"
---

# Tasks: KinetixAI (FlowVids-AI) v2.0 — Professional Non-Linear Video Editor (NLE) & Polyglot Studio

**Input**: Design documents from `/specs/001-auto-video-desktop-system/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/api-and-render-contracts.md`, `quickstart.md`)

**Tests**: Automated `pytest` unit and integration tests are MANDATORY per Constitution Principle V.

---

## Phase 1: Setup & Polyglot Infrastructure

- [X] T001 Create Clean Architecture directory hierarchy (`src/domain`, `src/application`, `src/infrastructure`, `src/presentation`, `render_engines/`, `desktop_app/`, `tests/`)
- [X] T002 Initialize Python 3.11+ project (`pyproject.toml`, `uv.lock`) with `fastapi`, `uvicorn`, `pydantic`, `yt-dlp`, `faster-whisper`, `ffmpeg-python`, `mcp`, and `pytest`
- [X] T003 [P] Initialize Node.js visual render engine subprojects (`render_engines/remotion_engine/` and `render_engines/hyperframes_engine/`)

---

## Phase 2: Foundational Domain Layer (Pure Python OOP & ABC Interfaces)

- [X] T004 [P] Implement core Domain Enumerations (`RenderEngineType`, `JobStatus`) in `src/domain/entities/enums.py`
- [X] T005 [P] Implement `WordTimestamp` and `SubtitleSegment` dataclasses with strict validation in `src/domain/entities/subtitle_segment.py`
- [X] T006 [P] Implement `MediaAsset`, `RenderJob`, and `VideoProject` entities in `src/domain/entities/`
- [X] T007 [P] Define `IMediaDownloader` and `ITranscriber` abstract base classes (`ABC`) in `src/domain/interfaces/`
- [X] T008 [P] Define `IVisualRenderer` and `IVideoProcessor` abstract base classes (`ABC`) in `src/domain/interfaces/`
- [X] T009 Write unit tests for all Domain Entities and ABC instantiation guards in `tests/unit/test_domain_entities.py`

---

## Phase 3: User Story 1 — End-to-End Automated Video Production Pipeline (Priority: P1)

- [X] T010 [P] [US1] Implement `YtDlpAdapter(IMediaDownloader)` in `src/infrastructure/downloaders/ytdlp_adapter.py`
- [X] T011 [P] [US1] Implement `FfmpegAdapter(IVideoProcessor)` in `src/infrastructure/processors/ffmpeg_adapter.py` (`extract_audio`, `merge_and_export`)
- [X] T012 [P] [US1] Implement `WhisperAdapter(ITranscriber)` in `src/infrastructure/transcribers/whisper_adapter.py` (`faster-whisper` + `openai-whisper` + Windows Speech STT)
- [X] T013 [US1] Implement `AutoVideoPipeline` in `src/application/pipelines/auto_video_pipeline.py`
- [X] T014 [US1] Write unit tests for `AutoVideoPipeline` orchestration in `tests/unit/test_auto_video_pipeline.py`

---

## Phase 4: User Story 2 — Pluggable Visual Render Engine Switching (`Remotion` vs `HyperFrames`) (Priority: P1)

- [X] T015 [P] [US2] Implement `RemotionAdapter(IVisualRenderer)` in `src/infrastructure/renderers/remotion_adapter.py` and React composition in `render_engines/remotion_engine/`
- [X] T016 [P] [US2] Implement `HyperFramesAdapter(IVisualRenderer)` in `src/infrastructure/renderers/hyperframes_adapter.py` and HTML/CSS/GSAP composition in `render_engines/hyperframes_engine/`
- [X] T017 [US2] Implement `RendererFactory` in `src/application/factories/renderer_factory.py`
- [X] T018 [US2] Write unit tests for `RendererFactory` in `tests/unit/test_renderer_factory.py`
- [X] T019 [US2] Write end-to-end integration test verifying both `Remotion` and `HyperFrames` pipeline execution in `tests/integration/test_end_to_end_pipeline.py`

---

## Phase 5: User Story 3 — Interactive Subtitle Editing, FastAPI Server & MCP Bridge (Priority: P2)

- [X] T020 [P] [US3] Implement `JsonProjectRepository` in `src/infrastructure/repositories/json_project_repository.py`
- [X] T021 [US3] Implement `ProjectService` in `src/application/services/project_service.py`
- [X] T022 [P] [US3] Define Pydantic v2 request/response schemas in `src/presentation/schemas/project_schemas.py`
- [X] T023 [US3] Implement FastAPI REST server in `src/presentation/api/main.py`
- [X] T024 [P] [US3] Implement Antigravity MCP Server (`kinetix-ai`) in `src/presentation/mcp/mcp_server.py`
- [X] T025 [P] [US3] Implement CLI entrypoint in `src/presentation/cli/main.py` and Streamlit Studio UI in `src/presentation/ui/streamlit_app.py`
- [X] T026 [US3] Implement Native Windows C# .NET WPF Desktop Studio in `desktop_app/KinetixAI.Desktop/`
- [X] T027 [US3] Write integration tests for FastAPI and MCP Server in `tests/integration/test_fastapi_endpoints.py` and `tests/integration/test_mcp_server.py`

---

## Phase 6 & 7: Deep Feature Audit & Remediation of All 5 GitHub Tools (Priority: P1)

- [X] T028 Audit and upgrade `YtDlpAdapter` (`extract_metadata`, `download_ranges` clipping, spoken audio synthesis) in `src/infrastructure/downloaders/ytdlp_adapter.py`
- [X] T029 Audit and upgrade `WhisperAdapter` (Windows `System.Speech.Recognition` real STT fallback + `.transcript.json` export) in `src/infrastructure/transcribers/whisper_adapter.py`
- [X] T030 Audit and upgrade `HyperFramesAdapter` (12-rule `window.__timelines` contract + multi-clip `<div data-composition-id>` registry) in `render_engines/hyperframes_engine/render.mjs`
- [X] T031 Audit and upgrade `RemotionAdapter` (real word-level karaoke highlighting + dynamic `calculateMetadata` duration) in `render_engines/remotion_engine/render.mjs`
- [X] T032 Audit and upgrade `FfmpegAdapter` (`probe_media`, `trim_video`, `mix_audio_tracks`, atomic `.staging_` file lock safety) in `src/infrastructure/processors/ffmpeg_adapter.py`
- [X] T033 Expose `/api/v1/sources/inspect`, `/probe`, `/trim`, and `/mix-audio` in `src/presentation/api/main.py` and MCP tools in `src/presentation/mcp/mcp_server.py`
- [X] T034 Bind `Inspect`, `Trim MP4`, `Auto Whisper`, and `ReleaseVideoPlayerLockAsync` in `desktop_app/KinetixAI.Desktop/MainWindow.xaml.cs`
- [X] T035 Verify 5-adapter unit tests in `tests/unit/test_adapters.py`

---

## Phase 8: Domain & Infrastructure NLE Expansion (Color Grading, Speed, Reframe, Silence Cut, Split, Concat, Snapshot)

- [X] T036 [P] [US3] Add `AspectRatioPreset`, `ColorLookPreset`, `TemplatePreset` enums in `src/domain/entities/enums.py` and `ColorGradeSpec` dataclass in `src/domain/entities/nle_specs.py`
- [X] T037 [P] [US3] Declare NLE abstract/default methods (`split_video`, `concat_clips`, `change_speed`, `apply_color_grade`, `reframe_aspect_ratio`, `remove_silences`, `normalize_audio`, `capture_snapshot`) on `IVideoProcessor` in `src/domain/interfaces/video_processor.py`
- [X] T038 [US3] Implement professional NLE video/audio processors (`split_video`, `concat_clips` with `xfade`, `change_speed` with `setpts`+`atempo`, `apply_color_grade` with 5 LUT/Look presets, `reframe_aspect_ratio` for `16:9`/`9:16` blur-pad/`1:1`, `remove_silences`, `normalize_audio`, `capture_snapshot`) in `src/infrastructure/processors/ffmpeg_adapter.py` and add `demo://bgm` synthesized ambient music generator + cinematic dark-slate studio canvas in `src/infrastructure/downloaders/ytdlp_adapter.py`

---

## Phase 9: Multi-Template Motion Graphics Library (Remotion & HyperFrames)

- [X] T039 [P] [US2] Upgrade `render_engines/hyperframes_engine/render.mjs` and `render_engines/remotion_engine/render.mjs` (+ `CaptionTemplate.tsx`) to support 4 selectable Studio Templates (`CaptionTemplate`, `KineticTitleCard`, `SocialPopCaptions`, `TechCalloutHUD`) and custom theme accent colors

---

## Phase 10: Application Service, FastAPI NLE Endpoints & MCP Tools

- [X] T040 [US4] Add NLE use-case methods (`change_project_speed`, `apply_project_color_grade`, `reframe_project_video`, `master_project_audio`, `capture_project_snapshot`, `split_project_video`, `concat_project_clips`, `split_subtitle_cue`, `export_project_subtitles`) in `src/application/services/project_service.py`
- [X] T041 [P] [US4] Add Pydantic v2 schemas (`SpeedChangeRequest`, `ColorGradeRequest`, `ReframeRequest`, `AudioMasterRequest`, `SnapshotRequest`, `SplitVideoRequest`, `ConcatClipsRequest`) in `src/presentation/schemas/project_schemas.py` and expose REST endpoints (`/speed`, `/color-grade`, `/reframe`, `/audio-master`, `/snapshot`, `/split`, `/concat`, `/subtitles/export`) in `src/presentation/api/main.py`
- [X] T042 [P] [US4] Register new NLE MCP tools (`kinetix_apply_color_grade`, `kinetix_change_speed`, `kinetix_reframe_video`, `kinetix_master_audio`, `kinetix_capture_snapshot`) in `src/presentation/mcp/mcp_server.py`

---

## Phase 11: Native Windows C# .NET WPF NLE Workstation v2.0 (Visual Multi-Track Timeline & Post-Production Deck)

- [X] T043 [US5] Upgrade `desktop_app/KinetixAI.Desktop/Models/ApiModels.cs`, `MainWindow.xaml`, and `MainWindow.xaml.cs` with:
  1. **Visual Multi-Track NLE Timeline (`V2 Motion Overlay`, `V1 Video Track`, `S1 Subtitle Cues`, `A1 Audio & Waveform`)** with proportional timeline blocks and click-to-seek playhead
  2. **Program Monitor Transport Deck** with Frame Step (`-1f` / `+1f`), `Set In [` / `Set Out ]` markers, `Split Cue at Playhead`, `Export SRT / VTT`, and `Snapshot PNG`
  3. **Post-Production FX & Color Grading Dock** (4 Template Presets, 5 Color Grade Looks + Brightness/Contrast/Saturation sliders, Speed Ramping `0.5x`–`2.0x`, Aspect Ratio `16:9` / `9:16` / `1:1`, Silence Jump-Cut, Loudness Normalize, BGM Ducking Mix)
- [X] T044 [US5] Write unit and integration tests for all new NLE features (`change_speed`, `apply_color_grade`, `reframe_aspect_ratio`, `remove_silences`, `normalize_audio`, `capture_snapshot`, `split_video`, `concat_clips`, `.srt`/`.vtt`/`.transcript.json` export, 4 Motion Templates, FastAPI NLE endpoints, MCP NLE tools) in `tests/unit/test_domain_entities.py`, `tests/unit/test_adapters.py`, `tests/integration/test_fastapi_endpoints.py`, and `tests/integration/test_mcp_server.py`
- [X] T045 Verify `uv run pytest -v` (100% pass), `dotnet build` (`0 Warning(s), 0 Error(s)`), launch `KinetixAI.Desktop.exe`, and push v2.0 to GitHub

---

## Phase 12: Domain Layer v3.0 — Context Bible, Consistent Characters, Storyboard, Audit Log, Voice/Audio ABCs

- [X] T046 [P] Add `TransitionPreset` and `AnimationPreset` enums in `src/domain/entities/enums.py`, create `SceneContext`, `CharacterProfile`, `StoryScene`, and `AuditLogEntry` dataclasses in `src/domain/entities/studio_entities.py`, and extend `VideoProject` in `src/domain/entities/video_project.py` + `JsonProjectRepository`
- [X] T047 [P] Define `IVoiceSynthesizer` (`src/domain/interfaces/voice_synthesizer.py`) and `IAudioAssetLibrary` (`src/domain/interfaces/audio_library.py`) ABCs and extend `IVideoProcessor` with `apply_transition_and_animation`, `detect_beats_and_cut`, and `insert_sfx_track`

---

## Phase 13: Infrastructure Adapters v3.0 — Voiceover TTS, BGM/SFX Library, Beat-Cut, Transitions & Motion Engines

- [X] T048 [P] Implement `TtsVoiceAdapter(IVoiceSynthesizer)` in `src/infrastructure/tts/tts_voice_adapter.py` supporting `edge-tts` voices (`vi-VN-HoaiMyNeural`, `vi-VN-NamMinhNeural`, `en-US-AriaNeural`, `en-US-GuyNeural`, `en-US-JennyNeural`, `win-sapi-studio`) with offline Windows `System.Speech` + FFmpeg formant fallback
- [X] T049 [P] Implement `StudioAudioLibraryAdapter(IAudioAssetLibrary)` in `src/infrastructure/audio/audio_library_adapter.py` providing 5 deterministic BGM tracks & 6 crisp SFX presets via FFmpeg synthesis
- [X] T050 Implement `apply_transition_and_animation`, `detect_beats_and_cut` (writes `.beats.json`), and `insert_sfx_track` (`adelay`+`amix`) in `src/infrastructure/processors/ffmpeg_adapter.py`, and upgrade `render_engines/remotion_engine/render.mjs` + `render_engines/hyperframes_engine/render.mjs` with Character Consistency HUD + Animation presets

---

## Phase 14: Application & Presentation Layers v3.0 — Full CRUD, Clone, Studio APIs & 22 MCP Tools

- [X] T051 Upgrade `src/application/services/project_service.py` with Project/Scene/Character CRUD + Clone (`clone_project`, `delete_project`, `update_scene_context`, `upsert_scene`, `delete_scene`, `clone_scene`, `upsert_character`, `delete_character`, `clone_character`), `synthesize_project_voiceover`, `apply_project_sfx_or_bgm`, `apply_project_transition_and_animation`, `apply_project_beat_cut`, and automatic structured `AuditLogEntry` tracking
- [X] T052 [P] Add Pydantic v2 schemas in `src/presentation/schemas/project_schemas.py` and expose REST endpoints (`/catalog/studio`, `/clone`, `DELETE /{id}`, `/context`, `/scenes`, `/characters`, `/voiceover`, `/sound-library`, `/fx-motion`, `/beat-cut`) in `src/presentation/api/main.py`
- [X] T053 [P] Register 8 new MCP tools (`kinetix_clone_project`, `kinetix_delete_project`, `kinetix_manage_character`, `kinetix_manage_scene`, `kinetix_generate_voiceover`, `kinetix_apply_sound_library`, `kinetix_apply_beat_cut`, `kinetix_apply_transition_animation` — total 22 tools) in `src/presentation/mcp/mcp_server.py`

---

## Phase 15: Native Windows C# .NET WPF Workstation v3.0 — 5-Tab Studio Dock & Beat-Grid Timeline

- [X] T054 Update `desktop_app/KinetixAI.Desktop/Models/ApiModels.cs` with C# DTOs for Context Bible, Consistent Characters, Storyboard Scenes, Audit Logs, Voiceover, Sound Library, FX Motion, and Beat-Cut
- [X] T055 Upgrade `desktop_app/KinetixAI.Desktop/MainWindow.xaml` and `MainWindow.xaml.cs` with Top FX/Transition/Animation/Clone/Delete bar, Beat Markers track in Multi-Track Timeline, and 5-Tab Studio Dock (1: Subtitles CRUD+Clone, 2: Context & Scenes CRUD+Clone, 3: Consistent Characters CRUD+Clone, 4: Voiceover TTS / BGM / SFX / Beat-Cut Studio, 5: Structured Audit Logs Ledger)

---

## Phase 16: Verification, Legacy SMPTE Purge, Launch & GitHub Push

- [X] T056 Purge legacy SMPTE bar `demo_sample_raw.mp4` caches in `workspace/` and regenerate showcase projects with Dark-Slate Broadcast Canvas + Character HUD + BGM
- [X] T057 Write comprehensive unit & integration tests for all v3.0 features (`tests/unit/test_domain_entities.py`, `tests/unit/test_adapters.py`, `tests/integration/test_fastapi_endpoints.py`, `tests/integration/test_mcp_server.py`)
- [X] T058 Verify `uv run pytest -v` (100% pass), `dotnet build` (`0 Warning(s), 0 Error(s)`), launch via `.\run_desktop.ps1`, confirm process alive, mark all tasks `[X]`, and push to GitHub
