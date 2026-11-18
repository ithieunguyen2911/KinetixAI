using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace KinetixAI.Desktop.Models;

public class WordTimestampDto
{
    [JsonPropertyName("word")]
    public string Word { get; set; } = string.Empty;

    [JsonPropertyName("start_time")]
    public double StartTime { get; set; }

    [JsonPropertyName("end_time")]
    public double EndTime { get; set; }
}

public class SubtitleSegmentDto
{
    [JsonPropertyName("start_time")]
    public double StartTime { get; set; }

    [JsonPropertyName("end_time")]
    public double EndTime { get; set; }

    [JsonPropertyName("text")]
    public string Text { get; set; } = string.Empty;

    [JsonPropertyName("words")]
    public List<WordTimestampDto> Words { get; set; } = new();

    [JsonIgnore]
    public string DurationDisplay => $"{(EndTime - StartTime):0.00}s";

    [JsonIgnore]
    public int WordCount => Words?.Count > 0
        ? Words.Count
        : (string.IsNullOrWhiteSpace(Text) ? 0 : Text.Split(' ', StringSplitOptions.RemoveEmptyEntries).Length);
}

public class SceneContextDto
{
    [JsonPropertyName("world_setting")]
    public string WorldSetting { get; set; } = "Modern AI Production Studio — Dark Slate Workstation";

    [JsonPropertyName("visual_style")]
    public string VisualStyle { get; set; } = "Cinematic Clean UI, Subtle Tech Grid, High Broadcast Contrast";

    [JsonPropertyName("lighting_mood")]
    public string LightingMood { get; set; } = "Cool Cobalt Rim Light + Crisp Key Fill";

    [JsonPropertyName("camera_lens")]
    public string CameraLens { get; set; } = "35mm Anamorphic Studio Framing";

    [JsonPropertyName("continuity_notes")]
    public string ContinuityNotes { get; set; } = "Maintain consistent character badge colors, voice tone, and subtitle styling.";
}

public class CharacterProfileDto
{
    [JsonPropertyName("character_id")]
    public string CharacterId { get; set; } = "char_host";

    [JsonPropertyName("name")]
    public string Name { get; set; } = "Minh Anh (Host)";

    [JsonPropertyName("role")]
    public string Role { get; set; } = "Presenter";

    [JsonPropertyName("visual_description")]
    public string VisualDescription { get; set; } = string.Empty;

    [JsonPropertyName("voice_id")]
    public string VoiceId { get; set; } = "vi-VN-HoaiMyNeural";

    [JsonPropertyName("theme_color")]
    public string ThemeColor { get; set; } = "#3B82F6";

    [JsonPropertyName("avatar_badge")]
    public string AvatarBadge { get; set; } = "HOST";
}

public class StorySceneDto
{
    [JsonPropertyName("scene_id")]
    public string SceneId { get; set; } = "scene_01";

    [JsonPropertyName("title")]
    public string Title { get; set; } = "Scene 01";

    [JsonPropertyName("setting_context")]
    public string SettingContext { get; set; } = "Main Studio Desk";

    [JsonPropertyName("character_id")]
    public string CharacterId { get; set; } = "char_host";

    [JsonPropertyName("narration_text")]
    public string NarrationText { get; set; } = string.Empty;

    [JsonPropertyName("start_time")]
    public double StartTime { get; set; }

    [JsonPropertyName("duration_sec")]
    public double DurationSec { get; set; } = 2.0;

    [JsonPropertyName("transition_in")]
    public string TransitionIn { get; set; } = "fade_black";

    [JsonPropertyName("animation_preset")]
    public string AnimationPreset { get; set; } = "spring_pop";

    [JsonPropertyName("sfx_id")]
    public string SfxId { get; set; } = "sfx_whoosh_fast";

    [JsonPropertyName("visual_prompt")]
    public string VisualPrompt { get; set; } = string.Empty;

    [JsonPropertyName("image_path")]
    public string? ImagePath { get; set; }
}

