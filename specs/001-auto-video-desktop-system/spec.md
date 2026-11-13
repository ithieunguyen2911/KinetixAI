# Feature Specification: KinetixAI (FlowVids-AI) v2.0 — Professional Non-Linear Video Editor (NLE) & Polyglot Automation Studio

**Feature Branch**: `001-auto-video-desktop-system`

**Created**: 2026-11-13 | **Updated**: 2026-11-13 (v2.0 Professional NLE Expansion)

**Status**: Approved

**Input**: User request: `/speckit-plan Lên kế hoạch tạo cho tôi các chức năng của 1 phần mềm chỉnh sửa Video chuyên nghiệp. Nhớ là phải đúng rule mà trước đó tôi đề ra nha.`

---

## 1. Architectural Governance Rules (Mandatory Constraints)

1. **Strict Clean Architecture & Layer Isolation**:
   - `src/domain`: Pure Python 3.11+ entities, value objects, enums, and `abc.ABC` interfaces (`IMediaDownloader`, `ITranscriber`, `IVisualRenderer`, `IVideoProcessor`). Zero third-party imports.
   - `src/application`: Use-case orchestration (`AutoVideoPipeline`, `RendererFactory`, `ProjectService`) communicating strictly via Domain ABCs (Dependency Inversion Principle).
   - `src/infrastructure`: Concrete OOP Adapters wrapping the 5 core GitHub ecosystems (`YtDlpAdapter`, `WhisperAdapter`, `FfmpegAdapter`, `RemotionAdapter`, `HyperFramesAdapter`) + `JsonProjectRepository`.
   - `src/presentation` & `desktop_app/KinetixAI.Desktop`: FastAPI REST Server, MCP Server (`kinetix-ai`), CLI, Streamlit UI, and Native Windows C# .NET WPF NLE Workstation. Zero business/FFmpeg logic inside UI code.
2. **Polyglot Modular Monolith**:
   - Python 3.11+ Core (`yt-dlp` + `faster-whisper`/`openai-whisper` + `FastAPI` + `Pydantic v2`)
   - Node.js 20+ / TypeScript Visual Render Engines (`remotion-dev/remotion` React + `heygen-com/hyperframes` HTML/CSS/GSAP)
   - `FFmpeg` / `ffprobe` Media Processing Engine
   - Native Windows C# .NET WPF Studio Workstation (`KinetixAI.Desktop`)

---

## 2. User Scenarios & Testing *(mandatory)*

### User Story 1 - End-to-End Automated Video Production Pipeline (Priority: P1)

As a video creator or automation operator, I want to provide a source video URL, local video file, or `demo://sample` broadcast source along with a chosen visual render engine (`remotion` or `hyperframes`) and composition template so that the system automatically ingests the media, extracts speech-filtered WAV audio, transcribes word-level subtitles, renders motion graphics overlays, and composites a master MP4.

**Independent Test**: Execute the 5-step pipeline via CLI, API, MCP, or Desktop App and verify `[project_id]_final.mp4`, `.srt`, `.vtt`, and `.transcript.json` are generated.

---

### User Story 2 - Dynamic Visual Render Engine & Multi-Template Motion Library (Priority: P2)

As a motion designer and video editor, I want to switch seamlessly between **Remotion** (React) and **HyperFrames** (HTML/CSS/GSAP) and choose from multiple professional broadcast templates (`CaptionTemplate`, `KineticTitleCard`, `SocialPopCaptions`, `TechCalloutHUD`) with customizable theme accent colors and caption positioning (`bottom`, `center`, `top`).

**Independent Test**: Render each of the 4 templates across both `RenderEngineType.REMOTION` and `RenderEngineType.HYPERFRAMES` via `RendererFactory` and verify valid overlay MP4s and HTML/React manifests.

---

### User Story 3 - Professional Non-Linear Editing (NLE): Trim, Split at Playhead, Speed Ramping, Transitions & Multi-Clip Concat (Priority: P2)

As a professional video editor, I want to perform non-linear editing operations on my video project—including **Trim (In/Out)**, **Razor Split at Playhead**, **Playback Speed Ramping (`0.5x` slow-motion to `2.0x` fast-forward)**, **Silence Jump-Cut Removal**, and **Multi-Clip Concatenation with Crossfade/Wipe Transitions**—all processed deterministically via `FfmpegAdapter` behind `IVideoProcessor`.

**Independent Test**: Invoke speed change (`1.5x`), silence removal, split/trim, and transition concatenation via `FfmpegAdapter` and FastAPI endpoints, verifying output duration and stream integrity with `ffprobe`.

---

### User Story 4 - Color Grading, LUT Presets, Smart Aspect Ratio Reframing & Audio Mastering (Priority: P3)

As a post-production colorist and sound editor, I want to apply **Color Grading** (Brightness, Contrast, Saturation, Gamma, and one-click presets: `Natural Rec.709`, `Teal & Orange`, `Warm Vintage`, `Monochrome Noir`, `Studio Crisp`), **Smart Aspect Ratio Reframing** (`16:9` Landscape, `9:16` Vertical Shorts/Reels with blurred background pillarbox, `1:1` Square), **EBU R128 Audio Normalization**, and **Background Music Mixing with Ducking**.

