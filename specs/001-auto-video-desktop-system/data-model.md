# Phase 1 Data Model: KinetixAI (FlowVids-AI) v3.0 — Storyboard, Consistent Character, Audio Studio & Full CRUD NLE

## 1. Enumerations (`src/domain/entities/enums.py`)
- `RenderEngineType`: `remotion`, `hyperframes`
- `JobStatus`: `pending`, `downloading`, `extracting_audio`, `transcribing`, `rendering_visuals`, `merging`, `post_processing`, `completed`, `failed`
- `AspectRatioPreset`: `16:9`, `9:16`, `1:1`
- `ColorLookPreset`: `natural`, `teal_orange`, `warm_vintage`, `noir_bw`, `studio_crisp`
- `TemplatePreset`: `CaptionTemplate`, `KineticTitleCard`, `SocialPopCaptions`, `TechCalloutHUD`
- `TransitionPreset`: `none`, `fade_black`, `cross_dissolve`, `wipe_left`, `slide_up`, `glitch_flash`
- `AnimationPreset`: `spring_pop`, `ken_burns_zoom`, `typewriter_reveal`, `neon_glow_pulse`, `slide_up_bounce`, `camera_shake_impact`

---

## 2. v3.0 Studio & Storyboard Domain Entities (`src/domain/entities/studio_entities.py`)

### `SceneContext` (Bối cảnh & Phong cách thống nhất)
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `world_setting` | `str` | `"Modern Tech Studio — Dark Slate Workstation"` | Global environment / setting Bible |
| `visual_style` | `str` | `"Cinematic Clean UI, Subtle Grid, Broadcast Contrast"` | Consistent art direction |
| `lighting_mood` | `str` | `"Cool Blue Rim Light + High-Contrast Key"` | Consistent lighting spec |
| `camera_lens` | `str` | `"35mm Anamorphic Wide"` | Virtual lens / framing rule |
| `continuity_notes` | `str` | `"Keep character palette & typography consistent across cuts."` | Multi-scene continuity notes |

### `CharacterProfile` (Nhân vật đồng nhất)
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `character_id` | `str` | required | Unique character slug (`char_host`, etc.) |
| `name` | `str` | required | Display name |
| `role` | `str` | `"Presenter"` | Narrative role (`Host / Narrator`, `AI Architect`, etc.) |
| `visual_description` | `str` | `""` | Fixed visual appearance / wardrobe description for continuity |
| `voice_id` | `str` | `"vi-VN-HoaiMyNeural"` | Bound TTS voice ID |
| `theme_color` | `str` | `"#3B82F6"` | Hex accent badge color |
| `avatar_badge` | `str` | `"HOST"` | Short badge label rendered on HUD |

### `StoryScene` (Phân cảnh Storyboard — Add / Edit / Clone / Delete)
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `scene_id` | `str` | required | Scene identifier (`scene_01`, etc.) |
| `title` | `str` | required | Scene title |
| `setting_context` | `str` | `""` | Scene-specific setting override |
| `character_id` | `str` | `""` | Linked `CharacterProfile.character_id` |
| `narration_text` | `str` | `""` | Dialogue / voiceover text |
| `start_time` | `float` | `0.0` | Timeline start position (seconds) |
| `duration_sec` | `float` | `2.0` | Scene duration (seconds) |
| `transition_in` | `str` | `"fade_black"` | Transition preset entering this scene |
| `animation_preset` | `str` | `"spring_pop"` | Motion/animation preset |
| `sfx_id` | `str` | `"sfx_whoosh_fast"` | Bound sound effect at scene boundary |

### `AuditLogEntry` (Nhật ký Log & Lịch sử thao tác)
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `log_id` | `str` | auto | Short log entry ID |
| `timestamp` | `str` | ISO-8601 / HH:MM:SS | Local execution timestamp |
| `category` | `str` | `"PIPELINE"` | `PIPELINE`, `NLE`, `AUDIO`, `CONTEXT`, `CHARACTER`, `SCENE`, `SUBTITLE` |
| `action` | `str` | required | Verb/operation performed |
| `details` | `str` | required | Detailed parameters & outcome |
| `status` | `str` | `"OK"` | `OK`, `WARN`, `ERROR` |

### Extended `VideoProject` Aggregate Root (`src/domain/entities/video_project.py`)
Adds `animation_preset`, `transition_preset`, `voice_id`, `bgm_preset`, `beat_timestamps`, `scene_context: SceneContext`, `characters: List[CharacterProfile]`, `scenes: List[StoryScene]`, `timeline_clips: List[TimelineClip]`, `podcast_turns: List[PodcastTurn]`, `audit_logs: List[AuditLogEntry]`, `ensure_timeline_clips()`, and `append_log(...)`.

---

## 3. v4.0 Podcast, VoiceStudio & Interactive Timeline Entities

- **`StorytellingGenre` (`src/domain/entities/enums.py`)**: `podcast_dialogue`, `late_night_story`, `thriller_mystery`, `audiobook_narration`, `tech_explainer`, `motivational_epic`.
- **`TimelineClip`**: `{clip_id, track_id ("V2"|"V1"|"S1"|"A1"|"B1"), label, start_time, end_time, source_start, source_end, speed, volume, transition_in}`.
- **`VoiceProfile`**: `{profile_id, name, mode ("builtin"|"designed"|"cloned"), base_voice_id, prompt_description, seed, pitch_hz, rate, warmth_eq, emotion_style, reference_audio_path, consent_verified}`.
- **`PodcastTurn`**: `{turn_id, speaker_name, voice_id, emotion, text, pause_after_ms}`.

---

## 4. v6.1 FullScreen Cinema Preview Models (US14)

### `FullScreenPlaybackState` (Desktop WPF Runtime Model)
| Field | Type | Description |
|-------|------|-------------|
| `SourceUri` | `Uri` | Absolute path/URI to the media file being previewed |
| `CurrentPosition` | `TimeSpan` | Playhead position transferred from/to `MainWindow` |
| `TotalDuration` | `TimeSpan` | Natural duration of the media stream |
| `IsPlaying` | `bool` | Running or paused status |
| `Volume` | `double` | Master audio volume [0.0 .. 1.0] |
| `IsMuted` | `bool` | Mute toggle state |
| `ResolutionLabel` | `string` | e.g. `"1280x720 • 30.0 fps"` |
| `EpisodeTitle` | `string` | Display label in upper corner of HUD |

### `CinemaHudVisibilityState` (Auto-Hide Glass Control State)
| Field | Type | Description |
|-------|------|-------------|
| `IsVisible` | `bool` | True when HUD is shown; false when faded out |
| `IdleTimeout` | `TimeSpan` | 2.5 seconds inactivity before triggering fade animation |
| `HudOpacity` | `double` | 1.0 when active, smoothly animated to 0.0 when idle |