public class AuditLogEntryDto
{
    [JsonPropertyName("log_id")]
    public string LogId { get; set; } = string.Empty;

    [JsonPropertyName("timestamp")]
    public string Timestamp { get; set; } = string.Empty;

    [JsonPropertyName("category")]
    public string Category { get; set; } = "PIPELINE";

    [JsonPropertyName("action")]
    public string Action { get; set; } = string.Empty;

    [JsonPropertyName("details")]
    public string Details { get; set; } = string.Empty;

    [JsonPropertyName("status")]
    public string Status { get; set; } = "OK";
}

public class TimelineClipDto
{
    [JsonPropertyName("clip_id")]
    public string ClipId { get; set; } = string.Empty;

    [JsonPropertyName("track_id")]
    public string TrackId { get; set; } = "V1";

    [JsonPropertyName("label")]
    public string Label { get; set; } = "Clip";

    [JsonPropertyName("start_time")]
    public double StartTime { get; set; }

    [JsonPropertyName("end_time")]
    public double EndTime { get; set; } = 2.0;

    [JsonPropertyName("source_start")]
    public double SourceStart { get; set; }

    [JsonPropertyName("source_end")]
    public double SourceEnd { get; set; } = 2.0;

    [JsonPropertyName("speed")]
    public double Speed { get; set; } = 1.0;

    [JsonPropertyName("volume")]
    public double Volume { get; set; } = 1.0;

    [JsonPropertyName("transition_in")]
    public string TransitionIn { get; set; } = "none";
}

public class ManageTimelineClipRequestDto
{
    [JsonPropertyName("action")]
    public string Action { get; set; } = "add";

    [JsonPropertyName("clip_id")]
    public string? ClipId { get; set; }

    [JsonPropertyName("split_time")]
    public double? SplitTime { get; set; }

    [JsonPropertyName("render_timeline")]
    public bool RenderTimeline { get; set; }

    [JsonPropertyName("clip")]
    public TimelineClipDto? Clip { get; set; }
}

public class PodcastTurnDto
{
    [JsonPropertyName("turn_id")]
    public string TurnId { get; set; } = string.Empty;

    [JsonPropertyName("speaker_name")]
    public string SpeakerName { get; set; } = "Host";

    [JsonPropertyName("voice_id")]
    public string VoiceId { get; set; } = "vi-VN-HoaiMyNeural";

    [JsonPropertyName("emotion")]
    public string Emotion { get; set; } = "warm";

    [JsonPropertyName("text")]
    public string Text { get; set; } = string.Empty;

    [JsonPropertyName("pause_after_ms")]
    public int PauseAfterMs { get; set; } = 350;
}

public class PodcastRequestDto
{
    [JsonPropertyName("raw_content")]
    public string RawContent { get; set; } = string.Empty;

    [JsonPropertyName("genre")]
    public string Genre { get; set; } = "podcast_dialogue";

    [JsonPropertyName("host_voice_id")]
    public string HostVoiceId { get; set; } = "vi-VN-HoaiMyNeural";

    [JsonPropertyName("guest_voice_id")]
    public string GuestVoiceId { get; set; } = "vi-VN-NamMinhNeural";

    [JsonPropertyName("bgm_volume")]
    public double BgmVolume { get; set; } = 0.14;
}

public class VoiceDesignRequestDto
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("prompt_description")]
    public string PromptDescription { get; set; } = string.Empty;

    [JsonPropertyName("seed")]
    public int Seed { get; set; } = 42;

    [JsonPropertyName("language")]
    public string Language { get; set; } = "vi-VN";
}

public class VoiceCloneRequestDto
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("reference_audio_path")]
    public string ReferenceAudioPath { get; set; } = string.Empty;

    [JsonPropertyName("consent_verified")]
    public bool ConsentVerified { get; set; }

    [JsonPropertyName("language")]
    public string Language { get; set; } = "vi-VN";
}

