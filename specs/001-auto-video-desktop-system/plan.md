# Implementation Plan: KinetixAI (FlowVids-AI) v6.0 — Soulful Prosody, On-Device VieNeu/Cloud Expressive TTS, AI Storyboard B-Roll & Sidechain Audio Studio

**Branch**: `001-auto-video-desktop-system` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

## 1. Technical Context & v6.0 Architectural Upgrades
- **Hardware Profile**: Windows 11 AMD64, NVIDIA GeForce RTX 3050 6GB Laptop GPU, 11.7GB RAM, Python 3.11.15 (`uv`), .NET 10 WPF, FFmpeg.
- **Root-Cause Solutions Implemented (Both Phương án 1 & Phương án 2)**:
  1. **Continuous Paragraph Prosody + `SentenceBoundary` / Whisper Word Sync (`PodcastScriptParser` + `TtsVoiceAdapter`)**:
     - Eliminates the 70-fragment robotic choppy cadence by synthesizing **12–16 full Emotional Paragraph Beats** continuously while extracting exact `SentenceBoundary` timestamps (`offset / 10_000_000`) or `faster-whisper` word timestamps to generate crisp 1–2 line `.ass` subtitles with `\fad(180,140)` and keyword emphasis!
     - Dynamic emotional pacing contours (`hook_dramatic`, `melancholic_narrative`, `urgent_collapse`, `introspective_analysis`, `hopeful_turnaround`, `warm_outro`) + subtle synthesized `[breath]` / `[sigh]` cues.
  2. **Multi-Backend Expressive & Zero-Shot Voice Cloning (`VieNeu-TTS` Local ONNX + `Gemini Acting TTS` + `ElevenLabs` + Real $F_0$ Acoustic Cloning)**:
     - Integrates on-device Vietnamese neural TTS (`vieneu` when installed in `.venv` + real `numpy` FFT $F_0$/formant/RMS acoustic extraction for `clone_voice`) alongside pluggable Cloud Acting providers (`gemini-2.5-flash-preview-tts` via `GEMINI_API_KEY` with acting prompts and `ElevenLabs Multilingual v2` via `ELEVENLABS_API_KEY`), configurable directly from WPF Tab 5 & `/api/v1/voices/providers`.
  3. **AI Storyboard Illustrations & Ken Burns B-Roll Compositor (`IVisualAssetGenerator` -> `StoryboardVisualAdapter` + `FfmpegAdapter.render_podcast_video`)**:
     - Splits a 6-minute podcast into **8–10 rich visual Storyboard Scenes** (`StoryScene.image_path`, `StoryScene.visual_prompt`), generates/resolves cohesive **1280x720 Cinematic Illustrations** (using `image-generator` AI artworks for Episode 1 + Pollinations/Gemini Imagen + offline Pillow atmospheric cinema canvas), and renders alternating **Ken Burns `zoompan` camera motion + `xfade` cross-dissolves + dark gradient vignette + sleek bottom audio spectrum bar**.
  4. **Concert-Hall Felt Piano Reverb & Dynamic `sidechaincompress` Ducking (`StudioAudioLibraryAdapter` + `FfmpegAdapter`)**:
     - Enriches `bgm_piano_melancholic` and `bgm_inspiring_acoustic` with warm piano overtones + `aecho` sustain reverb, and uses FFmpeg `sidechaincompress` keyed by the vocal track so the piano gently ducks during speech and rises emotionally into every pause and chapter transition.

## 2. Constitution Check (`.specify/memory/constitution.md`)
- **I. Clean Architecture**: **PASS** (`IVisualAssetGenerator` & `StoryScene` fields in `src/domain/`; `StoryboardVisualAdapter`, `TtsVoiceAdapter`, `FfmpegAdapter` in `src/infrastructure/`; orchestration in `ProjectService`).
- **II. SOLID & DIP**: **PASS** (`ProjectService` depends strictly on `IVisualAssetGenerator`, `IVoiceSynthesizer`, `IAudioAssetLibrary`, `IVideoProcessor`).
- **III. Adapter Pattern**: **PASS** (All external TTS/Image/FFmpeg calls encapsulated inside `src/infrastructure/`).
- **IV. Strict Type Hinting & Data Contracts**: **PASS** (Pydantic v2 schemas & C# DTOs updated for `image_path`, `visual_prompt`, and TTS provider config).
- **V. Pytest Coverage**: **PASS** (Unit + integration tests in `tests/unit/test_soulful_podcast_v6.py`).
