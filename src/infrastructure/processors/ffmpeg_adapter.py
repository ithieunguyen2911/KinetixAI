"""FfmpegAdapter - Infrastructure Adapter wrapping FFmpeg & FFprobe for stream inspection, trimming, audio mixing, and compositing."""

import json
from pathlib import Path
import shutil
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

    @staticmethod
    def _safe_finalize_output(staging_path: Path, output_path: Path) -> Path:
        """Move staging_path to output_path; if output_path is locked on Windows, roll over to an unlocked rev filename."""
        try:
            if output_path.exists():
                output_path.unlink()
            shutil.move(str(staging_path), str(output_path))
            return output_path
        except OSError:
            for rev in range(1, 50):
                alt_path = output_path.with_name(f"{output_path.stem}_rev{rev}{output_path.suffix}")
                try:
                    if alt_path.exists():
                        alt_path.unlink()
                    shutil.move(str(staging_path), str(alt_path))
                    return alt_path
                except OSError:
                    continue
            return staging_path

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
        staging_path = output_path.with_name(f".staging_trim_{output_path.name}")

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
            str(staging_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return self._safe_finalize_output(staging_path, output_path)

    def split_video(
        self,
        video_path: Path,
        split_time: float,
        output_dir: Path,
    ) -> List[Path]:
        """Split video_path at split_time (seconds) into two clip files [part1, part2]."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        probe = self.probe_media(video_path)
        total_dur = max(1.0, float(probe.get("duration_seconds") or 6.0))
        if split_time <= 0.1 or split_time >= total_dur - 0.1:
            raise ValueError(f"split_time ({split_time}s) must be within (0.1s, {total_dur - 0.1:.2f}s).")
        output_dir.mkdir(parents=True, exist_ok=True)
        part1 = output_dir / f"{video_path.stem}_part1.mp4"
        part2 = output_dir / f"{video_path.stem}_part2.mp4"
        p1 = self.trim_video(video_path, part1, 0.0, split_time)
        p2 = self.trim_video(video_path, part2, split_time, total_dur)
        return [p1, p2]

    def concat_clips(
        self,
        clip_paths: List[Path],
        output_path: Path,
        transition: str = "fade",
        transition_duration: float = 0.4,
    ) -> Path:
        """Concatenate multiple video clips seamlessly into output_path."""
        if not clip_paths:
            raise ValueError("clip_paths must not be empty.")
        for cp in clip_paths:
            if not cp.exists():
                raise FileNotFoundError(f"Clip file not found: {cp}")
        if len(clip_paths) == 1:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(clip_paths[0], output_path)
            return output_path

        output_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path = output_path.with_name(f".staging_concat_{output_path.name}")
        concat_list = output_path.with_name(f".concat_list_{output_path.stem}.txt")
        lines = [f"file '{str(cp.resolve()).replace(chr(92), '/')}'" for cp in clip_paths]
        concat_list.write_text("\n".join(lines), encoding="utf-8")
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-preset",
                "ultrafast",
                "-c:a",
                "aac",
                str(staging_path),
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        finally:
            if concat_list.exists():
                concat_list.unlink()
        return self._safe_finalize_output(staging_path, output_path)

    def change_speed(
        self,
        video_path: Path,
        output_path: Path,
        speed_factor: float,
    ) -> Path:
        """Change playback speed (0.25x to 4.0x) of both video (setpts) and audio (atempo) streams."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not (0.25 <= speed_factor <= 4.0):
            raise ValueError("speed_factor must be between 0.25 and 4.0.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path = output_path.with_name(f".staging_speed_{output_path.name}")

        pts_mult = round(1.0 / speed_factor, 4)
        # Build chained atempo filters if speed_factor < 0.5 or > 2.0
        atempo_filters: List[str] = []
        rem = speed_factor
        while rem > 2.0:
            atempo_filters.append("atempo=2.0")
            rem /= 2.0
        while rem < 0.5:
            atempo_filters.append("atempo=0.5")
            rem /= 0.5
        atempo_filters.append(f"atempo={rem:.3f}")
        audio_chain = ",".join(atempo_filters)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"setpts={pts_mult}*PTS",
            "-af",
            audio_chain,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "ultrafast",
            "-c:a",
            "aac",
            str(staging_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            # Fallback if source has no audio track
            cmd_no_audio = [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-vf",
                f"setpts={pts_mult}*PTS",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-preset",
                "ultrafast",
                str(staging_path),
            ]
            subprocess.run(cmd_no_audio, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return self._safe_finalize_output(staging_path, output_path)

    def apply_color_grade(
        self,
        video_path: Path,
        output_path: Path,
        preset: str = "natural",
        brightness: float = 0.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        gamma: float = 1.0,
    ) -> Path:
        """Apply LUT/Color Look preset and eq adjustments (brightness, contrast, saturation, gamma)."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path = output_path.with_name(f".staging_grade_{output_path.name}")

        preset_key = preset.strip().lower()
        b, c, s, g = brightness, contrast, saturation, gamma
        extra_filters: List[str] = []

        if preset_key == "teal_orange":
            c = round(c * 1.15, 2)
            s = round(s * 1.25, 2)
            extra_filters.append("colorbalance=rs=0.12:gs=-0.04:bs=-0.12:rh=0.08:bh=-0.08")
        elif preset_key == "warm_vintage":
            b = round(b + 0.03, 2)
            c = round(c * 0.95, 2)
            s = round(s * 0.85, 2)
            extra_filters.append("colorbalance=rm=0.10:gm=0.04:bm=-0.10")
        elif preset_key == "noir_bw":
            s = 0.0
            c = round(c * 1.30, 2)
            g = round(g * 0.92, 2)
        elif preset_key == "studio_crisp":
            c = round(c * 1.12, 2)
            s = round(s * 1.10, 2)
            extra_filters.append("unsharp=5:5:0.8:5:5:0.0")

        vf_parts = [f"eq=brightness={b:.2f}:contrast={c:.2f}:saturation={s:.2f}:gamma={g:.2f}"] + extra_filters
        vf_chain = ",".join(vf_parts)

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            vf_chain,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "ultrafast",
            "-c:a",
            "copy",
            str(staging_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return self._safe_finalize_output(staging_path, output_path)

    def reframe_aspect_ratio(
        self,
        video_path: Path,
        output_path: Path,
        aspect_ratio: str = "16:9",
    ) -> Path:
        """Reframe video into 16:9 (1280x720), 9:16 vertical Shorts (720x1280 blur-pad), or 1:1 square (720x720)."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path = output_path.with_name(f".staging_reframe_{output_path.name}")

        ar = aspect_ratio.strip()
        if ar == "9:16":
            filter_complex = (
                "[0:v]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,boxblur=20:8[bg];"
                "[0:v]scale=720:-2[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2[vout]"
            )
        elif ar == "1:1":
            filter_complex = (
                "[0:v]scale=720:720:force_original_aspect_ratio=increase,crop=720:720,boxblur=18:6[bg];"
                "[0:v]scale=720:-2[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2[vout]"
            )
        else:
            filter_complex = (
                "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,"
                "pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x0B0F19[vout]"
            )

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-filter_complex",
            filter_complex,
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
            "copy",
            str(staging_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return self._safe_finalize_output(staging_path, output_path)

    def remove_silences(
        self,
        video_path: Path,
        output_path: Path,
        threshold_db: float = -35.0,
        min_silence_sec: float = 0.35,
    ) -> Path:
        """Apply audio silence removal / tight voice pacing filter."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path = output_path.with_name(f".staging_silence_{output_path.name}")

        af_filter = (
            f"silenceremove=start_periods=1:start_duration=0.1:start_threshold={threshold_db:.1f}dB:"
            f"stop_periods=-1:stop_duration={min_silence_sec:.2f}:stop_threshold={threshold_db:.1f}dB"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-af",
            af_filter,
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            str(staging_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return self._safe_finalize_output(staging_path, output_path)

    def normalize_audio(
        self,
        video_path: Path,
        output_path: Path,
    ) -> Path:
        """Normalize audio loudness to broadcast EBU R128 standard (-16 LUFS)."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path = output_path.with_name(f".staging_norm_{output_path.name}")

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-af",
            "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            str(staging_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return self._safe_finalize_output(staging_path, output_path)

    def capture_snapshot(
        self,
        video_path: Path,
        timestamp_sec: float,
        output_image_path: Path,
    ) -> Path:
        """Export a single high-resolution PNG frame at timestamp_sec."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        output_image_path.parent.mkdir(parents=True, exist_ok=True)
        ts = max(0.0, float(timestamp_sec))

        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            f"{ts:.3f}",
            "-i",
            str(video_path),
            "-frames:v",
            "1",
            str(output_image_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_image_path

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
        staging_path = output_path.with_name(f".staging_mix_{output_path.name}")

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
            str(staging_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return self._safe_finalize_output(staging_path, output_path)

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
        staging_path = output_path.with_name(f".staging_merge_{output_path.name}")

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
            str(staging_path),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        final_file = self._safe_finalize_output(staging_path, output_path)

        if subtitles:
            self._write_srt(subtitles, final_file.with_suffix(".srt"))
            self._write_vtt(subtitles, final_file.with_suffix(".vtt"))

        return final_file

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
