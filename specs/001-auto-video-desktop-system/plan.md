# Implementation Plan: KinetixAI (FlowVids-AI) v3.0 — AI Storyboard, Consistent Character, Voiceover/SFX/BGM Studio, Beat-Cut & Full CRUD/Clone NLE Workstation

**Branch**: `001-auto-video-desktop-system` | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

## 1. Architectural Vision & Open-Source GitHub References
- **Strict Clean Architecture (`domain` -> `application` -> `infrastructure` -> `presentation`)** governed by `.specify/memory/constitution.md`.
- **Open-Source Patterns Adopted**:
  - `harry0703/MoneyPrinterTurbo` & `SamurAIGPT/AI-Youtube-Shorts-Generator` (Scene-by-Scene Storyboard + Context Bible)
  - `rany2/edge-tts` + Windows `System.Speech` fallback (`IVoiceSynthesizer` / `TtsVoiceAdapter`)
  - `heygen-com/hyperframes` (`media-use` audio/SFX/BGM ledger + `beats` grid + `hyperframes-registry` motion transitions)
  - `remotion-dev/remotion` (React spring/keyframe animation & character consistency badges)
  - `OpenCut-app/OpenCut` & `notivn/AIEVv2` (Multi-track NLE CRUD, Clone/Duplicate, Structured Audit Log)

## 2. Constitution Check
- **Gate 1 — Clean Architecture**: **PASS** (`studio_entities.py`, `IVoiceSynthesizer`, `IAudioAssetLibrary` live strictly in `src/domain/`; implementations live in `src/infrastructure/`).
- **Gate 2 — SOLID & DIP**: **PASS** (`ProjectService` depends only on `IMediaDownloader`, `ITranscriber`, `IVideoProcessor`, `IVoiceSynthesizer`, `IAudioAssetLibrary`).
- **Gate 3 — Adapter Pattern**: **PASS** (`TtsVoiceAdapter`, `StudioAudioLibraryAdapter`, `FfmpegAdapter`, `RemotionAdapter`, `HyperFramesAdapter`).
- **Gate 4 — Strict Data Contracts**: **PASS** (Pydantic v2 schemas & C# DTOs synchronized across `/clone`, `/context`, `/scenes`, `/characters`, `/voiceover`, `/sound-library`, `/fx-motion`, `/beat-cut`, `DELETE /{id}`).
- **Gate 5 — Pytest Coverage & WPF Build**: **PASS** (Unit & Integration tests cover all v3.0 entities, adapters, REST endpoints, and MCP tools).
