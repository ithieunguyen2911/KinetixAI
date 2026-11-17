# Feature Specification: KinetixAI (FlowVids-AI) v5.0 — End-to-End Verified NLE Workstation, Structured Podcast Production Engine & VoiceStudio AI

**Feature Branch**: `001-auto-video-desktop-system` | **Created**: 2026-11-13 | **Updated**: 2026-11-18 (v5.0 Production Verification & Real Podcast Studio) | **Status**: Approved

## 1. Architectural Governance Rules (Mandatory Constraints)
1. **Strict Clean Architecture & SOLID (`domain` -> `application` -> `infrastructure` -> `presentation`)** per `.specify/memory/constitution.md`.
2. **Dependency Inversion Principle (DIP)**: All Media Downloading (`IMediaDownloader`), Transcription (`ITranscriber`), Visual Rendering (`IVisualRenderer`), Video/Audio Processing (`IVideoProcessor`), Voice Synthesis/Cloning/Design (`IVoiceSynthesizer`), and Sound Library (`IAudioAssetLibrary`) capabilities MUST reside behind `abc.ABC` interfaces in `src/domain/interfaces/`.
3. **Zero-Shell / 100% Grounded Execution**: Every feature in the API, MCP Server (`27 tools`), and C# WPF Desktop App (`KinetixAI.Desktop`) MUST produce verifiable media output (`ffprobe`-validated MP4/WAV, frame-verified UTF-8 subtitles, reactive waveform visuals, and resilient startup).

---

## 2. User Stories & Functional Requirements

### US1–US5 — Core 5-Step Polyglot Pipeline & NLE Post-Production (Priority: P1)
- **FR-001**: Ingest remote URLs, local video files, or studio canvas (`YtDlpAdapter`), extract 16kHz mono speech WAV (`FfmpegAdapter`), transcribe or align scripts (`WhisperAdapter`), render motion overlays (`RemotionAdapter` / `HyperFramesAdapter`), and composite final H.264/AAC MP4 + `.srt`/`.vtt`.
- **FR-002**: Support NLE Trim, Split, Concat, Speed Ramp (`0.25x–4.0x`), 5 Color Grading LUT/Look presets, Aspect Reframe (`16:9`, `9:16`, `1:1`), Silence Removal, EBU R128 Loudness Normalization (`-16 LUFS`), and PNG Frame Snapshot.

### US6–US9 — Context Bible, Consistent Characters, Sound Library, Beat-Cut & Full CRUD (Priority: P1)
- **FR-003**: Manage global `SceneContext`, `StoryScene` storyboard items, and `CharacterProfile` identities (`Add`, `Edit`, `Clone`, `Delete`) with live overlay synchronization and structured `AuditLogEntry` history.
- **FR-004**: Provide curated & procedural BGM beds (`bgm_piano_melancholic`, `bgm_inspiring_acoustic`, `bgm_ambient_pad`, `bgm_lofi_chill`, `bgm_cyber_pulse`, `bgm_news_broadcast`, `bgm_dramatic_rise`) and diegetic/UI SFX (`sfx_fan_shutdown`, `sfx_phone_vibrate`, `sfx_whoosh_fast`, `sfx_pop_bubble`, `sfx_glitch_digital`, `sfx_cinematic_hit`, `sfx_camera_shutter`, `sfx_chime_ding`).

### US10 — Interactive Multi-Track Timeline CRUD & VoiceStudio AI (`debpalash/VoiceStudio` Architecture) (Priority: P1)
- **FR-005**: Interactive 5-Track Timeline (`V2`, `V1`, `S1`, `A1`, `B1`) supporting inline `Add`, `Edit`, `Split at Playhead`, `Clone`, `Delete`, and `Render Timeline` synchronized with `SubtitleSegment` cues.
- **FR-006**: Support Seeded Voice Design (`design_voice`), Consent-Gated Voice Cloning (`clone_voice` requiring `consent_verified=True`), Expressive Tags (`[pause 600ms]`, `[emotion:late_night]`), and Time-Aligned Video Dubbing (`dub_project_video`).

### US11 — Broadcast-Grade Structured Podcast Video Production (`TẬP 1: TUỔI 30...`) & Desktop Startup Resilience (Priority: P1)
- **FR-007 (Structured Script & Stage-Direction Parser)**: Automatically parse full-length podcast scripts containing Episode Titles (`TẬP 1: ...`), Timestamped Chapter Headers (`0:00 – 0:20 | HOOK: ...`), Bracketed Stage/SFX/BGM Cues (`[Âm thanh: ...]`, `[Nhạc nền ...]`), and Production Recording Notes (`GỢI Ý THU ÂM...`):
  - **NEVER** read timestamps, chapter prefixes, bracketed stage cues, or recording notes aloud via TTS.
  - Extract chapters into `PodcastChapter` / `StoryScene` timeline markers, map bracketed cues to real SFX (`sfx_fan_shutdown`, `sfx_phone_vibrate`) and multi-stage BGM transitions (`bgm_piano_melancholic` -> `bgm_inspiring_acoustic`), and chunk long paragraphs into natural 12–24 word caption phrases with psychological pauses on Hook anchor phrases (`"30 tuổi"`, `"tắt ngấm"`, `"con số âm"`).
- **FR-008 (Broadcast Podcast Visualizer & Multi-Line UTF-8 Subtitles)**: Render full-length 1280x720@30fps Podcast MP4s featuring:
  - Real-time audio-reactive waveform visualizer (`showwaves`) driven by the spoken Vietnamese neural voiceover (`vi-VN-NamMinhNeural` / `vi-VN-HoaiMyNeural`),
  - Episode Header Banner, Dynamic Chapter Title Badge, Progress Bar, and 2-stage mood color shift (melancholic indigo -> hopeful warm amber at turnaround chapter),
  - Multi-line auto-wrapped UTF-8 `.ass` Vietnamese subtitles guaranteed never to clip horizontally off-screen.
- **FR-009 (Resilient Desktop Launch & Repository Isolation)**: `JsonProjectRepository` MUST isolate deserialization errors per project item so a single corrupt entry never blanks `PROJECTS BIN`. Both `run_desktop.ps1` and `MainWindow.xaml.cs` MUST launch `.venv\Scripts\python.exe -m uvicorn` directly and health-check `/api/v1/health` so `PROJECTS BIN` and `Program Monitor` populate reliably on every launch.

---

## 3. Measurable Success Criteria
- **SC-001**: `uv run pytest -v` passes 100% of unit and integration tests (including structured script parser, stage-cue stripping, `.ass` subtitle wrapping, and repository fault isolation).
- **SC-002**: `dotnet build desktop_app/KinetixAI.Desktop/KinetixAI.Desktop.csproj` succeeds with `0 Error(s)` and `0 Warning(s)`.
- **SC-003**: Demo podcast video `tap_01_tuoi_30_podcast` renders end-to-end with real `vi-VN-NamMinhNeural` Vietnamese voiceover (`duration >= 180s`), audible intro SFX (`sfx_fan_shutdown` + `sfx_phone_vibrate`), 2-stage BGM transition (`bgm_piano_melancholic` -> `bgm_inspiring_acoustic`), live audio waveform, wrapped Vietnamese captions (verified via extracted PNG frames), and zero spoken stage directions.
- **SC-004**: Launching `.\run_desktop.ps1` brings FastAPI (`127.0.0.1:8000`) online first and opens `KinetixAI.Desktop` with `PROJECTS BIN` populated and `tap_01_tuoi_30_podcast` ready to play in `Program Monitor`.
