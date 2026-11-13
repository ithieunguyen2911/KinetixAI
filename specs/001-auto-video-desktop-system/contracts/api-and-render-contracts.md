# Interface & API Contracts: KinetixAI (FlowVids-AI) v2.0 Professional NLE

## 1. Domain Abstract Base Class (ABC) Contracts (`src/domain/interfaces/`)

```python
class IMediaDownloader(ABC):
    @abstractmethod
    def download(
        self,
        url: str,
        output_dir: Path,
        start_time: float | None = None,
        end_time: float | None = None,
    ) -> Path:
        """Download source video from URL or ingest local/demo video into output_dir."""
        pass

    def extract_metadata(self, url: str) -> Dict[str, Any]:
        """Inspect remote URL or local media metadata without downloading the full stream."""
        pass


class ITranscriber(ABC):
    @abstractmethod
    def transcribe(self, audio_path: Path, script_hint: str | None = None) -> List[SubtitleSegment]:
        """Transcribe audio file into timestamped SubtitleSegment items with word-level timing."""
        pass


class IVisualRenderer(ABC):
    @abstractmethod
    def render_composition(self, template_id: str, props: Dict[str, Any], output_path: Path) -> Path:
        """Render visual composition (Remotion React or HyperFrames HTML/GSAP) to output_path."""
        pass


class IVideoProcessor(ABC):
    @abstractmethod
    def extract_audio(self, video_path: Path, output_audio: Path) -> Path:
        """Extract 16kHz mono speech-bandpass WAV audio from video_path."""
        pass

    @abstractmethod
    def merge_and_export(
        self,
        base_video: Path,
        overlay_video: Path,
        output_path: Path,
        subtitles: List[SubtitleSegment] | None = None,
    ) -> Path:
        """Composite overlay_video and subtitles onto base_video and export final MP4 + SRT + VTT."""
        pass

    def probe_media(self, media_path: Path) -> Dict[str, Any]: ...
    def trim_video(self, video_path: Path, output_path: Path, start_time: float, end_time: float) -> Path: ...
    def split_video(self, video_path: Path, split_time: float, output_dir: Path) -> List[Path]: ...
    def concat_clips(self, clip_paths: List[Path], output_path: Path, transition: str = "fade") -> Path: ...
    def change_speed(self, video_path: Path, output_path: Path, speed_factor: float) -> Path: ...
    def apply_color_grade(
        self,
        video_path: Path,
        output_path: Path,
        preset: str = "natural",
        brightness: float = 0.0,
        contrast: float = 1.0,
        saturation: float = 1.0,
        gamma: float = 1.0,
    ) -> Path: ...
    def reframe_aspect_ratio(self, video_path: Path, output_path: Path, aspect_ratio: str = "16:9") -> Path: ...
    def remove_silences(self, video_path: Path, output_path: Path, threshold_db: float = -35.0) -> Path: ...
    def normalize_audio(self, video_path: Path, output_path: Path) -> Path: ...
    def mix_audio_tracks(self, video_path: Path, background_audio_path: Path, output_path: Path, bg_volume: float = 0.20) -> Path: ...
    def capture_snapshot(self, video_path: Path, timestamp_sec: float, output_image_path: Path) -> Path: ...
```

---

## 2. FastAPI REST Endpoints Contract (`http://127.0.0.1:8000`)

| Method | Endpoint | Purpose | Request Schema |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Check system & 5 tools readiness | — |
| `POST` | `/api/v1/sources/inspect` | Pre-inspect URL/file via `yt-dlp` / `ffprobe` | `InspectSourceRequest` |
| `GET` | `/api/v1/projects` | List all workspace projects | — |
| `POST` | `/api/v1/projects` | Create & run 5-step automated pipeline | `CreateProjectRequest` |
| `GET` | `/api/v1/projects/{id}` | Get project details & subtitle cues | — |
| `GET` | `/api/v1/projects/{id}/probe` | Inspect stream technical metadata (`ffprobe`) | — |
| `POST` | `/api/v1/projects/{id}/subtitles` | Edit subtitle cues, sync words & re-render overlay | `UpdateSubtitlesRequest` |
| `POST` | `/api/v1/projects/{id}/trim` | Non-linear In/Out trim (`FFmpeg`) | `TrimVideoRequest` |
| `POST` | `/api/v1/projects/{id}/speed` | Speed ramping (`0.25x`–`4.0x` via `setpts`+`atempo`) | `SpeedChangeRequest` |
| `POST` | `/api/v1/projects/{id}/color-grade` | Apply LUT/Color Look preset + `eq` parameters | `ColorGradeRequest` |
| `POST` | `/api/v1/projects/{id}/reframe` | Convert aspect ratio (`16:9`, `9:16` Shorts, `1:1`) | `ReframeRequest` |
| `POST` | `/api/v1/projects/{id}/audio-master` | Apply EBU R128 loudness normalization / silence removal / BGM mix | `AudioMasterRequest` |
| `POST` | `/api/v1/projects/{id}/snapshot` | Capture PNG frame snapshot at playhead timestamp | `SnapshotRequest` |
| `GET` | `/api/v1/projects/{id}/video` | Stream/download final master MP4 | — |
| `POST` | `/api/v1/mcp/command` | Execute natural-language or structured AI MCP command | `AiMcpCommandRequest` |
| `GET` | `/api/v1/mcp/tools` | List all registered `kinetix-ai` MCP tools | — |
