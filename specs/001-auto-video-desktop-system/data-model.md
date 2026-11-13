# Phase 1 Data Model: KinetixAI (FlowVids-AI) v2.0 Professional NLE

## 1. Enumerations (`src/domain/entities/enums.py`)

### `RenderEngineType(str, Enum)`
- `REMOTION = "remotion"`
- `HYPERFRAMES = "hyperframes"`

### `JobStatus(str, Enum)`
- `PENDING = "pending"`
- `DOWNLOADING = "downloading"`
- `EXTRACTING_AUDIO = "extracting_audio"`
- `TRANSCRIBING = "transcribing"`
- `RENDERING_VISUALS = "rendering_visuals"`
- `MERGING = "merging"`
- `POST_PROCESSING = "post_processing"`
- `COMPLETED = "completed"`
- `FAILED = "failed"`

### `AspectRatioPreset(str, Enum)`
- `LANDSCAPE_16_9 = "16:9"` (`1280x720`)
- `VERTICAL_9_16 = "9:16"` (`720x1280` with blurred background canvas)
- `SQUARE_1_1 = "1:1"` (`1080x1080` / `720x720`)

### `ColorLookPreset(str, Enum)`
- `NATURAL = "natural"` (Rec.709 neutral)
- `TEAL_ORANGE = "teal_orange"` (Cinematic Teal & Orange contrast)
- `WARM_VINTAGE = "warm_vintage"` (Warm golden film grade)
- `NOIR_BW = "noir_bw"` (High-contrast monochrome B&W)
- `STUDIO_CRISP = "studio_crisp"` (Enhanced contrast, saturation & unsharp mask)

### `TemplatePreset(str, Enum)`
- `CAPTION_TEMPLATE = "CaptionTemplate"` (Broadcast Lower-Third + Word Karaoke)
- `KINETIC_TITLE = "KineticTitleCard"` (Full-screen Intro Title Card + Lower-Third)
- `SOCIAL_POP = "SocialPopCaptions"` (High-Impact Center/Lower Pop Captions for Shorts/Reels)
- `TECH_CALLOUT = "TechCalloutHUD"` (Top Callout Badge + Lower-Third + Bottom Progress Bar)

---

## 2. Domain Entities (`src/domain/entities/`)

### `WordTimestamp`
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `word` | `str` | non-empty, stripped | Individual spoken word |
| `start_time` | `float` | `>= 0.0` | Start timestamp in seconds |
| `end_time` | `float` | `>= start_time` | End timestamp in seconds |

### `SubtitleSegment`
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `start_time` | `float` | `>= 0.0` | Segment start time in seconds |
| `end_time` | `float` | `> start_time` | Segment end time in seconds |
| `text` | `str` | non-empty, stripped | Caption text displayed on screen |
| `words` | `List[WordTimestamp]` | auto-synced via `ensure_word_timestamps()` | Word-level timestamps |

### `ColorGradeSpec` (`src/domain/entities/nle_specs.py`)
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `preset` | `ColorLookPreset` | default `NATURAL` | Named LUT / Color Look preset |
| `brightness` | `float` | `-1.0 <= val <= 1.0`, default `0.0` | FFmpeg `eq` brightness offset |
| `contrast` | `float` | `0.2 <= val <= 3.0`, default `1.0` | FFmpeg `eq` contrast multiplier |
| `saturation` | `float` | `0.0 <= val <= 3.0`, default `1.0` | FFmpeg `eq` saturation multiplier |
| `gamma` | `float` | `0.2 <= val <= 3.0`, default `1.0` | FFmpeg `eq` gamma |

### `VideoProject`
| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `project_id` | `str` | non-empty | Unique project identifier |
| `source_url` | `str` | non-empty URL, file path, or `demo://sample` | Input video source |
| `engine_type` | `RenderEngineType` | default `REMOTION` | Selected visual render engine |
| `template_id` | `str` | default `"CaptionTemplate"` | Composition template identifier |
| `script_text` | `str \| None` | optional | Optional custom script text |
| `raw_video_path` | `Path \| None` | optional | Downloaded/ingested source MP4 path |
| `audio_path` | `Path \| None` | optional | Extracted WAV audio path |
| `overlay_video_path` | `Path \| None` | optional | Rendered visual overlay MP4 path |
| `subtitles` | `List[SubtitleSegment]` | default `[]` | Generated timestamped subtitle list |
| `final_output_path` | `Path \| None` | optional | Active master MP4 video path |
| `status` | `JobStatus` | default `PENDING` | Current project status |
| `progress_percent` | `int` | `0..100` | Current pipeline progress percentage |
| `current_step` | `str` | non-empty | Human-readable active step description |
| `error_message` | `str \| None` | optional | Error message if failed |
