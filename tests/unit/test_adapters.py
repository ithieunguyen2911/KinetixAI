"""Unit tests for the 5 Infrastructure Adapters."""

from pathlib import Path
import pytest

from src.domain.entities.subtitle_segment import SubtitleSegment
from src.infrastructure.downloaders.ytdlp_adapter import YtDlpAdapter
from src.infrastructure.processors.ffmpeg_adapter import FfmpegAdapter
from src.infrastructure.renderers.hyperframes_adapter import HyperFramesAdapter
from src.infrastructure.renderers.remotion_adapter import RemotionAdapter
from src.infrastructure.transcribers.whisper_adapter import WhisperAdapter


def test_ytdlp_adapter_demo_and_local_ingestion(tmp_path: Path) -> None:
    downloader = YtDlpAdapter()
    meta = downloader.extract_metadata("demo://sample")
    assert meta["source_type"] == "demo"
    assert meta["resolution"] == "1280x720"
    assert meta["duration"] == 6.0

    raw_video = downloader.download("demo://sample", tmp_path)
    assert raw_video.exists()
    assert raw_video.stat().st_size > 1000

    # Test local file copy ingestion & metadata
    copy_dir = tmp_path / "copied"
    ingested = downloader.download(str(raw_video), copy_dir)
    assert ingested.exists()
    assert ingested.parent == copy_dir
    local_meta = downloader.extract_metadata(str(raw_video))
    assert local_meta["source_type"] == "file"


def test_ffmpeg_adapter_extract_audio_and_whisper_transcribe(tmp_path: Path) -> None:
    downloader = YtDlpAdapter()
    processor = FfmpegAdapter()
    transcriber = WhisperAdapter()

    raw_video = downloader.download("demo://sample", tmp_path)
    probe_info = processor.probe_media(raw_video)
    assert probe_info["width"] == 1280
    assert probe_info["height"] == 720
    assert probe_info["video_codec"] == "h264"
    assert probe_info["duration_seconds"] > 4.0

    # Test trim_video
    trimmed_video = tmp_path / "trimmed.mp4"
    processor.trim_video(raw_video, trimmed_video, start_time=0.5, end_time=3.5)
    assert trimmed_video.exists()
    trimmed_probe = processor.probe_media(trimmed_video)
    assert 2.0 <= trimmed_probe["duration_seconds"] <= 4.0

    audio_path = tmp_path / "extracted.wav"
    out_audio = processor.extract_audio(raw_video, audio_path)
    assert out_audio.exists()
    assert out_audio.stat().st_size > 1000

    segments = transcriber.transcribe(
        out_audio,
        script_hint="Segment One|Segment Two|Segment Three",
    )
    assert len(segments) == 3
    assert segments[0].text == "Segment One"
    assert segments[0].start_time == 0.0
    assert segments[2].end_time > segments[1].end_time
    assert len(segments[0].words) == 2

    # Verify HyperFrames-compatible .transcript.json export
    transcript_json = out_audio.with_suffix(".transcript.json")
    assert transcript_json.exists()

    # Verify automatic speech-to-text transcription when script_hint is None
    auto_segments = transcriber.transcribe(out_audio, script_hint=None)
    assert len(auto_segments) >= 1
    assert all(len(seg.words) >= 1 for seg in auto_segments)

    # Verify mix_audio_tracks
    mixed_video = tmp_path / "mixed.mp4"
    processor.mix_audio_tracks(raw_video, out_audio, mixed_video, bg_volume=0.15)
    assert mixed_video.exists()
    assert mixed_video.stat().st_size > 1000


def test_remotion_and_hyperframes_adapters_render_overlays(tmp_path: Path) -> None:
    remotion = RemotionAdapter()
    hyperframes = HyperFramesAdapter()
    props = {
        "subtitles": [
            {"start_time": 0.0, "end_time": 2.0, "text": "Hello Remotion & HyperFrames"},
            {"start_time": 2.0, "end_time": 4.0, "text": "Clean Architecture Verified"},
        ]
    }

    remotion_out = tmp_path / "remotion_overlay.mp4"
    res_r = remotion.render_composition("CaptionTemplate", props, remotion_out)
    assert res_r.exists()
    assert res_r.stat().st_size > 1000
    assert (tmp_path / "remotion_overlay.mp4.remotion.json").exists()

    hf_out = tmp_path / "hf_overlay.mp4"
    res_hf = hyperframes.render_composition("CaptionTemplate", props, hf_out)
    assert res_hf.exists()
    assert res_hf.stat().st_size > 1000
    assert (tmp_path / "hf_overlay.mp4.hyperframes.json").exists()
    assert (tmp_path / "hyperframes_composition" / "index.html").exists()
    assert (tmp_path / "hyperframes_composition" / "compositions" / "captions.html").exists()
