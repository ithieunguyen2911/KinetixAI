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

## 3. Reverse Engineering `debpalash/VoiceStudio` (REA Evidence Summary)
- **Target Inspected**: `https://github.com/debpalash/VoiceStudio` (111,712 GitHub stars, AGPL-3.0, Electron + Python backend powered by `k2-fsa/OmniVoice`, `CosyVoice 3`, `IndexTTS 2.5`, `WhisperX`, `faster-whisper`).
- **Core Features Mapped into KinetixAI v4.0 Clean Architecture**:
  1. **Consent-Gated Voice Cloning**: Extracts acoustic traits from clean reference audio while strictly enforcing `consent_verified == True` (refuses cloning without explicit owner permission).
  2. **Seeded Voice Design**: Deterministic natural-language trait parser (`prompt_description` + `seed`) creating reusable `VoiceProfile` definitions.
  3. **Expressive Speech Tags & Multi-Genre Podcast/Storytelling**: Supports `[pause]`, `[pause 500ms]`, `[breath]`, `[laughter]`, `[sigh]`, `[emotion:warm|excited|whisper|dramatic|mysterious|calm|late_night]` across 6 genres (`StorytellingGenre`).
  4. **Time-Aligned Video Dubbing**: Synthesizes translated segments stitched cleanly onto video timeline duration (`replace_audio_track` with automatic `tpad` video extension if narration exceeds base video).
  5. **Interactive Multi-Track Timeline CRUD**: Clickable `TimelineClip` entities across `V2`, `V1`, `S1`, `A1`, `B1` supporting inline **Add, Edit, Split at Playhead, Clone, Delete, and Ripple MP4 Render** directly inside WPF.

## 4. Research & Architectural Decision: Cinema FullScreen Player for WPF NLE Desktop (US14)

### 4.1 Evaluation of Fullscreen Approaches in WPF
- **Option 1: In-place Grid Maximization inside MainWindow**:
  - Toggling visibility of Left Dock (Column 0), Right Inspector (Column 4), Center Timeline (Row 2), and Tabs (Row 4).
  - *Drawbacks*: Prone to layout jitter, tricky grid splitter position restoration, fails to hide the Windows OS taskbar and title bar, leaving visual clutter.
- **Option 2: Dedicated Borderless Cinema Window (`FullScreenPlayerWindow.xaml`) (CHOSEN)**:
  - Configured with `WindowStyle="None"`, `WindowState="Maximized"`, `Topmost="True"`, `Background="#000000"`, `ShowInTaskbar="False"`, and `AllowsTransparency="False"` (for optimal Direct3D hardware video acceleration).
  - *Advantages*: Pure distraction-free cinema canvas, true 100% monitor resolution, completely immune to docking layout bugs, seamless keyboard event capture (`F11`, `F`, `Space`, `Esc`, arrow keys), and clean lifetime lifecycle.

### 4.2 Auto-Hiding Glass HUD Engine
- Uses a `DispatcherTimer` running on the UI thread with a `2.5-second` inactivity threshold.
- `MouseMove` event handlers on the root canvas reset the idle timer and restore HUD opacity to `1.0` with a smooth `0.2s` `DoubleAnimation`.
- When the timer fires without mouse interaction, the HUD smoothly fades to `Opacity = 0.0` with a `0.5s` `DoubleAnimation`, giving the user an unobstructed 100% view of subtitles, artwork, Ken Burns motion, and typography.
- Mouse movement immediately wakes the HUD and displays timecode, playback status, volume slider, and navigation controls.

### 4.3 Bidirectional State Synchronization
- **Entry Phase**: When the user clicks **"Toàn Màn Hình" (⛶)**, double-clicks the Program Monitor, or hits `F11`/`F`, `MainWindow` captures:
  1. Active video file URI (`VideoPlayer.Source`),
  2. Current playhead position (`VideoPlayer.Position`),
  3. Playback state (`_isPlaying`),
  4. Master volume (`_currentVolume`).
  The MainWindow pauses its player and instantiates `FullScreenPlayerWindow`.
- **Exit Phase**: Upon pressing `Esc`, `F11`, or clicking the close button, `FullScreenPlayerWindow` halts playback, passes its `CurrentPosition` and `IsPlaying` back to `MainWindow`, and `MainWindow` restores its `VideoPlayer` and timeline slider without dropping a single millisecond of progress.