**Independent Test**: Apply a color grade preset + `9:16` vertical reframe + audio normalization/BGM mix via API and verify output resolution (`720x1280` for `9:16`) and audio stream properties via `ffprobe`.

---

### User Story 5 - Native Windows C# WPF NLE Workstation with Visual Multi-Track Timeline (Priority: P3)

As a desktop video editor on Windows, I want a studio-grade NLE interface (`KinetixAI.Desktop`) featuring a **Left Media & Effects Dock** (Project Bin, Motion Templates, Color Grading & FX), a **Center Program Monitor** (with Frame Step `-1f`/`+1f`, Set In `[` / Set Out `]`, Razor Split, Snapshot PNG, and Scrub Bar), a **Right Inspector & Subtitle Cue Dock**, and a **Bottom Visual Multi-Track Timeline (`V2 Overlay`, `V1 Video`, `S1 Subtitles`, `A1 Audio`)** synchronized in real time with the Python Core API and Antigravity MCP (`kinetix-ai`).

**Independent Test**: Build and launch `KinetixAI.Desktop.exe`, verify 0 warnings/errors, load a project, inspect visual timeline blocks on tracks `V2`/`V1`/`S1`/`A1`, trigger NLE actions (Color Grade, Speed, Reframe, Snapshot, Trim, Re-Render), and verify real-time preview playback.

---

## 3. Functional Requirements *(mandatory)*

- **FR-001 (Domain Layer)**: Define pure domain entities (`VideoProject`, `SubtitleSegment`, `WordTimestamp`, `MediaAsset`, `RenderJob`, `ColorGradeSpec`, `NleEditSpec`) and enums (`RenderEngineType`, `JobStatus`, `AspectRatioPreset`, `ColorLookPreset`, `TransitionStyle`, `TemplatePreset`) with zero external dependencies.
- **FR-002 (Domain Interfaces - DIP)**: Define all media operations on `IMediaDownloader`, `ITranscriber`, `IVisualRenderer`, and `IVideoProcessor` using Python `abc.ABC`.
- **FR-003 (`YtDlpAdapter`)**: Support URL video/audio downloading (`format_selector`), `extract_metadata` pre-inspection, `download_ranges` clipping, local file ingestion, synthesized spoken-voice broadcast sample (`demo://sample`), and synthesized ambient background music track (`demo://bgm`).
- **FR-004 (`FfmpegAdapter` Core & NLE)**: Support `probe_media` (`ffprobe`), `extract_audio` (`16kHz` mono speech bandpass), `trim_video`, `split_video`, `concat_clips` (with `xfade`/`acrossfade`), `change_speed` (`0.25x`–`4.0x` via `setpts` & `atempo`), `apply_color_grade` (`eq` brightness/contrast/saturation/gamma + look presets), `reframe_aspect_ratio` (`16:9`, `9:16` blur-pad, `1:1`), `remove_silences` (`silenceremove`), `normalize_audio` (`loudnorm`), `mix_audio_tracks`, `capture_snapshot` (PNG frame grab), and `merge_and_export` (with `.srt` + `.vtt` export and Windows file-lock safe staging).
- **FR-005 (`WhisperAdapter`)**: Support `faster-whisper` (with VAD & word timestamps), `openai-whisper`, Windows native `SpeechRecognitionEngine` offline STT, script alignment, subtitle timing shift/split, and `.transcript.json` export.
- **FR-006 (`RemotionAdapter` & `HyperFramesAdapter`)**: Support 4 templates (`CaptionTemplate`, `KineticTitleCard`, `SocialPopCaptions`, `TechCalloutHUD`), theme color/position customization, and `RendererFactory`.
- **FR-007 (FastAPI & MCP Server)**: Expose REST endpoints and MCP tools (`kinetix-ai`) for all NLE operations (`/inspect`, `/probe`, `/trim`, `/speed`, `/color-grade`, `/reframe`, `/remove-silence`, `/normalize-audio`, `/mix-audio`, `/snapshot`, `/subtitles`).
- **FR-008 (Windows WPF NLE Desktop App)**: Provide a 4-zone NLE workstation with Visual Multi-Track Timeline Canvas, Frame Stepping, Snapshot Capture, Color/Speed/Aspect Ratio Studio Controls, Subtitle Cue Editor, and MCP Live Sync.

---

## 4. Success Criteria *(mandatory)*

- **SC-001**: All 5 tools (`yt-dlp`, `Whisper`, `HyperFrames`, `Remotion`, `FFmpeg`) are encapsulated strictly inside `src/infrastructure/` adapters implementing `src/domain/interfaces/` ABCs with zero layer violations.
- **SC-002**: Users can execute both automated 5-step video production and interactive NLE post-production (Color Grading, Speed Ramping, `9:16` Vertical Reframe, Silence Removal, Audio Mixing, Frame Snapshot, Subtitle Editing) from the Desktop App, REST API, CLI, or Antigravity MCP.
- **SC-003**: 100% of unit and integration tests pass under `uv run pytest -v` and `dotnet build` compiles `KinetixAI.Desktop` with `0 Warning(s), 0 Error(s)`.
