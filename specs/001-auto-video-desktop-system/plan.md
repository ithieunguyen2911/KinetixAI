# Implementation Plan: KinetixAI (FlowVids-AI) v5.0 — End-to-End Verified NLE Workstation & Broadcast Podcast Production Engine

**Branch**: `001-auto-video-desktop-system` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md) | **Analysis**: [analysis-v5.md](analysis-v5.md)

## 1. Technical Context & Root-Cause Remediation Architecture
- **Core Runtime**: Python 3.11+ (`uv`, FastAPI, Pydantic v2, `edge-tts==7.3.1`, `faster-whisper`, `yt-dlp`, `FFmpeg`/`ffprobe`).
- **Visual Render Engines**: `render_engines/remotion_engine` & `render_engines/hyperframes_engine` (Node.js 20+ + UTF-8 `.ass` multi-line wrapped caption compositing) + `FfmpegAdapter.render_podcast_video` (real-time `showwaves` audio-reactive broadcast visualizer).
- **Desktop Workstation**: C# .NET 10 WPF (`desktop_app/KinetixAI.Desktop`) communicating strictly over HTTP/JSON with `http://127.0.0.1:8000`.

### Key Architectural Upgrades in v5.0
1. **Domain Structured Podcast Parser (`src/domain/services/podcast_script_parser.py`)**:
   - Pure Python domain parser (zero external dependencies, 100% Clean Architecture compliant) transforming raw Vietnamese/English scripts with timestamps (`0:00 – 0:20 | HOOK:...`), stage cues (`[Âm thanh: ...]`, `[Nhạc nền ...]`), and production notes (`GỢI Ý THU ÂM...`) into structured `ParsedPodcastScript` (`episode_title`, `chapters`, `turns`, `sfx_cues`, `bgm_segments`, `recommended_voice_id`, `recommended_rate`).
2. **Resilient Neural TTS & Acoustic Piano/SFX Synthesis (`src/infrastructure/tts/tts_voice_adapter.py`, `src/infrastructure/audio/audio_library_adapter.py`)**:
   - `TtsVoiceAdapter`: 45s timeout + retry logic for `edge-tts`, parallel/batched turn synthesis for multi-minute podcasts, psychological Hook pause injection (`[pause 650ms]`), warm late-night baritone EQ (`vi-VN-NamMinhNeural`), and explicit diagnostics.
   - `StudioAudioLibraryAdapter`: Multi-chord struck-piano `bgm_piano_melancholic` (`Am–F–Dm–E7`), uplifting `bgm_inspiring_acoustic` (`C–G–Am–F`), plus diegetic `sfx_fan_shutdown` (cooling fan spin-down) and `sfx_phone_vibrate` (dual-pulse buzz).
3. **Broadcast Podcast Compositor & Wrapped `.ass` Subtitles (`src/infrastructure/processors/ffmpeg_adapter.py`, `render_engines/*/render.mjs`)**:
   - Auto-wrapped `.ass` subtitle generation (`PlayResX: 1280, PlayResY: 720`, `MarginL/R: 90`, `Segoe UI` bold with translucent dark backplate) eliminating horizontal clipping and `colorkey` jaggedness.
   - `FfmpegAdapter.render_podcast_video`: Composites 2-stage mood background, Episode/Chapter HUD cards, progress bar, live `showwaves` voice waveform, `.ass` wrapped Vietnamese subtitles, intro diegetic SFX, and 2-stage crossfaded BGM ducked cleanly beneath normalized speech.
4. **Desktop Startup & State Sync Hardening (`MainWindow.xaml.cs`, `MainWindow.xaml`, `run_desktop.ps1`, `json_project_repository.py`)**:
   - Direct `.venv\Scripts\python.exe -m uvicorn` auto-launch + pre-flight health check in `run_desktop.ps1`.
   - Per-project error isolation in `JsonProjectRepository._load()`.
   - Context/Scene/Character save operations synchronize overlay metadata, and Tab 5 includes 1-click preset loading for full structured podcast scripts.

## 2. Constitution Check (`.specify/memory/constitution.md`)
- **I. Clean Architecture & Layer Isolation**: **PASS** — `podcast_script_parser.py` is pure Python in `src/domain/`; `IVideoProcessor.render_podcast_video` is declared as an abstract/default contract in `src/domain/interfaces/video_processor.py`; all `ffmpeg`/`edge_tts`/`subprocess` calls remain strictly inside `src/infrastructure/`.
- **II. SOLID & Dependency Inversion**: **PASS** — `ProjectService` orchestrates `PodcastScriptParser`, `IVoiceSynthesizer`, `IAudioAssetLibrary`, and `IVideoProcessor` purely through abstractions.
- **III. Adapter Pattern**: **PASS** — All external media tools encapsulated in `src/infrastructure/`.
- **IV. Strict Type Hinting & Data Contracts**: **PASS** — Full Python 3.11+ type annotations, dataclasses, Pydantic v2 schemas, and C# DTOs.
- **V. Test-Driven Quality & Pytest Coverage**: **PASS** — Unit + integration tests verify every new parser rule, audio cue, subtitle wrapper, API endpoint, and real podcast video export.
