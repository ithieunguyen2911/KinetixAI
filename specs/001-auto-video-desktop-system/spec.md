# Feature Specification: KinetixAI (FlowVids-AI) v6.0 — Soulful Prosody, On-Device VieNeu/Cloud Expressive TTS, AI Storyboard B-Roll Illustrations & Sidechain Piano Studio

**Feature Branch**: `001-auto-video-desktop-system` | **Created**: 2026-11-13 | **Updated**: 2026-11-18 (v6.0 Soulful Voice & Visual Storyboard Upgrade) | **Status**: Approved

## 1. Architectural Governance Rules (Mandatory Constraints)
1. **Strict Clean Architecture & SOLID (`domain` -> `application` -> `infrastructure` -> `presentation`)** per `.specify/memory/constitution.md`.
2. **Dependency Inversion Principle (DIP)**: All Media Downloading (`IMediaDownloader`), Transcription (`ITranscriber`), Visual Rendering (`IVisualRenderer`), Video/Audio Processing (`IVideoProcessor`), Voice Synthesis/Cloning/Design (`IVoiceSynthesizer`), Sound Library (`IAudioAssetLibrary`), and Storyboard Illustration Generation (`IVisualAssetGenerator`) MUST reside behind `abc.ABC` interfaces in `src/domain/interfaces/`.
3. **Zero-Shell / 100% Grounded Execution**: Every feature in the API, MCP Server, and C# WPF Desktop App (`KinetixAI.Desktop`) MUST produce verifiable, emotionally engaging media output.

---

## 2. User Stories & Functional Requirements

### US1–US10 — Core Pipeline, NLE Post-Production, Context/Characters, Timeline CRUD & VoiceStudio Foundation (Priority: P1)
- **FR-001..FR-006**: 5-Step Polyglot Pipeline, NLE Trim/Split/Concat/Speed/Color/Reframe/Loudnorm, Storyboard & Character CRUD, Curated BGM/SFX, 5-Track Interactive Timeline CRUD, and Consent-Gated VoiceStudio profiles.

### US11 — Structured Podcast Production & Desktop Startup Resilience (Priority: P1)
- **FR-007..FR-009**: Structured script parsing (never reading stage cues/timestamps/notes aloud), UTF-8 `.ass` wrapped captions, and resilient `.venv` FastAPI auto-start + `mtime_ns` hot-reload.

### US12 — Soulful Continuous Prosody, Dynamic Rhythm & Multi-Engine Expressive/Cloned TTS (Phương án 1 + Phương án 2) (Priority: P1)
- **FR-010 (Paragraph-Flow Prosody & Exact Boundary Sync — Phương án 1)**:
  - `PodcastScriptParser` MUST group narrative text into coherent **Emotional Paragraph Beats** (`35–85 words` per beat) instead of micro-chopping into 12-word fragments, preserving natural human sentence-to-sentence intonation and breath continuity.
  - Each beat MUST carry a dynamic emotional contour (`hook_dramatic`, `melancholic_narrative`, `urgent_collapse`, `introspective_analysis`, `hopeful_turnaround`, `warm_outro`) modulating speaking rate, pitch warmth, audible `[breath]`/`[sigh]` micro-cues, and inter-paragraph emotional pauses (`750ms–1100ms`).
  - `TtsVoiceAdapter` MUST extract exact `SentenceBoundary` / `faster-whisper` timestamps from continuous paragraph audio to slice 1–2 line `.ass` subtitle cues WITHOUT slicing the spoken audio stream.
- **FR-011 (Multi-Provider Expressive & On-Device Cloned TTS — Phương án 2)**:
  - `TtsVoiceAdapter` MUST support pluggable expressive TTS backends:
    1. **On-Device `VieNeu-TTS` (`vieneu` ONNX Vietnamese Neural TTS & Zero-Shot 3–5s Reference Voice Cloning)** and real `numpy` $F_0$/spectral reference voice profiling,
    2. **Enhanced Continuous `Edge-TTS` Prosody Streaming** (`vi-VN-NamMinhNeural` / `vi-VN-HoaiMyNeural` with paragraph-level SSML/prosody & `SentenceBoundary` sync),
    3. **Cloud Acting Engines (`Gemini Native Audio TTS` via `GEMINI_API_KEY` with directorial acting instructions, and `ElevenLabs Multilingual v2` via `ELEVENLABS_API_KEY`)** configurable via `/api/v1/voices/providers` and the WPF Desktop UI.

