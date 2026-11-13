# Phase 0 Research: KinetixAI (FlowVids-AI) v2.0 Professional NLE Architecture

## 1. Non-Linear Editing (NLE) Filtergraph Architecture in `FfmpegAdapter`

- **Decision**: Implement non-destructive NLE post-production operations (`apply_color_grade`, `change_speed`, `reframe_aspect_ratio`, `remove_silences`, `normalize_audio`, `concat_clips`, `capture_snapshot`) as composable methods on `IVideoProcessor` / `FfmpegAdapter`, always reading from either `raw_video_path` or `final_output_path` via atomic staging files (`.staging_*`).
- **Rationale**:
  - **Color Grading (`apply_color_grade`)**: FFmpeg's `eq=brightness=...:contrast=...:saturation=...:gamma=...` combined with `colorbalance` / `hue` / `curves` and `unsharp` allows real-time broadcast color looks (`Teal & Orange`, `Warm Vintage`, `Monochrome Noir`, `Studio Crisp`) at native C speed.
  - **Smart Aspect Ratio Reframe (`reframe_aspect_ratio`)**: Converting a `16:9` horizontal clip into `9:16` Vertical (`720x1280`) for Shorts/TikTok/Reels using `[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,boxblur=20:10[bg];[0:v]scale=720:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2` produces a studio-grade blurred background canvas without black bars.
  - **Speed Ramping (`change_speed`)**: Using `setpts=(1/speed)*PTS` for video and `atempo=speed` for audio keeps A/V sync intact across `0.5x`–`2.0x`.
  - **Silence Removal (`remove_silences`)**: FFmpeg's `silenceremove=stop_periods=-1:stop_duration=0.4:stop_threshold=-35dB` automatically cuts dead air in talking-head videos.
- **Alternatives considered**: Frame-by-frame Python OpenCV/MoviePy pixel loops (rejected because MoviePy/OpenCV is 10x–30x slower than native FFmpeg filtergraphs and drops audio metadata).

## 2. Multi-Template Motion Graphics Engine (`Remotion` + `HyperFrames`)

- **Decision**: Support 4 standardized broadcast templates (`CaptionTemplate`, `KineticTitleCard`, `SocialPopCaptions`, `TechCalloutHUD`) across both `RemotionAdapter` and `HyperFramesAdapter`.
- **Rationale**:
  - Gives video editors distinct visual styles for different content formats:
    1. `CaptionTemplate`: Clean broadcast lower-third with word-level timing.
    2. `KineticTitleCard`: Bold intro title card (`0.0s–2.2s`) transitioning into lower-third captions.
    3. `SocialPopCaptions`: High-contrast centered/lower dynamic captions ideal for `9:16` Shorts/Reels and fast explainers.
    4. `TechCalloutHUD`: Top-left chapter callout + bottom-third caption + animated timeline progress bar at the bottom edge of the frame.
- **Alternatives considered**: Single static subtitle style (rejected because a professional video editor requires multiple motion graphic presets).

## 3. Visual Multi-Track Timeline in C# .NET WPF (`KinetixAI.Desktop`)

- **Decision**: Build a custom hardware-accelerated WPF Multi-Track Timeline panel at the bottom of `MainWindow.xaml` rendering 4 synchronized horizontal tracks (`V2 Motion Overlay`, `V1 Video Clip`, `S1 Whisper Subtitles`, `A1 Audio & Waveform`) with proportional time blocks (`Canvas` / `ItemsControl`) and interactive click-to-seek playhead.
- **Rationale**: A professional NLE (like DaVinci Resolve or Premiere Pro) relies on a visual multi-track timeline so editors can immediately see where video clips, motion overlays, subtitle cues, and audio segments sit in time, click any subtitle block to jump the Program Monitor playhead to that exact second, and inspect edits visually.
- **Alternatives considered**: Showing only a plain `DataGrid` table in the bottom half of the window (rejected because a table alone looks like a database utility rather than a professional NLE workstation).
