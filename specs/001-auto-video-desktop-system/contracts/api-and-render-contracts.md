# Interface & API Contracts: KinetixAI (FlowVids-AI)

## 1. Domain Abstract Base Class (ABC) Contracts (`src/domain/interfaces/`)

```python
class IMediaDownloader(ABC):
    @abstractmethod
    def download(self, url: str, output_dir: Path) -> Path:
        """Download source video from URL or ingest local/demo video into output_dir."""
        pass

class ITranscriber(ABC):
    @abstractmethod
    def transcribe(self, audio_path: Path, script_hint: str | None = None) -> List[SubtitleSegment]:
        """Transcribe audio file into timestamped SubtitleSegment items."""
        pass

class IVisualRenderer(ABC):
    @abstractmethod
    def render_composition(self, template_id: str, props: Dict[str, Any], output_path: Path) -> Path:
        """Render visual composition (Remotion React or HyperFrames HTML/GSAP) to output_path."""
        pass

class IVideoProcessor(ABC):
    @abstractmethod
    def extract_audio(self, video_path: Path, output_audio: Path) -> Path:
        """Extract 16kHz mono WAV audio from video_path."""
        pass

    @abstractmethod
    def merge_and_export(
        self,
        base_video: Path,
        overlay_video: Path,
        output_path: Path,
        subtitles: List[SubtitleSegment] | None = None,
    ) -> Path:
        """Composite overlay_video and subtitles onto base_video and export final MP4."""
        pass
```

## 2. Python <-> Node.js Visual Renderer JSON Props Contract

Passed via CLI `--props` (or temporary JSON file path) to `RemotionAdapter` and `HyperFramesAdapter`:

```json
{
  "template_id": "CaptionTemplate",
  "project_id": "proj_001",
  "width": 1280,
  "height": 720,
  "fps": 30,
  "duration_in_seconds": 6.0,
  "theme": {
    "primary_color": "#00F5D4",
    "accent_color": "#7B2CBF",
    "font_family": "Inter, Segoe UI, sans-serif"
  },
  "subtitles": [
    {
      "start_time": 0.0,
      "end_time": 2.0,
      "text": "KinetixAI Clean Architecture Studio"
    },
    {
      "start_time": 2.0,
      "end_time": 4.0,
      "text": "Powered by Remotion, HyperFrames & FFmpeg"
    },
    {
      "start_time": 4.0,
      "end_time": 6.0,
      "text": "Spec-Driven Development with GitHub Spec Kit"
    }
  ]
}
```

## 3. FastAPI REST Contract (`http://127.0.0.1:8000`)

### `GET /api/v1/health`
Returns server status and detected tool versions (`ffmpeg`, `node`, `yt-dlp`, `whisper`, `remotion`, `hyperframes`).

### `POST /api/v1/projects`
Creates and optionally executes a `VideoProject` pipeline run.
- **Request Body (`CreateProjectRequest`)**:
  ```json
  {
    "project_id": "demo_remotion_01",
    "source_url": "demo://sample",
    "engine_type": "remotion",
    "template_id": "CaptionTemplate",
    "script_text": "Welcome to KinetixAI automated video studio.|Built with Clean Architecture and SOLID principles.|Rendered with Remotion, HyperFrames, Whisper and FFmpeg.",
    "run_async": false
  }
  ```
- **Response (`ProjectResponse`)**: Full project state including `raw_video_path`, `audio_path`, `overlay_video_path`, `final_output_path`, `subtitles`, `status`, and `progress_percent`.

### `GET /api/v1/projects`
Lists all projects in the workspace.

### `GET /api/v1/projects/{project_id}`
Returns real-time status, progress percentage, paths, and generated subtitles for a specific project.

### `POST /api/v1/projects/{project_id}/Subtitles`
Updates subtitle segments and re-renders the visual overlay + final MP4.