public class ConfigureTtsProviderRequestDto
{
    [JsonPropertyName("provider_id")]
    public string ProviderId { get; set; } = "gemini_tts";

    [JsonPropertyName("api_key")]
    public string ApiKey { get; set; } = string.Empty;

    [JsonPropertyName("model_id")]
    public string ModelId { get; set; } = string.Empty;
}

public class VoiceProfileDto
{
    [JsonPropertyName("voice_id")]
    public string VoiceId { get; set; } = string.Empty;

    [JsonPropertyName("profile_id")]
    public string ProfileId { get; set; } = string.Empty;

    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("mode")]
    public string Mode { get; set; } = "builtin";
}

public class DubbingRequestDto
{
    [JsonPropertyName("target_language")]
    public string TargetLanguage { get; set; } = "vi-VN";

    [JsonPropertyName("voice_id")]
    public string VoiceId { get; set; } = "vi-VN-HoaiMyNeural";

    [JsonPropertyName("translated_lines")]
    public List<string>? TranslatedLines { get; set; }
}

public class TimelineClipBlockVm
{
    public string ClipId { get; set; } = string.Empty;
    public string TrackId { get; set; } = "V1";
    public string Label { get; set; } = string.Empty;
    public double StartTime { get; set; }
    public double EndTime { get; set; }
    public double LeftPx { get; set; }
    public double WidthPx { get; set; }
    public string BackgroundHex { get; set; } = "#1E3A8A";
    public string BorderHex { get; set; } = "#3B82F6";
    public string BorderThicknessStr { get; set; } = "1";
}

public class CreateProjectRequestDto
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; set; } = "studio_project_01";

    [JsonPropertyName("source_url")]
    public string SourceUrl { get; set; } = "demo://sample";

    [JsonPropertyName("engine_type")]
    public string EngineType { get; set; } = "remotion";

    [JsonPropertyName("template_id")]
    public string TemplateId { get; set; } = "CaptionTemplate";

    [JsonPropertyName("script_text")]
    public string? ScriptText { get; set; }
}

public class CloneProjectRequestDto
{
    [JsonPropertyName("new_project_id")]
    public string? NewProjectId { get; set; }
}

public class ManageSceneRequestDto
{
    [JsonPropertyName("action")]
    public string Action { get; set; } = "replace_all";

    [JsonPropertyName("scene_id")]
    public string? SceneId { get; set; }

    [JsonPropertyName("scene")]
    public StorySceneDto? Scene { get; set; }

    [JsonPropertyName("scenes")]
    public List<StorySceneDto>? Scenes { get; set; }
}

public class ManageCharacterRequestDto
{
    [JsonPropertyName("action")]
    public string Action { get; set; } = "replace_all";

    [JsonPropertyName("character_id")]
    public string? CharacterId { get; set; }

    [JsonPropertyName("character")]
    public CharacterProfileDto? Character { get; set; }

    [JsonPropertyName("characters")]
    public List<CharacterProfileDto>? Characters { get; set; }
}

public class VoiceoverRequestDto
{
    [JsonPropertyName("text")]
    public string? Text { get; set; }

    [JsonPropertyName("voice_id")]
    public string VoiceId { get; set; } = "vi-VN-HoaiMyNeural";

    [JsonPropertyName("rate")]
    public double Rate { get; set; } = 1.0;

    [JsonPropertyName("pitch_hz")]
    public int PitchHz { get; set; } = 0;
}

public class SoundLibraryRequestDto
{
    [JsonPropertyName("bgm_preset")]
    public string? BgmPreset { get; set; }

    [JsonPropertyName("bgm_volume")]
    public double BgmVolume { get; set; } = 0.18;

    [JsonPropertyName("sfx_id")]
    public string? SfxId { get; set; }

    [JsonPropertyName("sfx_timestamp")]
    public double SfxTimestamp { get; set; } = 0.5;

    [JsonPropertyName("sfx_volume")]
    public double SfxVolume { get; set; } = 0.65;
}

