# Phase 0 Research: KinetixAI (FlowVids-AI) Polyglot Architecture

## 1. Python Core Orchestrator vs Single-Language Approach

- **Decision**: Use Python 3.11+ (`FastAPI` + `Pydantic v2` + `uv`) as the Core Backend & Orchestrator.
- **Rationale**: `yt-dlp` and `Whisper` (`faster-whisper` / `openai-whisper`) are native Python ecosystems. Invoking them via Python OOP classes (`YtDlpAdapter`, `WhisperAdapter`) captures millisecond-accurate subtitle segment timestamps (`start_time`, `end_time`, `text`) and download progress callbacks directly without brittle stdout text parsing.
- **Alternatives considered**: Pure C# or pure Node.js orchestrator (rejected because calling Python ML libraries from C#/Node requires extra IPC wrappers and loses native object-level control over `faster-whisper` and `yt-dlp`).

## 2. Dual Visual Render Engines (Remotion vs HyperFrames)

- **Decision**: Support both `Remotion` (React-based component video engine) and `HyperFrames` (HTML/CSS/GSAP deterministic video composition engine) behind `IVisualRenderer` and `RendererFactory`.
- **Rationale**:
  - **HyperFrames** excels when generating dynamic HTML/CSS/GSAP motion graphics and kinetic typography directly from JSON props without heavy React bundling.
  - **Remotion** excels at reusable, strongly-typed React video component libraries (`CaptionTemplate`).
  - Both engines accept `--props <json>` and output an overlay MP4/WebM video file (`[project_id]_overlay.mp4`) that `FfmpegAdapter` composites onto the source video.
- **Alternatives considered**: Hardcoding a single render engine (rejected because the specification requires dynamic factory-based switching between Remotion and HyperFrames).

## 3. High-Performance Overlay Compositing with FFmpeg

- **Decision**: Render subtitle/motion overlays separately and composite them with `FfmpegAdapter.merge_and_export(base_video, overlay_video, output_path)` using FFmpeg filtergraphs (`colorkey`/`chromakey` or alpha overlay + audio passthrough).
- **Rationale**: Decoding large source videos frame-by-frame inside headless Chromium slows rendering dramatically. Rendering lightweight caption overlays in Remotion/HyperFrames and using FFmpeg C/hardware pipelines for audio extraction and video merging achieves 5x-10x faster throughput.
- **Alternatives considered**: Embedding the entire raw video inside Remotion `<OffthreadVideo>` for every job (rejected due to excessive browser memory and decoding overhead).

## 4. Windows Desktop Client Architecture

- **Decision**: Provide a native Windows C# .NET WPF Desktop App (`desktop_app/KinetixAI.Desktop`) that communicates with the Python FastAPI Core over HTTP REST (`http://127.0.0.1:8000`), alongside a Streamlit Web Studio (`src/presentation/ui/streamlit_app.py`) and CLI (`src/presentation/cli/main.py`).
- **Rationale**: Delivers a responsive native Windows Desktop App with dark-mode studio styling, one-click backend auto-start, real-time progress bar polling, engine selector (`Remotion` vs `HyperFrames`), subtitle table inspector, and direct MP4 playback/folder opening.
- **Alternatives considered**: CLI-only interface (rejected because the user requested a full Desktop App).
