# Implementation Plan: KinetixAI (FlowVids-AI) v6.1 — Soulful Prosody, AI Storyboard B-Roll, Sidechain Audio & Integrated Cinema FullScreen Player

**Branch**: `001-auto-video-desktop-system` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

## 1. Technical Context & v6.1 Architectural Upgrades
- **Hardware Profile**: Windows 11 AMD64, NVIDIA GeForce RTX 3050 6GB Laptop GPU, 11.7GB RAM, Python 3.11.15 (`uv`), .NET 10 WPF, FFmpeg.
- **Root-Cause Solutions Implemented in v6.0**:
  1. **Continuous Paragraph Prosody + `SentenceBoundary` / Whisper Word Sync (`PodcastScriptParser` + `TtsVoiceAdapter`)**:
     - Eliminates the 70-fragment robotic choppy cadence by synthesizing **12–16 full Emotional Paragraph Beats** continuously while extracting exact `SentenceBoundary` timestamps (`offset / 10_000_000`) or `faster-whisper` word timestamps to generate crisp 1–2 line `.ass` subtitles with `\fad(180,140)` and keyword emphasis!
     - Dynamic emotional pacing contours (`hook_dramatic`, `melancholic_narrative`, `urgent_collapse`, `introspective_analysis`, `hopeful_turnaround`, `warm_outro`) + subtle synthesized `[breath]` / `[sigh]` cues.
  2. **Multi-Backend Expressive & Zero-Shot Voice Cloning (`VieNeu-TTS` Local ONNX + `Gemini Acting TTS` + `ElevenLabs` + Real $F_0$ Acoustic Cloning)**:
     - Integrates on-device Vietnamese neural TTS (`vieneu` when installed in `.venv` + real `numpy` FFT $F_0$/formant/RMS acoustic extraction for `clone_voice`) alongside pluggable Cloud Acting providers (`gemini-2.5-flash-preview-tts` via `GEMINI_API_KEY` with acting prompts and `ElevenLabs Multilingual v2` via `ELEVENLABS_API_KEY`), configurable directly from WPF Tab 5 & `/api/v1/voices/providers`.
  3. **AI Storyboard Illustrations & Ken Burns B-Roll Compositor (`IVisualAssetGenerator` -> `StoryboardVisualAdapter` + `FfmpegAdapter.render_podcast_video`)**:
     - Splits a 6-minute podcast into **8–10 rich visual Storyboard Scenes** (`StoryScene.image_path`, `StoryScene.visual_prompt`), generates/resolves cohesive **1280x720 Cinematic Illustrations** (using `image-generator` AI artworks for Episode 1 + Pollinations/Gemini Imagen + offline Pillow atmospheric cinema canvas), and renders alternating **Ken Burns `zoompan` camera motion + `xfade` cross-dissolves + dark gradient vignette + sleek bottom audio spectrum bar**.
  4. **Concert-Hall Felt Piano Reverb & Dynamic `sidechaincompress` Ducking (`StudioAudioLibraryAdapter` + `FfmpegAdapter`)**:
     - Enriches `bgm_piano_melancholic` and `bgm_inspiring_acoustic` with warm piano overtones + `aecho` sustain reverb, and uses FFmpeg `sidechaincompress` keyed by the vocal track so the piano gently ducks during speech and rises emotionally into every pause and chapter transition.

## 2. v6.1 Cinema FullScreen Video Preview Architecture (US14)
- **Problem Statement**: In the multi-track NLE workstation, the `PROGRAM MONITOR` preview box is constrained to a `230px` vertical window. Users cannot clearly inspect subtitle readability, fine typography margins, Ken Burns motion smoothness, visual artifacting, or color grading without a true full-screen cinema view.
- **Engineered Solution**:
  1. **Dedicated Borderless Cinema Window (`FullScreenPlayerWindow.xaml`)**:
     - `WindowStyle="None"`, `WindowState="Maximized"`, `Topmost="True"`, `Background="#000000"`, Direct3D hardware-accelerated WPF `MediaElement` with `Stretch="Uniform"`.
  2. **Floating Auto-Hiding Glass HUD**:
     - Bottom-docked translucent HUD bar with Play/Pause, Step -1f/+5s, Scrub Slider, Timecode (`00:00.00 / 06:03.50`), Volume control, Video Spec badge (`1280x720 • 30fps`), and Exit button.
     - `DispatcherTimer` monitors mouse inactivity: after 2.5s of no mouse movement, the HUD automatically fades to `Opacity = 0.0`. Mouse movement immediately wakes the HUD back to `Opacity = 1.0`.
  3. **Bidirectional Playback Synchronization**:
     - Seamlessly captures current position (`Position`), play/pause state, and volume when entering FullScreen.
     - On closing (`Esc`, `F11`, exit button), passes position and playback status back to `MainWindow.VideoPlayer` and timeline scrubber.
  4. **Multi-Modal Ergonomic Controls**:
     - `BtnFullScreen` ("⛶ Toàn Màn Hình [F11]") on Transport Deck.
     - Double-clicking Program Monitor toggles FullScreen.
     - Keyboard shortcuts: `F11` or `F` toggles FullScreen; `Space` toggles Play/Pause; `Esc` exits; `Left` / `Right` arrows jump -5s / +5s.

## 3. Constitution Check (`.specify/memory/constitution.md`)
- **I. Clean Architecture**: **PASS** (UI changes strictly contained in `desktop_app/KinetixAI.Desktop/`; no presentation coupling into `domain` or `application`).
- **II. SOLID & DIP**: **PASS** (Single Responsibility: `FullScreenPlayerWindow` manages cinema viewing & auto-hide HUD; `MainWindow` orchestrates NLE workspace).
- **III. Adapter Pattern**: **PASS** (No raw process spawning; WPF MediaElement interacts with clean URI media contracts).
- **IV. Strict Type Hinting & Data Contracts**: **PASS** (Clean C# contracts for playback sync state).
- **V. Pytest & Build Coverage**: **PASS** (C# build verified with 0 warnings/errors; pytest suite verified 100% pass).