public class FxMotionRequestDto
{
    [JsonPropertyName("transition_preset")]
    public string TransitionPreset { get; set; } = "fade_black";

    [JsonPropertyName("animation_preset")]
    public string AnimationPreset { get; set; } = "spring_pop";
}

public class BeatCutRequestDto
{
    [JsonPropertyName("bpm")]
    public int Bpm { get; set; } = 120;

    [JsonPropertyName("align_subtitles")]
    public bool AlignSubtitles { get; set; } = true;

    [JsonPropertyName("pulse_flash")]
    public bool PulseFlash { get; set; } = true;
}

public class AiMcpCommandRequestDto
{
    [JsonPropertyName("prompt")]
    public string Prompt { get; set; } = string.Empty;

    [JsonPropertyName("project_id")]
    public string? ProjectId { get; set; }

    [JsonPropertyName("source_url")]
    public string SourceUrl { get; set; } = "demo://sample";

    [JsonPropertyName("engine_type")]
    public string? EngineType { get; set; }

    [JsonPropertyName("script_text")]
    public string? ScriptText { get; set; }
}

public class TrimVideoRequestDto
{
    [JsonPropertyName("start_time")]
    public double StartTime { get; set; }

    [JsonPropertyName("end_time")]
    public double EndTime { get; set; }
}

public class SpeedChangeRequestDto
{
    [JsonPropertyName("speed_factor")]
    public double SpeedFactor { get; set; } = 1.25;
}

public class ColorGradeRequestDto
{
    [JsonPropertyName("preset")]
    public string Preset { get; set; } = "natural";

    [JsonPropertyName("brightness")]
    public double Brightness { get; set; } = 0.0;

    [JsonPropertyName("contrast")]
    public double Contrast { get; set; } = 1.0;

    [JsonPropertyName("saturation")]
    public double Saturation { get; set; } = 1.0;

    [JsonPropertyName("gamma")]
    public double Gamma { get; set; } = 1.0;
}

public class ReframeRequestDto
{
    [JsonPropertyName("aspect_ratio")]
    public string AspectRatio { get; set; } = "16:9";
}

public class AudioMasterRequestDto
{
    [JsonPropertyName("remove_silence")]
    public bool RemoveSilence { get; set; }

    [JsonPropertyName("normalize_loudness")]
    public bool NormalizeLoudness { get; set; } = true;

    [JsonPropertyName("mix_bgm")]
    public bool MixBgm { get; set; }

    [JsonPropertyName("bgm_source")]
    public string BgmSource { get; set; } = "demo://bgm";

    [JsonPropertyName("bg_volume")]
    public double BgVolume { get; set; } = 0.18;
}

public class SnapshotRequestDto
{
    [JsonPropertyName("timestamp_sec")]
    public double TimestampSec { get; set; } = 1.0;
}

public class SnapshotResponseDto
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; set; } = string.Empty;

    [JsonPropertyName("timestamp_sec")]
    public double TimestampSec { get; set; }

    [JsonPropertyName("snapshot_path")]
    public string SnapshotPath { get; set; } = string.Empty;
}

public class InspectSourceRequestDto
{
    [JsonPropertyName("source_url")]
    public string SourceUrl { get; set; } = "demo://sample";
}

public class SourceMetadataDto
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    [JsonPropertyName("duration")]
    public double Duration { get; set; }

    [JsonPropertyName("resolution")]
    public string Resolution { get; set; } = string.Empty;

    [JsonPropertyName("fps")]
    public double Fps { get; set; }

    [JsonPropertyName("source_type")]
    public string SourceType { get; set; } = string.Empty;
}

public class UpdateSubtitlesRequestDto
{
    [JsonPropertyName("engine_type")]
    public string? EngineType { get; set; }

    [JsonPropertyName("template_id")]
    public string? TemplateId { get; set; }

    [JsonPropertyName("subtitles")]
    public List<SubtitleSegmentDto> Subtitles { get; set; } = new();
}

