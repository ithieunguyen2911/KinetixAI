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

    def replace_audio_track(
        self,
        video_path: Path,
        audio_path: Path,
        output_path: Path,
    ) -> Path:
        """Replace the active audio stream of video_path with spoken voiceover audio_path, extending video if audio is longer."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path = output_path.with_name(f".staging_voice_{output_path.name}")

        v_probe = self.probe_media(video_path)
        a_probe = self.probe_media(audio_path)
        v_dur = max(2.0, float(v_probe.get("duration_seconds") or 6.0))
        a_dur = max(1.0, float(a_probe.get("duration_seconds") or v_dur))
        target_dur = max(v_dur, a_dur)

        if a_dur > v_dur + 0.15:
            pad_sec = a_dur - v_dur + 0.2
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-i",
                str(audio_path),
                "-filter_complex",
                f"[0:v]tpad=stop_mode=clone:stop_duration={pad_sec:.2f}[vout];[1:a]apad=whole_dur={target_dur:.2f}[aout]",
                "-map",
                "[vout]",
                "-map",
                "[aout]",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-preset",
                "ultrafast",
                "-c:a",
                "aac",
                "-t",
                f"{target_dur:.2f}",
                str(staging_path),
            ]
        else:
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-i",
                str(audio_path),
                "-filter_complex",
                f"[1:a]apad=whole_dur={v_dur:.2f}[aout]",
                "-map",
                "0:v:0",
                "-map",
                "[aout]",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-t",
                f"{v_dur:.2f}",
                str(staging_path),
            ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return self._safe_finalize_output(staging_path, output_path)

    def insert_sfx_track(
        self,
        video_path: Path,
        sfx_path: Path,
        output_path: Path,
        timestamp_sec: float = 0.0,
        volume: float = 0.65,
    ) -> Path:
        """Mix a short sound effect (SFX) into video_path at the exact timestamp_sec."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not sfx_path.exists():
            raise FileNotFoundError(f"SFX file not found: {sfx_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path = output_path.with_name(f".staging_sfx_{output_path.name}")
        delay_ms = max(0, int(round(timestamp_sec * 1000)))

        filter_complex = (
            f"[1:a]adelay={delay_ms}|{delay_ms},volume={volume:.2f}[sfx];"
            "[0:a][sfx]amix=inputs=2:duration=first:dropout_transition=0[aout]"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-i",
            str(sfx_path),
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
            str(staging_path),
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if res.returncode != 0:
            # Fallback if base video had no audio track
            cmd_fallback = [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-i",
                str(sfx_path),
                "-filter_complex",
                f"[1:a]adelay={delay_ms}|{delay_ms},volume={volume:.2f}[aout]",
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
            subprocess.run(cmd_fallback, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return self._safe_finalize_output(staging_path, output_path)

    def apply_transition_and_animation(
        self,
        video_path: Path,
        output_path: Path,
        transition_preset: str = "fade_black",
        animation_preset: str = "spring_pop",
    ) -> Path:
        """Apply visual transition and camera/motion animation filters onto video_path."""
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path = output_path.with_name(f".staging_fx_{output_path.name}")

        probe = self.probe_media(video_path)
        dur = max(1.5, float(probe.get("duration_seconds") or 6.0))
        w = int(probe.get("width") or 1280)
        h = int(probe.get("height") or 720)
        out_st = max(0.5, dur - 0.55)

        vf_parts: List[str] = []
        tr = transition_preset.strip().lower()
        an = animation_preset.strip().lower()

        if an == "ken_burns_zoom":
            vf_parts.append(
                f"scale=1600:-1,zoompan=z='min(zoom+0.0008,1.12)':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=30"
            )
        elif an == "neon_glow_pulse":
            vf_parts.append("eq=contrast=1.08:saturation=1.20")
            vf_parts.append(
                f"drawbox=x=0:y=0:w={w}:h=4:color=0x38BDF8@0.90:t=fill:enable='gt(mod(t\\,1.0)\\,0.5)'"
            )
        elif an == "camera_shake_impact":
            vf_parts.append(
                f"crop=w=iw-16:h=ih-16:x='8+8*sin(t*36)*lt(t\\,0.50)':y='8+6*cos(t*40)*lt(t\\,0.50)',scale={w}:{h}"
            )

        if tr == "fade_black":
            vf_parts.append(f"fade=t=in:st=0:d=0.50,fade=t=out:st={out_st:.2f}:d=0.50")
        elif tr == "cross_dissolve":
            vf_parts.append(f"fade=t=in:st=0:d=0.45:color=0x0B0F19,fade=t=out:st={out_st:.2f}:d=0.45:color=0x0B0F19")
        elif tr == "wipe_left":
            vf_parts.append("drawbox=x='max(0,w-2400*t)':y=0:w=iw:h=ih:color=0x0B0F19@0.96:t=fill:enable='lt(t\\,0.55)'")
        elif tr == "slide_up":
            vf_parts.append("drawbox=x=0:y='min(ih,ih*(1-t/0.50))':w=iw:h=ih:color=0x0B0F19@0.96:t=fill:enable='lt(t\\,0.50)'")
        elif tr == "glitch_flash":
            vf_parts.append("rgbashift=rh=-8:bh=8:enable='lt(t\\,0.35)+between(t\\,2.0\\,2.2)+between(t\\,4.0\\,4.2)'")

        if not vf_parts:
            vf_parts.append("null")

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            ",".join(vf_parts),
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

    def detect_beats_and_cut(
        self,
        video_path: Path,
        output_path: Path,
        bpm: int = 120,
        pulse_flash: bool = True,
    ) -> tuple[Path, List[float]]:
        """Generate BPM beat timestamps (.beats.json) and render rhythmic beat-cut accents."""
        import json

        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        staging_path = output_path.with_name(f".staging_beat_{output_path.name}")

        probe = self.probe_media(video_path)
        dur = max(1.0, float(probe.get("duration_seconds") or 6.0))
        safe_bpm = max(40, min(240, int(bpm)))
        beat_step = 60.0 / safe_bpm
        beats: List[float] = []
        t = 0.0
        while t < dur - 0.05:
            beats.append(round(t, 3))
            t += beat_step

        beats_file = output_path.with_suffix(".beats.json")
        beats_file.write_text(
            json.dumps({"bpm": safe_bpm, "duration_seconds": dur, "beats": beats}, indent=2),
            encoding="utf-8",
        )

        if pulse_flash and beats:
            downbeats = [b for idx, b in enumerate(beats) if idx % 2 == 0][:16]
            enable_expr = "+".join([f"between(t\\,{b:.2f}\\,{b + 0.14:.2f})" for b in downbeats])
            vf = (
                f"drawbox=x=0:y=0:w=iw:h=6:color=0x3B82F6@0.92:t=fill:enable='{enable_expr}',"
                f"drawbox=x=0:y=ih-6:w=iw:h=6:color=0x3B82F6@0.92:t=fill:enable='{enable_expr}'"
            )
        else:
            vf = "null"

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            vf,
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
        final_file = self._safe_finalize_output(staging_path, output_path)
        return final_file, beats

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
    def _escape_drawtext(text: str) -> str:
        """Escape special characters for FFmpeg drawtext filter strings while preserving UTF-8 Vietnamese glyphs."""
        return (
            str(text or "")
            .replace("\\", "\\\\")
            .replace("'", "’")
            .replace(":", "\\:")
            .replace("%", "\\%")
            .replace(",", "\\,")
            .replace(";", "\\;")
            .replace("[", "\\[")
            .replace("]", "\\]")
        )

    @staticmethod
    def _escape_filter_path(file_path: Path) -> str:
        """Format a Windows/POSIX path for single-quoted FFmpeg filter options such as ass='...'."""
        return (
            str(file_path.resolve())
            .replace("\\", "/")
            .replace(":", "\\:")
            .replace("'", "\\'")
        )

    @staticmethod
    def wrap_subtitle_text(text: str, max_chars: int = 50, sep: str = "\\N") -> str:
        """Word-wrap UTF-8 Vietnamese/English text into lines of at most max_chars without splitting words mid-syllable."""
        cleaned = " ".join(str(text or "").strip().split())
        if not cleaned:
            return ""
        limit = max(12, int(max_chars))
        if len(cleaned) <= limit:
            return cleaned

        words = cleaned.split(" ")

        def _greedy_wrap(line_limit: int) -> List[str]:
            out: List[str] = []
            current = ""
            for word in words:
                if not current:
                    current = word
                elif len(current) + 1 + len(word) <= line_limit:
                    current = f"{current} {word}"
                else:
                    out.append(current)
                    current = word
            if current:
                out.append(current)
            return out

        lines = _greedy_wrap(limit)
        # Balance 2-line captions when the trailing line has a short orphan word
        if len(lines) == 2 and len(lines[1]) < 14 and len(cleaned) <= limit * 2:
            balanced_target = min(limit, max(22, (len(cleaned) // 2) + 5))
            balanced = _greedy_wrap(balanced_target)
            if len(balanced) == 2 and all(len(ln) <= limit for ln in balanced):
                lines = balanced

        return sep.join(lines)

    @classmethod
    def _write_ass(
        cls,
        subtitles: List[SubtitleSegment],
        ass_path: Path,
        width: int = 1280,
        height: int = 720,
    ) -> Path:
        """Write a broadcast-styled UTF-8 Advanced SubStation Alpha (.ass) subtitle file with word-wrapped lines."""
        ass_path.parent.mkdir(parents=True, exist_ok=True)

        def fmt_ass_time(seconds: float) -> str:
            total_cs = max(0, int(round(float(seconds) * 100)))
            hrs = total_cs // 360000
            mins = (total_cs % 360000) // 6000
            secs = (total_cs % 6000) // 100
            cs = total_cs % 100
            return f"{hrs}:{mins:02d}:{secs:02d}.{cs:02d}"

        max_chars = max(24, int(round(50 * (width / 1280.0))))
        lines: List[str] = [
            "[Script Info]",
            "Title: KinetixAI Broadcast Subtitles",
            "ScriptType: v4.00+",
            f"PlayResX: {int(width)}",
            f"PlayResY: {int(height)}",
            "WrapStyle: 0",
            "ScaledBorderAndShadow: yes",
            "YCbCr Matrix: TV.709",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
            "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
            "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            # BorderStyle=1 over lower-third scrim prevents multi-line box overlap while keeping crisp contrast
            "Style: Default,Segoe UI,28,&H00FBFAF9,&H00F8BD38,&H00180D06,&HAA120804,"
            "-1,0,0,0,100,100,0,0,1,2.8,1.8,2,90,90,50,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]

        for seg in subtitles:
            raw_text = str(seg.text or "").replace("{", "(").replace("}", ")").strip()
            if not raw_text:
                continue
            wrapped = cls.wrap_subtitle_text(raw_text, max_chars=max_chars, sep="\\N")
            line_count = wrapped.count("\\N") + 1
            prefix = "{\\fad(160,140)\\fs24}" if line_count >= 3 else "{\\fad(160,140)}"
            start_ts = fmt_ass_time(seg.start_time)
            end_ts = fmt_ass_time(max(seg.start_time + 0.15, seg.end_time))
            lines.append(f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{prefix}{wrapped}")

        ass_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return ass_path

    def _render_storyboard_broll_track(
        self,
        scene_visuals: List[Dict[str, Any]],
        total_dur: float,
        output_path: Path,
        temp_files: List[Path],
    ) -> Path | None:
        """Render per-scene 30fps Ken Burns animated segments and concatenate seamlessly into a B-roll MP4."""
        valid_scenes: List[Dict[str, Any]] = []
        for sc in scene_visuals:
            img_raw = sc.get("image_path")
            if img_raw and Path(img_raw).is_file():
                valid_scenes.append(sc)

        if not valid_scenes:
            return None

        has_explicit_times = any(float(sc.get("end_time", 0.0) or 0.0) > 0.0 for sc in valid_scenes)
        if has_explicit_times:
            ordered = sorted(
                enumerate(valid_scenes),
                key=lambda pair: (float(pair[1].get("start_time", 0.0) or 0.0), pair[0]),
            )
            valid_scenes = [sc for _, sc in ordered]

        n_scenes = len(valid_scenes)
        durations: List[float] = []
        if has_explicit_times and n_scenes > 1 and total_dur >= 0.6 * n_scenes:
            bounds: List[float] = [0.0]
            for idx in range(1, n_scenes):
                raw_st = float(valid_scenes[idx].get("start_time", 0.0) or 0.0)
                min_b = bounds[-1] + 0.45
                max_b = total_dur - 0.45 * (n_scenes - idx)
                bounds.append(max(min_b, min(max_b, raw_st)))
            bounds.append(total_dur)
            durations = [max(0.45, bounds[i + 1] - bounds[i]) for i in range(n_scenes)]
        else:
            even_dur = max(0.5, total_dur / float(n_scenes))
            durations = [even_dur for _ in range(n_scenes)]
            if durations:
                durations[-1] = max(0.45, total_dur - sum(durations[:-1]))

        clip_paths: List[Path] = []
        for idx, (sc, dur_i) in enumerate(zip(valid_scenes, durations)):
            img_path = Path(sc["image_path"])
            frames = max(12, int(round(dur_i * 30.0)))
            denom = max(1, frames - 1)
            fade_d = round(min(0.60, max(0.15, dur_i * 0.24)), 2)
            fade_out_st = round(max(0.05, (frames / 30.0) - fade_d), 2)

            if idx % 2 == 0:
                z_expr = f"1.0+0.10*(on/{denom})"
                x_expr = f"(iw-iw/zoom)/2+(iw-iw/zoom)*0.20*(on/{denom}-0.5)"
            else:
                z_expr = f"1.10-0.10*(on/{denom})"
                x_expr = f"(iw-iw/zoom)/2-(iw-iw/zoom)*0.20*(on/{denom}-0.5)"
            y_expr = "(ih-ih/zoom)/2"

            vf_scene = (
                f"scale=1536:864:force_original_aspect_ratio=increase,crop=1536:864,"
                f"zoompan=z='{z_expr}':x='{x_expr}':y='{y_expr}':d={frames}:s=1280x720:fps=30,"
                f"vignette=PI/5.5,"
                f"fade=t=in:st=0:d={fade_d:.2f}:color=0x070B14,"
                f"fade=t=out:st={fade_out_st:.2f}:d={fade_d:.2f}:color=0x070B14,"
                f"format=yuv420p"
            )
            seg_path = output_path.with_name(f".staging_pod_kb_{output_path.stem}_{idx:02d}.mp4")
            temp_files.append(seg_path)

            seg_cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(img_path),
                "-vf",
                vf_scene,
                "-frames:v",
                str(frames),
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-preset",
                "ultrafast",
                "-r",
                "30",
                "-video_track_timescale",
                "15360",
                "-an",
                str(seg_path),
            ]
            res_seg = subprocess.run(seg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res_seg.returncode == 0 and seg_path.exists():
                clip_paths.append(seg_path)

        if not clip_paths:
            return None
        if len(clip_paths) == 1:
            return clip_paths[0]

        broll_track = output_path.with_name(f".staging_pod_broll_{output_path.stem}.mp4")
        concat_list = output_path.with_name(f".staging_pod_broll_list_{output_path.stem}.txt")
        temp_files.extend([broll_track, concat_list])

        concat_lines = [f"file '{str(cp.resolve()).replace(chr(92), '/')}'" for cp in clip_paths]
        concat_list.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")

        concat_copy_cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_list),
            "-c",
            "copy",
            str(broll_track),
        ]
        res_concat = subprocess.run(concat_copy_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res_concat.returncode != 0 or not broll_track.exists():
            concat_reenc_cmd = [
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
                "-r",
                "30",
                "-an",
                str(broll_track),
            ]
            res_re = subprocess.run(concat_reenc_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res_re.returncode != 0 or not broll_track.exists():
                return clip_paths[0]

        return broll_track

    def render_podcast_video(
        self,
        voice_audio_path: Path,
        output_path: Path,
        subtitles: List[SubtitleSegment],
        episode_title: str = "KINETIX PODCAST STUDIO",
        speaker_label: str = "HOST • NAM MINH",
        chapters: List[Dict[str, Any]] | None = None,
        bgm_primary_path: Path | None = None,
        bgm_secondary_path: Path | None = None,
        bgm_transition_sec: float | None = None,
        bgm_volume: float = 0.14,
        sfx_events: List[Dict[str, Any]] | None = None,
        scene_visuals: List[Dict[str, Any]] | None = None,
    ) -> Path:
        """Render a broadcast-grade 1280x720@30fps Podcast MP4 with Ken Burns storyboard B-roll, live voice waveform, Chapter HUD, wrapped .ass captions, SFX, and sidechain-ducked 2-stage BGM."""
        if not voice_audio_path.exists():
            raise FileNotFoundError(f"Podcast voice audio file not found: {voice_audio_path}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        staging_video = output_path.with_name(f".staging_pod_{output_path.name}")
        staging_master_audio = output_path.with_name(f".staging_pod_master_{output_path.stem}.wav")
        staging_ass = output_path.with_name(f".staging_pod_subs_{output_path.stem}.ass")
        extra_temp_files: List[Path] = []

        voice_probe = self.probe_media(voice_audio_path)
        voice_dur = max(2.0, float(voice_probe.get("duration_seconds") or 2.0))
        max_sub_end = max((float(s.end_time) for s in subtitles), default=0.0)
        total_dur = round(max(voice_dur, max_sub_end), 2)

        safe_bgm_vol = max(0.0, min(1.0, float(bgm_volume)))
        bgm_eff_vol = min(0.42, safe_bgm_vol * 1.85) if safe_bgm_vol > 0.0 else 0.0
        has_primary = bgm_primary_path is not None and Path(bgm_primary_path).exists()
        has_secondary = bgm_secondary_path is not None and Path(bgm_secondary_path).exists()
        has_two_stage_bgm = (
            has_primary
            and has_secondary
            and bgm_transition_sec is not None
            and (1.0 < float(bgm_transition_sec) < total_dur - 1.0)
        )
        has_any_bgm = (has_primary or has_secondary) and bgm_eff_vol > 0.001

        try:
            # =========================================================================
            # STEP A: Master Podcast Audio (Sidechain-Ducked BGM + Upfront Voice + SFX)
            # =========================================================================
            def _build_master_audio_cmd(use_sidechain: bool) -> List[str]:
                cmd: List[str] = ["ffmpeg", "-y", "-i", str(voice_audio_path)]
                filters: List[str] = [
                    f"[0:a]aresample=24000,aformat=sample_rates=24000:channel_layouts=stereo,"
                    f"volume=1.18,apad=whole_dur={total_dur:.2f},atrim=0:{total_dur:.2f},asetpts=PTS-STARTPTS[voice]"
                ]
                sfx_labels: List[str] = []
                next_idx = 1

                for sfx_i, ev in enumerate(sfx_events or []):
                    raw_sfx_path = ev.get("path")
                    if not raw_sfx_path:
                        continue
                    sfx_file = Path(raw_sfx_path)
                    ts_sec = float(ev.get("timestamp_sec", 0.0) or 0.0)
                    if not sfx_file.exists() or ts_sec < 0.0 or ts_sec >= total_dur:
                        continue
                    sfx_vol = max(0.0, min(2.0, float(ev.get("volume", 0.55) or 0.55)))
                    delay_ms = max(0, int(round(ts_sec * 1000)))
                    cmd.extend(["-i", str(sfx_file)])
                    lbl = f"sfx{sfx_i}"
                    filters.append(
                        f"[{next_idx}:a]aresample=24000,aformat=sample_rates=24000:channel_layouts=stereo,"
                        f"volume={sfx_vol:.3f},adelay={delay_ms}|{delay_ms},"
                        f"apad=whole_dur={total_dur:.2f},atrim=0:{total_dur:.2f},asetpts=PTS-STARTPTS[{lbl}]"
                    )
                    sfx_labels.append(f"[{lbl}]")
                    next_idx += 1

                end_fade_d = min(1.8, max(0.25, total_dur * 0.25))
                end_fade_st = max(0.1, total_dur - end_fade_d)
                bed_vol = bgm_eff_vol if use_sidechain else safe_bgm_vol

                if has_two_stage_bgm and bgm_primary_path is not None and bgm_secondary_path is not None and bed_vol > 0.001:
                    tr_sec = float(bgm_transition_sec or 0.0)
                    bgm1_end = min(total_dur, tr_sec + 1.25)
                    f1_d = min(2.5, max(0.3, bgm1_end - 0.2))
                    f1_st = max(0.1, bgm1_end - f1_d)

                    bgm2_start = max(0.0, tr_sec - 1.5)
                    bgm2_len = max(0.5, total_dur - bgm2_start)
                    bgm2_ms = max(0, int(round(bgm2_start * 1000)))
                    f2_in_d = min(2.5, max(0.3, bgm2_len * 0.6))

                    cmd.extend(["-stream_loop", "-1", "-i", str(bgm_primary_path)])
                    idx_b1 = next_idx
                    next_idx += 1

                    cmd.extend(["-stream_loop", "-1", "-i", str(bgm_secondary_path)])
                    idx_b2 = next_idx
                    next_idx += 1

                    filters.append(
                        f"[{idx_b1}:a]aresample=24000,aformat=sample_rates=24000:channel_layouts=stereo,"
                        f"atrim=0:{bgm1_end:.2f},asetpts=PTS-STARTPTS,"
                        f"afade=t=in:st=0:d=0.80,afade=t=out:st={f1_st:.2f}:d={f1_d:.2f},"
                        f"volume={bed_vol:.3f},apad=whole_dur={total_dur:.2f},atrim=0:{total_dur:.2f},asetpts=PTS-STARTPTS[bgm1]"
                    )
                    filters.append(
                        f"[{idx_b2}:a]aresample=24000,aformat=sample_rates=24000:channel_layouts=stereo,"
                        f"atrim=0:{bgm2_len:.2f},asetpts=PTS-STARTPTS,"
                        f"afade=t=in:st=0:d={f2_in_d:.2f},volume={bed_vol:.3f},"
                        f"adelay={bgm2_ms}|{bgm2_ms},apad=whole_dur={total_dur:.2f},atrim=0:{total_dur:.2f},"
                        f"afade=t=out:st={end_fade_st:.2f}:d={end_fade_d:.2f},asetpts=PTS-STARTPTS[bgm2]"
                    )
                    filters.append(
                        "[bgm1][bgm2]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
                        "aformat=sample_rates=24000:channel_layouts=stereo[bgm_bed]"
                    )
                    bgm_ready = True
                elif (has_primary or has_secondary) and bed_vol > 0.001:
                    single_bgm = bgm_primary_path if has_primary else bgm_secondary_path
                    cmd.extend(["-stream_loop", "-1", "-i", str(single_bgm)])
                    idx_b = next_idx
                    next_idx += 1
                    filters.append(
                        f"[{idx_b}:a]aresample=24000,aformat=sample_rates=24000:channel_layouts=stereo,"
                        f"atrim=0:{total_dur:.2f},asetpts=PTS-STARTPTS,"
                        f"afade=t=in:st=0:d=0.80,afade=t=out:st={end_fade_st:.2f}:d={end_fade_d:.2f},"
                        f"volume={bed_vol:.3f},apad=whole_dur={total_dur:.2f},atrim=0:{total_dur:.2f},asetpts=PTS-STARTPTS[bgm_bed]"
                    )
                    bgm_ready = True
                else:
                    bgm_ready = False

                if bgm_ready and use_sidechain and total_dur >= 1.0:
                    filters.append("[voice]asplit=2[voice_main][voice_sc]")
                    filters.append(
                        "[bgm_bed][voice_sc]sidechaincompress="
                        "threshold=0.022:ratio=5.5:attack=35:release=680:makeup=1.0[bgm_ducked]"
                    )
                    mix_labels = ["[voice_main]", "[bgm_ducked]"] + sfx_labels
                else:
                    mix_labels = ["[voice]"] + (["[bgm_bed]"] if bgm_ready else []) + sfx_labels

                if len(mix_labels) == 1:
                    filters.append(f"{mix_labels[0]}alimiter=limit=0.96[aout]")
                else:
                    filters.append(
                        f"{''.join(mix_labels)}amix=inputs={len(mix_labels)}:duration=first:"
                        f"dropout_transition=0:normalize=0,alimiter=limit=0.96[aout]"
                    )

                cmd.extend(
                    [
                        "-filter_complex",
                        ";".join(filters),
                        "-map",
                        "[aout]",
                        "-acodec",
                        "pcm_s16le",
                        "-ar",
                        "24000",
                        "-ac",
                        "2",
                        "-t",
                        f"{total_dur:.2f}",
                        str(staging_master_audio),
                    ]
                )
                return cmd

            res_audio = subprocess.run(
                _build_master_audio_cmd(use_sidechain=has_any_bgm and total_dur >= 1.0),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if (res_audio.returncode != 0 or not staging_master_audio.exists()) and has_any_bgm:
                # Fallback 1: standard non-sidechain amix if sidechaincompress failed on edge-case stream
                res_audio = subprocess.run(
                    _build_master_audio_cmd(use_sidechain=False),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            if res_audio.returncode != 0 or not staging_master_audio.exists():
                # Fallback 2: clean upfront voice master
                fallback_audio_cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(voice_audio_path),
                    "-af",
                    f"aresample=24000,aformat=sample_rates=24000:channel_layouts=stereo,"
                    f"volume=1.18,apad=whole_dur={total_dur:.2f},atrim=0:{total_dur:.2f}",
                    "-acodec",
                    "pcm_s16le",
                    "-ar",
                    "24000",
                    "-ac",
                    "2",
                    str(staging_master_audio),
                ]
                subprocess.run(fallback_audio_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # =========================================================================
            # STEP B: Storyboard Ken Burns B-Roll (or Studio Canvas) + Waveform + .ass
            # =========================================================================
            self._write_ass(subtitles, staging_ass, width=1280, height=720)

            font_reg_file = Path("C:/Windows/Fonts/segoeui.ttf")
            font_bold_file = Path("C:/Windows/Fonts/segoeuib.ttf")
            font_reg = "fontfile='C\\:/Windows/Fonts/segoeui.ttf':" if font_reg_file.exists() else ""
            font_bold = (
                "fontfile='C\\:/Windows/Fonts/segoeuib.ttf':"
                if font_bold_file.exists()
                else font_reg
            )

            clean_title = " ".join(str(episode_title or "KINETIX PODCAST STUDIO").strip().split())
            if len(clean_title) > 48:
                clean_title = f"{clean_title[:46].rstrip()}…"
            clean_speaker = " ".join(str(speaker_label or "HOST • NAM MINH").strip().split())
            if len(clean_speaker) > 28:
                clean_speaker = f"{clean_speaker[:26].rstrip()}…"

            safe_title = self._escape_drawtext(clean_title)
            safe_speaker = self._escape_drawtext(clean_speaker)

            has_turnaround_hud = bgm_transition_sec is not None and (0.2 < float(bgm_transition_sec) < total_dur)
            tr_val = float(bgm_transition_sec or 0.0)
            tr_enable = f":enable='gte(t\\,{tr_val:.2f})'"

            effective_chapters = list(chapters) if chapters else [
                {"title": clean_title, "start_time": 0.0, "end_time": total_dur, "mood": "STUDIO LIVE"}
            ]

            broll_track: Path | None = None
            if scene_visuals:
                broll_track = self._render_storyboard_broll_track(
                    scene_visuals=scene_visuals,
                    total_dur=total_dur,
                    output_path=output_path,
                    temp_files=extra_temp_files,
                )

            esc_ass = self._escape_filter_path(staging_ass)
            sub_stage = f"[vp]ass='{esc_ass}'[vout]" if subtitles else "[vp]null[vout]"

            if broll_track is not None and broll_track.exists():
                # -----------------------------------------------------------------
                # CINEMATIC STORYBOARD B-ROLL LAYOUT (75% Unobstructed Center Art)
                # -----------------------------------------------------------------
                broll_hud_ops: List[str] = [
                    # Subtle top (y=0..118) & bottom (y=530..720) dark cinema scrims
                    "drawbox=x=0:y=0:w=1280:h=118:color=0x070B14@0.68:t=fill",
                    "drawbox=x=0:y=530:w=1280:h=190:color=0x070B14@0.78:t=fill",
                    "drawbox=x=0:y=0:w=1280:h=3:color=0x38BDF8@0.90:t=fill",
                    # Translucent Top Episode Bar (y=18..58)
                    "drawbox=x=44:y=18:w=1192:h=40:color=0x0B1120@0.62:t=fill",
                    "drawbox=x=44:y=18:w=4:h=40:color=0x38BDF8@0.96:t=fill",
                    f"drawtext={font_bold}text='PODCAST STUDIO':fontcolor=0x38BDF8:fontsize=13:x=62:y=31",
                    f"drawtext={font_bold}text='{safe_title}':fontcolor=0xF9FAFB:fontsize=18:x=204:y=28",
                    f"drawtext={font_bold}text='{safe_speaker}':fontcolor=0x93C5FD:fontsize=14:x=1218-text_w:y=31",
                    # Active Chapter HUD Strip (y=64..98)
                    "drawbox=x=44:y=64:w=1192:h=34:color=0x070B14@0.54:t=fill",
                    "drawbox=x=44:y=64:w=3:h=34:color=0x38BDF8@0.88:t=fill",
                    # Subtle center baseline for compact waveform + bottom progress track (y=714, h=6)
                    "drawbox=x=440:y=519:w=400:h=1:color=0x94A3B8@0.28:t=fill",
                    "drawbox=x=0:y=714:w=1280:h=6:color=0x1E293B@0.88:t=fill",
                ]
                if has_turnaround_hud:
                    broll_hud_ops.extend(
                        [
                            f"drawbox=x=0:y=0:w=1280:h=3:color=0xF59E0B@0.96:t=fill{tr_enable}",
                            f"drawbox=x=44:y=18:w=4:h=40:color=0xF59E0B@0.98:t=fill{tr_enable}",
                            f"drawtext={font_bold}text='PODCAST STUDIO':fontcolor=0xFCD34D:fontsize=13:x=62:y=31{tr_enable}",
                            f"drawbox=x=44:y=64:w=3:h=34:color=0x10B981@0.95:t=fill{tr_enable}",
                        ]
                    )

                for idx, ch in enumerate(effective_chapters, start=1):
                    ch_raw = " ".join(str(ch.get("title") or f"Phần {idx}").strip().split())
                    if len(ch_raw) > 64:
                        ch_raw = f"{ch_raw[:62].rstrip()}…"
                    c_start = max(0.0, float(ch.get("start_time", 0.0) or 0.0))
                    c_end = max(c_start + 0.1, float(ch.get("end_time", total_dur) or total_dur))
                    if idx == len(effective_chapters):
                        c_end = max(c_end, total_dur + 0.25)
                    ch_label = self._escape_drawtext(f"CHƯƠNG {idx:02d}  •  {ch_raw}")
                    broll_hud_ops.append(
                        f"drawtext={font_bold}text='{ch_label}':fontcolor=0xE2E8F0:fontsize=15:"
                        f"x=62:y=73:enable='between(t\\,{c_start:.2f}\\,{c_end:.2f})'"
                    )
                    mood_raw = " ".join(str(ch.get("mood") or "").strip().split()).upper()
                    if mood_raw:
                        safe_mood = self._escape_drawtext(mood_raw[:24])
                        mood_col = "0xFCD34D" if "HOPE" in mood_raw else "0x38BDF8"
                        broll_hud_ops.append(
                            f"drawtext={font_reg}text='{safe_mood}':fontcolor={mood_col}:fontsize=13:"
                            f"x=1218-text_w:y=74:enable='between(t\\,{c_start:.2f}\\,{c_end:.2f})'"
                        )

                video_fc = (
                    f"[2:v]scale=1280:720,fps=30,tpad=stop_mode=clone:stop_duration=1.0,"
                    f"trim=duration={total_dur:.2f},setpts=PTS-STARTPTS[bg0];"
                    f"color=c=0x38BDF8:s=1280x6:r=30:d={total_dur:.2f}[pbar];"
                    f"[0:a]aresample=24000,aformat=sample_rates=24000:channel_layouts=stereo,"
                    f"volume=1.45,apad=whole_dur={total_dur:.2f},atrim=0:{total_dur:.2f},"
                    f"showwaves=s=420x38:mode=cline:draw=full:rate=30:scale=lin:"
                    f"colors=0x38BDF8@0.85|0xF59E0B@0.75,format=rgba,"
                    f"colorkey=0x000000:0.04:0.08,colorchannelmixer=aa=0.84[wave];"
                    f"[bg0]{','.join(broll_hud_ops)}[hud];"
                    f"[hud][wave]overlay=x=430:y=500:shortest=1[vwave];"
                    f"[vwave][pbar]overlay=x='-1280+1280*(t/{total_dur:.2f})':y=714:shortest=1[vp];"
                    f"{sub_stage}"
                )
                video_cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(voice_audio_path),
                    "-i",
                    str(staging_master_audio),
                    "-i",
                    str(broll_track),
                    "-filter_complex",
                    video_fc,
                    "-map",
                    "[vout]",
                    "-map",
                    "1:a:0",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-preset",
                    "ultrafast",
                    "-r",
                    "30",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-ar",
                    "44100",
                    "-t",
                    f"{total_dur:.2f}",
                    "-movflags",
                    "+faststart",
                    str(staging_video),
                ]
            else:
                # -----------------------------------------------------------------
                # CLASSIC v5.0 STUDIO WAVEFORM CANVAS (when scene_visuals is None)
                # -----------------------------------------------------------------
                hud_ops: List[str] = [
                    "drawbox=x=0:y=0:w=1280:h=4:color=0x38BDF8@0.90:t=fill",
                    "drawbox=x=42:y=16:w=1196:h=684:color=0x111827@0.38:t=fill",
                    "drawbox=x=84:y=179:w=1112:h=342:color=0x38BDF8@0.07:t=fill",
                ]

                if has_turnaround_hud:
                    hud_ops.extend(
                        [
                            f"drawbox=x=0:y=0:w=1280:h=5:color=0xF59E0B@0.96:t=fill{tr_enable}",
                            f"drawbox=x=84:y=179:w=1112:h=342:color=0xF59E0B@0.14:t=fill{tr_enable}",
                        ]
                    )

                hud_ops.extend(
                    [
                        "drawbox=x=56:y=28:w=1168:h=54:color=0x111827@0.95:t=fill",
                        "drawbox=x=56:y=28:w=1168:h=54:color=0x1E293B@0.95:t=1",
                        "drawbox=x=56:y=28:w=5:h=54:color=0x38BDF8@1.0:t=fill",
                        "drawbox=x=74:y=38:w=164:h=34:color=0x1E293B@0.96:t=fill",
                        f"drawtext={font_bold}text='PODCAST STUDIO':fontcolor=0x38BDF8:fontsize=14:x=90:y=48",
                        f"drawtext={font_bold}text='{safe_title}':fontcolor=0xF9FAFB:fontsize=20:x=254:y=44",
                        "drawbox=x=924:y=36:w=286:h=38:color=0x0F172A@0.95:t=fill",
                        "drawbox=x=1206:y=36:w=4:h=38:color=0x38BDF8@1.0:t=fill",
                        f"drawtext={font_bold}text='{safe_speaker}':fontcolor=0x93C5FD:fontsize=15:x=1194-text_w:y=47",
                    ]
                )
                if has_turnaround_hud:
                    hud_ops.extend(
                        [
                            f"drawbox=x=56:y=28:w=5:h=54:color=0xF59E0B@1.0:t=fill{tr_enable}",
                            f"drawtext={font_bold}text='PODCAST STUDIO':fontcolor=0xFCD34D:fontsize=14:x=90:y=48{tr_enable}",
                            f"drawbox=x=1206:y=36:w=4:h=38:color=0x10B981@1.0:t=fill{tr_enable}",
                        ]
                    )

                hud_ops.extend(
                    [
                        "drawbox=x=56:y=96:w=1168:h=52:color=0x0E1628@0.92:t=fill",
                        "drawbox=x=56:y=96:w=1168:h=52:color=0x1E293B@0.90:t=1",
                        "drawbox=x=56:y=96:w=4:h=52:color=0x38BDF8@0.95:t=fill",
                    ]
                )
                if has_turnaround_hud:
                    hud_ops.append(f"drawbox=x=56:y=96:w=4:h=52:color=0x10B981@0.95:t=fill{tr_enable}")

                for idx, ch in enumerate(effective_chapters, start=1):
                    ch_raw = " ".join(str(ch.get("title") or f"Phần {idx}").strip().split())
                    if len(ch_raw) > 62:
                        ch_raw = f"{ch_raw[:60].rstrip()}…"
                    c_start = max(0.0, float(ch.get("start_time", 0.0) or 0.0))
                    c_end = max(c_start + 0.1, float(ch.get("end_time", total_dur) or total_dur))
                    if idx == len(effective_chapters):
                        c_end = max(c_end, total_dur + 0.25)
                    ch_label = self._escape_drawtext(f"CHƯƠNG {idx:02d}  •  {ch_raw}")
                    hud_ops.append(
                        f"drawtext={font_bold}text='{ch_label}':fontcolor=0xE2E8F0:fontsize=18:"
                        f"x=78:y=112:enable='between(t\\,{c_start:.2f}\\,{c_end:.2f})'"
                    )
                    mood_raw = " ".join(str(ch.get("mood") or "").strip().split()).upper()
                    if mood_raw:
                        safe_mood = self._escape_drawtext(mood_raw[:24])
                        hud_ops.append(
                            f"drawtext={font_reg}text='{safe_mood}':fontcolor=0x38BDF8:fontsize=14:"
                            f"x=1204-text_w:y=115:enable='between(t\\,{c_start:.2f}\\,{c_end:.2f})'"
                        )

                hud_ops.extend(
                    [
                        "drawbox=x=90:y=185:w=1100:h=330:color=0x0E1422@0.94:t=fill",
                        "drawbox=x=90:y=185:w=1100:h=330:color=0x1E293B@0.95:t=2",
                        "drawbox=x=90:y=185:w=1100:h=3:color=0x38BDF8@0.92:t=fill",
                        "drawbox=x=130:y=350:w=1020:h=1:color=0x334155@0.55:t=fill",
                        f"drawtext={font_reg}text='LIVE VOICE WAVEFORM  •  24kHz BROADCAST MASTER':fontcolor=0x64748B:fontsize=13:x=118:y=204",
                    ]
                )
                if has_turnaround_hud:
                    hud_ops.append(f"drawbox=x=90:y=185:w=1100:h=3:color=0xF59E0B@0.96:t=fill{tr_enable}")

                hud_ops.extend(
                    [
                        "drawbox=x=64:y=542:w=1152:h=144:color=0x0B0F19@0.90:t=fill",
                        "drawbox=x=64:y=542:w=1152:h=144:color=0x1E293B@0.92:t=1",
                        "drawbox=x=64:y=542:w=1152:h=3:color=0x38BDF8@0.88:t=fill",
                        "drawbox=x=0:y=712:w=1280:h=8:color=0x1E293B@0.92:t=fill",
                    ]
                )
                if has_turnaround_hud:
                    hud_ops.append(f"drawbox=x=64:y=542:w=1152:h=3:color=0x10B981@0.95:t=fill{tr_enable}")

                video_fc = (
                    f"color=c=0x090D16:s=1280x720:r=30:d={total_dur:.2f}[bg0];"
                    f"color=c=0x38BDF8:s=1280x8:r=30:d={total_dur:.2f}[pbar];"
                    f"[0:a]aresample=24000,aformat=sample_rates=24000:channel_layouts=stereo,"
                    f"volume=2.2,apad=whole_dur={total_dur:.2f},atrim=0:{total_dur:.2f},"
                    f"showwaves=s=1020x210:mode=cline:draw=full:rate=30:scale=sqrt:"
                    f"colors=0x38BDF8@0.92|0x60A5FA@0.75,format=rgb24,colorkey=0x000000:0.03:0.05[wave];"
                    f"[bg0]{','.join(hud_ops)}[hud];"
                    f"[hud][wave]overlay=x=130:y=245:shortest=1[vwave];"
                    f"[vwave][pbar]overlay=x='-1280+1280*(t/{total_dur:.2f})':y=712:shortest=1[vp];"
                    f"{sub_stage}"
                )
                video_cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(voice_audio_path),
                    "-i",
                    str(staging_master_audio),
                    "-filter_complex",
                    video_fc,
                    "-map",
                    "[vout]",
                    "-map",
                    "1:a:0",
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    "-preset",
                    "ultrafast",
                    "-r",
                    "30",
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-ar",
                    "44100",
                    "-t",
                    f"{total_dur:.2f}",
                    "-movflags",
                    "+faststart",
                    str(staging_video),
                ]

            res_vid = subprocess.run(video_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res_vid.returncode != 0:
                raise RuntimeError(
                    f"FFmpeg podcast video render failed (code {res_vid.returncode}): {res_vid.stderr[-600:]}"
                )

            final_file = self._safe_finalize_output(staging_video, output_path)
            self._write_ass(subtitles, final_file.with_suffix(".ass"), width=1280, height=720)
            self._write_srt(subtitles, final_file.with_suffix(".srt"))
            self._write_vtt(subtitles, final_file.with_suffix(".vtt"))
            return final_file
        finally:
            for temp_f in (staging_master_audio, staging_ass, *extra_temp_files):
                if temp_f.exists():
                    try:
                        temp_f.unlink()
                    except OSError:
                        pass

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
