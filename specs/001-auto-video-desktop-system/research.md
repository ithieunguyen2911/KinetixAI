# Phase 0 Research: KinetixAI (FlowVids-AI) v3.0 — AI Storyboard, Character Consistency, Voiceover/SFX/BGM & Beat-Cut NLE

## 1. Open-Source GitHub Architectures Referenced
Rather than inventing ad-hoc patterns, KinetixAI v3.0 synthesizes proven design patterns from leading open-source GitHub video & NLE projects while keeping strict Clean Architecture boundaries (`domain` -> `application` -> `infrastructure` -> `presentation`):

1. **`harry0703/MoneyPrinterTurbo` & `SamurAIGPT/AI-Youtube-Shorts-Generator`**:
   - **Scene-by-Scene Storyboard & Context Bible**: Splitting video narration into structured scenes (`StoryScene`) bound to a shared world/visual style guide (`SceneContext`) before voiceover and overlay assembly.
2. **`rany2/edge-tts` + Offline Windows `System.Speech.Synthesis`**:
   - **Multi-Voice Neural TTS**: Standard neural voice IDs (`vi-VN-HoaiMyNeural`, `vi-VN-NamMinhNeural`, `en-US-AriaNeural`, `en-US-GuyNeural`, `en-US-JennyNeural`, `win-sapi-studio`) with rate/pitch control. Uses `edge_tts` when available and automatically falls back to Windows `System.Speech.Synthesis` + FFmpeg `asetrate`/`atempo`/`equalizer` formant shaping so offline/CI test runs never fail.
3. **`heygen-com/hyperframes` (`media-use` + `hyperframes-registry` + `beats`)**:
   - **Audio Asset Library & Beat Grid**: Treating BGM (`bgm_cyber_pulse`, `bgm_ambient_pad`, `bgm_lofi_chill`, `bgm_news_broadcast`, `bgm_dramatic_rise`) and SFX (`sfx_whoosh_fast`, `sfx_pop_bubble`, `sfx_glitch_digital`, `sfx_cinematic_hit`, `sfx_camera_shutter`, `sfx_chime_ding`) as deterministic local WAV assets under `assets/audio/`.
   - **Beat Synchronization**: Generating `.beats.json` markers at target BPM (`60.0 / bpm` intervals), snapping subtitle/scene cuts onto the beat grid, and triggering rhythmic FFmpeg visual accents.
4. **`OpenCut-app/OpenCut` & `notivn/AIEVv2`**:
   - **Full CRUD + Clone & Structured Audit Log**: Editors can Create, Read, Update, Delete, and **Clone (Duplicate)** Projects, Scenes, Characters, and Subtitle Cues. Every mutation appends an `AuditLogEntry` (`timestamp`, `category`, `action`, `details`, `status`) to the project timeline ledger.
5. **`remotion-dev/remotion`**:
   - **Character Consistency HUD & Motion Presets**: Passing active `CharacterProfile` metadata (Name, Role, Accent Color, Visual Description) and `animation_preset` (`spring_pop`, `ken_burns_zoom`, `typewriter_reveal`, `neon_glow_pulse`, `slide_up_bounce`, `camera_shake_impact`) into both Remotion and HyperFrames props.

## 2. Deterministic FFmpeg Implementations for Transitions, Animations, SFX & Beat-Cut
- **Decision**: Implement `apply_transition_and_animation`, `detect_beats_and_cut`, and `insert_sfx_track` inside `FfmpegAdapter(IVideoProcessor)` using pure FFmpeg filtergraphs.
- **Rationale**:
  - **Transitions**: `fade_black` (`fade=t=in:st=0:d=0.55,fade=t=out:st=end-0.55:d=0.55`), `cross_dissolve` (`fade=t=in/out:alpha=0`), `wipe_left` (animated sweep bar + fade), `slide_up` (sliding band reveal), `glitch_flash` (`rgbashift=rh=-6:bh=6` flash windows).
  - **Animations**: `ken_burns_zoom` (`scale=1600:-1,zoompan=z='min(zoom+0.0012,1.18)':d=1:s=1280x720:fps=30`), `neon_glow_pulse` (modulated vignette/eq brightness pulse), `camera_shake_impact` (short crop jitter oscillation), plus overlay-level motion styles in Remotion/HyperFrames (`spring_pop`, `typewriter_reveal`, `slide_up_bounce`).
  - **SFX Layering**: `[1:a]adelay={ms}|{ms},volume={vol}[sfx];[0:a][sfx]amix=inputs=2:duration=first:dropout_transition=0[aout]` mixes crisp SFX onto the exact millisecond timestamp without cutting existing narration.
  - **Legacy SMPTE Removal**: Ensure no workspace project retains legacy SMPTE bars `demo_sample_raw.mp4` by switching all synthesis to dark-slate studio canvas (`0x0B0F19`) and purging legacy cached files.