public class ProjectResponseDto
{
    [JsonPropertyName("project_id")]
    public string ProjectId { get; set; } = string.Empty;

    [JsonPropertyName("source_url")]
    public string SourceUrl { get; set; } = string.Empty;

    [JsonPropertyName("engine_type")]
    public string EngineType { get; set; } = "remotion";

    [JsonPropertyName("template_id")]
    public string TemplateId { get; set; } = "CaptionTemplate";

    [JsonPropertyName("script_text")]
    public string? ScriptText { get; set; }

    [JsonPropertyName("raw_video_path")]
    public string? RawVideoPath { get; set; }

    [JsonPropertyName("audio_path")]
    public string? AudioPath { get; set; }

    [JsonPropertyName("overlay_video_path")]
    public string? OverlayVideoPath { get; set; }

    [JsonPropertyName("subtitles")]
    public List<SubtitleSegmentDto> Subtitles { get; set; } = new();

    [JsonPropertyName("final_output_path")]
    public string? FinalOutputPath { get; set; }

    [JsonPropertyName("status")]
    public string Status { get; set; } = "pending";

    [JsonPropertyName("progress_percent")]
    public int ProgressPercent { get; set; }

    [JsonPropertyName("current_step")]
    public string CurrentStep { get; set; } = "Ready";

    [JsonPropertyName("error_message")]
    public string? ErrorMessage { get; set; }

    [JsonPropertyName("animation_preset")]
    public string AnimationPreset { get; set; } = "spring_pop";

    [JsonPropertyName("transition_preset")]
    public string TransitionPreset { get; set; } = "fade_black";

    [JsonPropertyName("voice_id")]
    public string VoiceId { get; set; } = "vi-VN-HoaiMyNeural";

    [JsonPropertyName("bgm_preset")]
    public string BgmPreset { get; set; } = "bgm_ambient_pad";

    [JsonPropertyName("beat_timestamps")]
    public List<double> BeatTimestamps { get; set; } = new();

    [JsonPropertyName("scene_context")]
    public SceneContextDto SceneContext { get; set; } = new();

    [JsonPropertyName("characters")]
    public List<CharacterProfileDto> Characters { get; set; } = new();

    [JsonPropertyName("scenes")]
    public List<StorySceneDto> Scenes { get; set; } = new();

    [JsonPropertyName("timeline_clips")]
    public List<TimelineClipDto> TimelineClips { get; set; } = new();

    [JsonPropertyName("podcast_turns")]
    public List<PodcastTurnDto> PodcastTurns { get; set; } = new();

    [JsonPropertyName("audit_logs")]
    public List<AuditLogEntryDto> AuditLogs { get; set; } = new();

    [JsonIgnore]
    public string EngineUpper => EngineType.ToUpperInvariant();

    [JsonIgnore]
    public string StatusUpper => Status.ToUpperInvariant();
}

public class MediaProbeDto
{
    [JsonPropertyName("file_path")]
    public string FilePath { get; set; } = string.Empty;

    [JsonPropertyName("duration_seconds")]
    public double DurationSeconds { get; set; }

    [JsonPropertyName("resolution")]
    public string Resolution { get; set; } = "1280x720";

    [JsonPropertyName("fps")]
    public double Fps { get; set; } = 30.0;

    [JsonPropertyName("video_codec")]
    public string VideoCodec { get; set; } = "h264";

    [JsonPropertyName("audio_codec")]
    public string AudioCodec { get; set; } = "aac";

    [JsonPropertyName("sample_rate")]
    public int SampleRate { get; set; } = 16000;

    [JsonPropertyName("size_bytes")]
    public long SizeBytes { get; set; }
}

public class HealthResponseDto
{
    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;

    [JsonPropertyName("app_name")]
    public string AppName { get; set; } = string.Empty;

    [JsonPropertyName("version")]
    public string Version { get; set; } = string.Empty;
}
