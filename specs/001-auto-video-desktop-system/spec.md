# Feature Specification: KinetixAI (FlowVids-AI) v3.0 — AI Storyboard, Consistent Character, Voiceover/SFX/BGM Studio, Beat-Cut & Full CRUD NLE

**Feature Branch**: `001-auto-video-desktop-system` | **Created**: 2026-11-13 | **Updated**: 2026-11-16 (v3.0 Studio Expansion) | **Status**: Approved

## 1. Architectural Governance Rules (Mandatory Constraints)
1. **Strict Clean Architecture & SOLID (`domain` -> `application` -> `infrastructure` -> `presentation`)** per `.specify/memory/constitution.md`.
2. **Dependency Inversion Principle (DIP)**: All new Voiceover TTS (`IVoiceSynthesizer`), BGM/SFX Asset Library (`IAudioAssetLibrary`), and Beat-Cut / Transition / Animation (`IVideoProcessor`) capabilities live behind `abc.ABC` interfaces in `src/domain/interfaces/`.
3. **Grounded Implementation**: Zero fake/mocked UI stubs — every control in `KinetixAI.Desktop` invokes real FastAPI endpoints backed by `FFmpeg`, `edge-tts`/`System.Speech`, `Whisper`, `Remotion`, `HyperFrames`, and `yt-dlp`.

---

## 2. v3.0 User Scenarios & Functional Requirements
- **US6 — Context Bible, Storyboard Scenes & Consistent Characters**: Editors define global `SceneContext` (world setting, visual style, lighting, lens, continuity notes) and reusable `CharacterProfile`s (`name`, `role`, `voice_id`, `theme_color`, `visual_description`), link characters to scenes, and render Character Consistency HUDs in both Remotion and HyperFrames.
- **US7 — Voiceover TTS, BGM & SFX Audio Library**: Editors pick from curated Voiceover voices (`vi-VN-HoaiMyNeural`, `vi-VN-NamMinhNeural`, `en-US-AriaNeural`, etc.), 5 BGM music beds, and 6 SFX effects (`sfx_whoosh_fast`, `sfx_pop_bubble`, `sfx_glitch_digital`, `sfx_cinematic_hit`, `sfx_camera_shutter`, `sfx_chime_ding`) with real waveform synthesis, mixing, and timestamped SFX injection (`adelay` + `amix`).
- **US8 — Beat-Cut Synchronization, Transitions & Motion Animations**: Editors generate BPM Beat Grids (e.g., `120 BPM`), snap subtitle/scene cuts onto musical beats, apply visual transitions (`fade_black`, `cross_dissolve`, `wipe_left`, `slide_up`, `glitch_flash`) and camera/caption animations (`spring_pop`, `ken_burns_zoom`, `typewriter_reveal`, `neon_glow_pulse`, `slide_up_bounce`, `camera_shake_impact`).
- **US9 — Full CRUD + Clone & Structured Audit Logs**: Editors can **Add, Edit, Clone (Duplicate), and Delete** Projects, Scenes, Characters, and Subtitle Cues, and inspect every operation in the persistent structured **Audit Log Ledger**.
