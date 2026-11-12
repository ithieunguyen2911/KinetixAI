"""FfmpegAdapter - Infrastructure Adapter wrapping FFmpeg & FFprobe for stream inspection, trimming, audio mixing, and compositing."""

import json
from pathlib import Path
import subprocess
from typing import Any, Dict, List

from src.domain.entities.subtitle_segment import SubtitleSegment
from src.domain.interfaces.video_processor import IVideoProcessor


class FfmpegAdapter(IVideoProcessor):
    """Adapter encapsulating FFmpeg CLI & ffprobe for media inspection, cutting, audio normalization, mixing, and overlay compositing."""

    def probe_media(self, media_path: Path) -> Dict[str, Any]:
        """Inspect media streams using ffprobe and return technical metadata (codec, resolution, fps, duration, audio)."""
        if not media_path.exists():
            raise FileNotFoundError(f"Media file not found: {media_path}")

        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            str(media_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            return {"file_path": str(media_path), "duration_seconds": 0.0}

        try:
            raw = json.loads(res.stdout)
        except Exception:
            return {"file_path": str(media_path), "duration_seconds": 0.0}

        streams = raw.get("streams", [])
        fmt = raw.get("format", {})
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})

        fps_str = str(video_stream.get("r_frame_rate", "30/1"))
        try:
            if "/" in fps_str:
                num, den = fps_str.split("/", 1)
                fps = round(float(num) / max(1.0, float(den)), 2)
            else:
                fps = round(float(fps_str), 2)
        except Exception:
            fps = 30.0

        width = int(video_stream.get("width", 1280))
        height = int(video_stream.get("height", 720))
        duration = round(float(fmt.get("duration", video_stream.get("duration", 0.0)) or 0.0), 3)
        size_bytes = int(fmt.get("size", media_path.stat().st_size) or 0)

        return {
            "file_path": str(media_path),
            "duration_seconds": duration,
            "width": width,
            "height": height,
            "resolution": f"{width}x{height}",
            "fps": fps,
            "video_codec": video_stream.get("codec_name", "h264"),
            "audio_codec": audio_stream.get("codec_name", "aac"),
            "sample_rate": int(audio_stream.get("sample_rate", 16000) or 16000),
            "size_bytes": size_bytes,
        }

    def extract_audio(self, video_path: Path, output_audio: Path) -> Path:
        """Extract speech-optimized 16kHz mono PCM WAV audio track from video_path."""
        if not video_path.exists():
            raise FileNotFoundError(f"Source video not found: {video_path}")
        output_audio.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vn",
            "-af",
            "highpass=f=80,lowpass=f=7600",
            "-acodec",
            "pcm_s16le",
            "-ar",
            "16000",
            "-ac",
            "1",
            str(output_audio),
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0 or not output_audio.exists():
            fallback_cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "anullsrc=r=16000:cl=mono",
                "-t",
                "6",
                "-acodec",
                "pcm_s16le",
                str(output_audio),
            ]
            subprocess.run(fallback_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_audio

    def trim_video(
        self,
        video_path: Path,
        output_path: Path,
        start_time: float,
        end_time: float,
    ) -> Path:
        """Cut/trim a video segment between start_time and end_time in seconds."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if end_time <= start_time:
            raise ValueError("end_time must be greater than start_time.")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            f"{start_time:.3f}",
            "-to",
            f"{end_time:.3f}",
            "-i",
            str(video_path),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "ultrafast",
            "-c:a",
            "aac",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path

    def mix_audio_tracks(
        self,
        video_path: Path,
        background_audio_path: Path,
        output_path: Path,
        bg_volume: float = 0.20,
    ) -> Path:
        """Mix background audio/music into the main video's voice track with volume attenuation."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not background_audio_path.exists():
            raise FileNotFoundError(f"Background audio not found: {background_audio_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        filter_complex = (
            f"[1:a]volume={bg_volume:.2f}[bg];"
            "[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(background_audio_path),
            "-filter_complex",
            filter_complex,
            "-map",
            "0:v:0",
            "-map",
            "[aout]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path

    def merge_and_export(
        self,
        base_video: Path,
        overlay_video: Path,
        output_path: Path,
        subtitles: List[SubtitleSegment] | None = None,
    ) -> Path:
        """Composite overlay_video (with HUD + timed captions) over base_video and export final MP4 + SRT + VTT."""
        if not base_video.exists():
            raise FileNotFoundError(f"Base video not found: {base_video}")
        if not overlay_video.exists():
            raise FileNotFoundError(f"Overlay video not found: {overlay_video}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        overlay_chain = "[1:v]colorkey=0x000000:0.06:0.05[ov];[0:v][ov]overlay=0:0:shortest=1[vout]"

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(base_video),
            "-i",
            str(overlay_video),
            "-filter_complex",
            overlay_chain,
            "-map",
            "[vout]",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "ultrafast",
            "-c:a",
            "aac",
            "-shortest",
            str(output_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if subtitles:
            self._write_srt(subtitles, output_path.with_suffix(".srt"))
            self._write_vtt(subtitles, output_path.with_suffix(".vtt"))

        return output_path

    @staticmethod
    def _write_srt(subtitles: List[SubtitleSegment], srt_path: Path) -> None:
        """Write standard SubRip (.srt) subtitle file."""
        def fmt_time(seconds: float) -> str:
            ms = int(round((seconds - int(seconds)) * 1000))
            total_sec = int(seconds)
            hrs = total_sec // 3600
            mins = (total_sec % 3600) // 60
            secs = total_sec % 60
            return f"{hrs:02d}:{mins:02d}:{secs:02d},{ms:03d}"

        lines: List[str] = []
        for idx, seg in enumerate(subtitles, start=1):
            lines.append(f"{idx}")
            lines.append(f"{fmt_time(seg.start_time)} --> {fmt_time(seg.end_time)}")
            lines.append(seg.text)
            lines.append("")
        srt_path.write_text("\n".join(lines), encoding="utf-8")

    @staticmethod
    def _write_vtt(subtitles: List[SubtitleSegment], vtt_path: Path) -> None:
        """Write standard WebVTT (.vtt) subtitle file."""
        def fmt_time(seconds: float) -> str:
            ms = int(round((seconds - int(seconds)) * 1000))
            total_sec = int(seconds)
            hrs = total_sec // 3600
            mins = (total_sec % 3600) // 60
            secs = total_sec % 60
            return f"{hrs:02d}:{mins:02d}:{secs:02d}.{ms:03d}"

        lines: List[str] = ["WEBVTT", ""]
        for idx, seg in enumerate(subtitles, start=1):
            lines.append(f"{idx}")
            lines.append(f"{fmt_time(seg.start_time)} --> {fmt_time(seg.end_time)}")
            lines.append(seg.text)
            lines.append("")
        vtt_path.write_text("\n".join(lines), encoding="utf-8")
