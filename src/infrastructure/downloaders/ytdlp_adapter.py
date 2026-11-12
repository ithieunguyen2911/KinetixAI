"""YtDlpAdapter - Infrastructure Adapter wrapping yt-dlp/yt-dlp with metadata inspection, time-range clipping, and spoken sample generation."""

from pathlib import Path
import shutil
import subprocess
from typing import Any, Callable, Dict

from src.domain.interfaces.media_downloader import IMediaDownloader


class YtDlpAdapter(IMediaDownloader):
    """Adapter encapsulating yt-dlp Python OOP API for downloading video/audio, metadata extraction, and spoken sample synthesis."""

    def __init__(
        self,
        format_selector: str = "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best",
        write_subtitles: bool = False,
        progress_callback: Callable[[Dict[str, Any]], None] | None = None,
    ) -> None:
        self.format_selector = format_selector
        self.write_subtitles = write_subtitles
        self.progress_callback = progress_callback

    def extract_metadata(self, url: str) -> Dict[str, Any]:
        """Inspect remote URL or local media metadata without downloading the full stream."""
        normalized = url.strip()
        if normalized.startswith("demo://") or normalized.lower() == "sample":
            return {
                "id": "demo_sample",
                "title": "KinetixAI Spoken Sample Broadcast",
                "duration": 6.0,
                "uploader": "KinetixAI Studio",
                "resolution": "1280x720",
                "fps": 30,
                "source_type": "demo",
            }

        local_candidate = Path(normalized.removeprefix("file://"))
        if local_candidate.exists() and local_candidate.is_file():
            return {
                "id": local_candidate.stem,
                "title": local_candidate.name,
                "duration": 0.0,
                "uploader": "Local File",
                "resolution": "local",
                "source_type": "file",
                "file_path": str(local_candidate.resolve()),
            }

        import yt_dlp

        ydl_opts: Dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(normalized, download=False)
            return {
                "id": info.get("id", "unknown"),
                "title": info.get("title", "Untitled"),
                "duration": float(info.get("duration") or 0.0),
                "uploader": info.get("uploader", "Unknown"),
                "resolution": f"{info.get('width', 1280)}x{info.get('height', 720)}",
                "fps": info.get("fps", 30),
                "webpage_url": info.get("webpage_url", normalized),
                "source_type": "yt-dlp",
            }

    def download(
        self,
        url: str,
        output_dir: Path,
        start_time: float | None = None,
        end_time: float | None = None,
    ) -> Path:
        """Download video from URL via yt-dlp, ingest local file, or synthesize a spoken sample video."""
        output_dir.mkdir(parents=True, exist_ok=True)
        normalized = url.strip()

        # 1. Built-in spoken sample video generator (uses Windows SpeechSynthesizer + FFmpeg HD test broadcast)
        if normalized.startswith("demo://") or normalized.lower() == "sample":
            target = output_dir / "demo_sample_raw.mp4"
            self._generate_demo_video(target, duration_seconds=6)
            return target

        # 2. Local file path ingestion
        local_candidate = Path(normalized.removeprefix("file://"))
        if local_candidate.exists() and local_candidate.is_file():
            target = output_dir / f"local_{local_candidate.name}"
            if local_candidate.resolve() != target.resolve():
                shutil.copy2(local_candidate, target)
            return target

        # 3. Live remote URL download via yt-dlp Python OOP API
        import yt_dlp

        hooks = []
        if self.progress_callback:
            hooks.append(self.progress_callback)

        ydl_opts: Dict[str, Any] = {
            "outtmpl": str(output_dir / "%(id)s.%(ext)s"),
            "format": self.format_selector,
            "merge_output_format": "mp4",
            "writesubtitles": self.write_subtitles,
            "writeautomaticsub": self.write_subtitles,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": hooks,
        }

        if start_time is not None and end_time is not None and end_time > start_time:
            from yt_dlp.utils import download_range_func

            ydl_opts["download_ranges"] = download_range_func(None, [(start_time, end_time)])
            ydl_opts["force_keyframes_at_cuts"] = True

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(normalized, download=True)
            prepared = Path(ydl.prepare_filename(info))
            mp4_candidate = prepared.with_suffix(".mp4")
            if mp4_candidate.exists():
                return mp4_candidate
            return prepared

    @staticmethod
    def _generate_demo_video(output_path: Path, duration_seconds: int = 6) -> Path:
        """Generate a 1280x720 30fps studio reference video with real synthesized speech audio."""
        speech_wav = output_path.parent / "demo_synthesized_speech.wav"
        spoken_ok = False

        # Attempt to synthesize real human speech via Windows System.Speech so Whisper can transcribe actual voice
        try:
            ps_script = (
                "Add-Type -AssemblyName System.Speech; "
                "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$synth.SetOutputToWaveFile('{str(speech_wav)}'); "
                "$synth.Rate = 0; "
                "$synth.Speak('Kinetix Studio automated video pipeline. Powered by Remotion, HyperFrames, Whisper, and FFmpeg.'); "
                "$synth.Dispose();"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=8,
            )
            if res.returncode == 0 and speech_wav.exists() and speech_wav.stat().st_size > 2000:
                spoken_ok = True
        except Exception:
            spoken_ok = False

        if spoken_ok:
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"testsrc2=size=1280x720:rate=30:duration={duration_seconds}",
                "-i",
                str(speech_wav),
                "-filter_complex",
                f"[1:a]apad=whole_dur={duration_seconds}[aout]",
                "-map",
                "0:v:0",
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
                str(duration_seconds),
                str(output_path),
            ]
        else:
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"testsrc2=size=1280x720:rate=30:duration={duration_seconds}",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency=440:sample_rate=16000:duration={duration_seconds}",
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
        return output_path
