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

public class TimelineClipBlockVm
{
    public string Label { get; set; } = string.Empty;
    public double StartTime { get; set; }
    public double EndTime { get; set; }
    public double LeftPx { get; set; }
    public double WidthPx { get; set; }
    public string BackgroundHex { get; set; } = "#1E3A8A";
    public string BorderHex { get; set; } = "#3B82F6";
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