### US13 — AI Storyboard Illustrations, Ken Burns B-Roll & Sidechain Reverb Piano Mixing (Priority: P1)
- **FR-012 (AI Storyboard Illustrations & Ken Burns B-Roll)**:
  - Extend `StoryScene` with `image_path` and `visual_prompt`, and introduce `IVisualAssetGenerator` (`src/domain/interfaces/visual_generator.py`) implemented by `StoryboardVisualAdapter` (`src/infrastructure/visuals/storyboard_visual_adapter.py`).
  - Automatically resolve or generate cohesive **16:9 Cinematic Storyboard Illustrations** for every chapter/sub-scene of a podcast (8 scenes for Episode 1), supporting pre-rendered AI art, Gemini Imagen / Pollinations AI generation, and rich Pillow cinematic atmosphere fallback, plus user-selected custom scene images in WPF Tab 2.
  - `FfmpegAdapter.render_podcast_video` MUST animate scene illustrations with **smooth alternating Ken Burns `zoompan` camera motion**, **`xfade` cross-dissolves**, cinematic vignette, sleek non-intrusive bottom waveform bar, and smooth fade-in `.ass` subtitles (`\fad(180,140)`).
- **FR-013 (Felt-Piano Reverb & Dynamic Sidechain Audio Ducking)**:
  - Upgrade `bgm_piano_melancholic` and `bgm_inspiring_acoustic` with multi-harmonic felt-piano overtones and concert-hall sustain reverb (`aecho`), and mix BGM via FFmpeg **`sidechaincompress` (Auto-Ducking)** triggered by the vocal track so the music ducks cleanly during speech and swells organically during emotional pauses.

### US14 — Integrated Cinema Full-Screen Video Preview & Transport Controls (`v6.1`) (Priority: P1)
- **FR-014 (Integrated Cinema FullScreen Player Window & Synchronized Playback)**:
  - The C# WPF Desktop App (`desktop_app/KinetixAI.Desktop`) MUST provide a dedicated borderless, maximized **Cinema FullScreen Player** (`FullScreenPlayerWindow.xaml`) with pitch-black backdrop (`#000000`) and high-fidelity video rendering (`Stretch="Uniform"`).
  - **Floating Auto-Hiding Cinema HUD**:
    - A sleek glass-morphism HUD docked at the bottom of the screen with Play/Pause, Replay 5s, Forward 5s, Full-width Scrubber Slider, Real-time Timecode (`mm:ss.ff / mm:ss.ff`), Volume Slider + Mute Toggle, Video Metadata Badge (`1280x720 • 30fps`), and "Thu Nhỏ / Thoát [Esc]" button.
    - An automatic mouse-idle detection timer (`DispatcherTimer`, 2.5s) fades the HUD smoothly to `Opacity=0` during undisturbed playback. Any mouse movement immediately restores the HUD.
  - **Bidirectional Playback Synchronization**:
    - Entering FullScreen inherits the current video path, playback position (`Position`), and playing state from `MainWindow.VideoPlayer`.
    - Exiting FullScreen (via `Esc`, double-click, or Close button) seamlessly updates `MainWindow.VideoPlayer.Position` and timeline scrubber slider so editing resumes without losing position.
  - **Multi-Modal Triggers**:
    1. Dedicated **"Toàn Màn Hình" (Full Screen [F11])** button with icon `⛶` located in the Program Monitor Transport Deck.
    2. Double-clicking anywhere on the Program Monitor video canvas toggles FullScreen.
    3. Global keyboard shortcuts: `F11` or `F` toggles FullScreen; `Space` toggles Play/Pause; `Esc` exits FullScreen; `Left Arrow` / `Right Arrow` jumps -5s / +5s.

---

## 3. Measurable Success Criteria
- **SC-001**: `uv run pytest -v` passes 100% of unit & integration tests (including v6.0 paragraph prosody, multi-provider TTS, `StoryboardVisualAdapter`, Ken Burns B-Roll, and sidechain ducking).
- **SC-002**: `dotnet build desktop_app/KinetixAI.Desktop/KinetixAI.Desktop.csproj` succeeds with `0 Error(s)` and `0 Warning(s)`.
- **SC-003**: Regenerated `tap_01_tuoi_30_podcast` features **8 distinct cinematic 16:9 storyboard illustrations** with Ken Burns motion & `xfade` transitions (verified via frame snapshots across chapters), unbroken paragraph-flow voiceover with natural rhythm, and audible sidechain piano swells during pauses.
- **SC-004**: Clicking **"Toàn Màn Hình"** or pressing `F11` in `KinetixAI.Desktop` opens the maximized Cinema FullScreen Player with auto-hiding HUD, synchronized timecode, keyboard navigation (`Space`, `Esc`, `Left`, `Right`), and smooth return to the NLE editing workspace upon exit.
