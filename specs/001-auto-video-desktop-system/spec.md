# Feature Specification: KinetixAI (FlowVids-AI) Automated Video Production & Desktop Studio

**Feature Branch**: `001-auto-video-desktop-system`

**Created**: 2026-11-13

**Status**: Approved

**Input**: User description: "Xây dựng hệ thống tự động sản xuất video và ứng dụng Desktop App: Nhận đầu vào là URL video mẫu, file video nội bộ, hoặc kịch bản văn bản. Hệ thống dùng yt-dlp tải video, FFmpeg tách âm thanh, Whisper nhận diện giọng nói ra phụ đề JSON có timestamps. Cho phép người dùng chọn Engine dựng hình là Remotion (React) hoặc HyperFrames (HTML/GSAP) để render lớp đồ họa chuyển động và phụ đề. Cuối cùng dùng FFmpeg ghép các lớp lại và xuất ra file MP4 hoàn chỉnh."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - End-to-End Automated Video Production Pipeline (Priority: P1)

As a video creator or automation operator, I want to provide a source video URL, local video file, or text script along with a chosen visual render engine (Remotion or HyperFrames) so that the system automatically downloads/ingests the media, extracts audio, transcribes timestamped subtitles, renders animated captions/motion graphics, and merges everything into a final MP4 video.

**Why this priority**: This is the core value proposition of KinetixAI—automating the 5-step media production workflow from raw input to final MP4 output without manual editing.

**Independent Test**: Can be fully tested by executing the pipeline with a sample video URL or local sample video/script, verifying that audio extraction, subtitle generation, visual overlay rendering, and final MP4 compositing all complete and produce a playable MP4 file with burned-in/composited animated subtitles.

**Acceptance Scenarios**:

1. **Given** a valid video source URL (or local sample video) and a selected visual engine (`remotion` or `hyperframes`), **When** the user triggers the automated pipeline, **Then** the system downloads/ingests the video, extracts a WAV audio file, transcribes timestamped `SubtitleSegment` items, renders the caption overlay composition, and exports `[project_id]_final.mp4`.
2. **Given** a video with spoken audio or a provided script, **When** transcription finishes, **Then** each `SubtitleSegment` contains accurate `start_time` (seconds), `end_time` (seconds), `text`, and optional word-level timing metadata serialized as a clean JSON data contract.

---

### User Story 2 - Dynamic Visual Render Engine Switching (Remotion vs HyperFrames) (Priority: P2)

As a video producer, I want to seamlessly switch between **Remotion** (reusable React component templates) and **HyperFrames** (lightweight HTML/CSS/GSAP deterministic compositions) for rendering subtitle animations and motion graphics overlays without changing any pipeline workflow settings.

**Why this priority**: Different production workflows require either structured React templates (Remotion) or fast, AI-friendly HTML/GSAP motion compositions (HyperFrames). Seamless switching is a key architectural requirement.

**Independent Test**: Can be tested independently by invoking the visual rendering step with identical subtitle JSON props under both `RenderEngineType.REMOTION` and `RenderEngineType.HYPERFRAMES` and verifying both produce valid video overlays ready for compositing.

**Acceptance Scenarios**:

1. **Given** a list of `SubtitleSegment` objects and template configuration (`CaptionTemplate`), **When** `RenderEngineType.REMOTION` is selected, **Then** the system renders the React-based composition into an overlay video file.
2. **Given** the same list of `SubtitleSegment` objects and template configuration, **When** `RenderEngineType.HYPERFRAMES` is selected, **Then** the system renders the HTML/CSS/GSAP composition into an overlay video file using the same interface contract.

---

### User Story 3 - Native Windows Desktop App & REST API Control Studio (Priority: P3)

As a desktop user on Windows, I want a modern Desktop Application (and companion web/dashboard view) that connects to the core orchestration backend so I can create projects, choose between URL/local file/script input, select Remotion or HyperFrames, choose the Whisper model size, monitor real-time step-by-step progress, inspect/edit generated subtitles, and preview/open the final exported MP4 video.

**Why this priority**: Delivers the complete end-user Desktop experience requested by the user while keeping all business logic cleanly separated in the backend orchestrator.

**Independent Test**: Can be tested by launching the Backend API and the Windows Desktop Client, submitting a render job from the UI, observing real-time pipeline status updates, viewing generated subtitles in the UI, and verifying the output MP4 path is accessible.

**Acceptance Scenarios**:

1. **Given** the KinetixAI Desktop App is open, **When** the user enters a project name, source URL (or selects local sample/demo mode), selects `Remotion` or `HyperFrames`, and clicks "Start Production", **Then** the UI submits the job to the backend API, displays step-by-step progress (Download -> Extract Audio -> Transcribe -> Render Visuals -> Merge MP4), and shows the completed output file and subtitle timeline.
2. **Given** a completed or in-progress project, **When** the user views the project details in the Desktop App, **Then** all generated subtitle segments with start/end timestamps and output file paths are displayed clearly.

---

### Edge Cases

- What happens when an invalid or unreachable URL is provided to the downloader? The system catches the adapter error, records a descriptive failure state on the job, and reports an actionable message to the user without crashing the service.
- How does the system handle environments where a user wants to test the pipeline immediately without downloading a large external video or multi-gigabyte Whisper weight? The system supports both real online/model execution and a built-in local sample video generator + fallback/synthetic transcription mode so offline/instant verification works out-of-the-box.
- What happens when the source video has no audio stream? The video processor detects the missing audio stream (or generates a silent track / uses script subtitles if provided) and surfaces a clear warning.
- How does the system avoid slow frame-by-frame decoding of huge raw videos inside the headless browser? The visual renderers render lightweight overlay compositions (or chroma/alpha overlays) which the video processor composites over the source video stream.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a clean domain model including `RenderEngineType` (`remotion`, `hyperframes`), `SubtitleSegment` (`start_time`, `end_time`, `text`, optional `words`), `MediaAsset`, `RenderJob`, and `VideoProject`.
- **FR-002**: System MUST define strict abstract interfaces (`IMediaDownloader`, `ITranscriber`, `IVisualRenderer`, `IVideoProcessor`) so domain and application logic remain 100% decoupled from third-party libraries.
- **FR-003**: System MUST implement `YtDlpAdapter` (`IMediaDownloader`) capable of downloading video from URLs into a workspace directory, while also supporting local video file ingestion or sample video generation for offline testing.
- **FR-004**: System MUST implement `FfmpegAdapter` (`IVideoProcessor`) capable of extracting WAV audio (`16kHz` mono optimal for speech recognition) from a source video and compositing/merging the visual overlay with the base video into a final MP4 output.
- **FR-005**: System MUST implement `WhisperAdapter` (`ITranscriber`) supporting speech-to-text transcription (via `faster-whisper` or `openai-whisper`, with graceful fallback when running in lightweight/script mode) returning timestamped `SubtitleSegment` collections.
- **FR-006**: System MUST implement `RemotionAdapter` and `HyperFramesAdapter` (`IVisualRenderer`) plus `RendererFactory` to dynamically select and execute the requested visual render engine using a standardized JSON props contract.
- **FR-007**: System MUST implement `AutoVideoPipeline` to orchestrate the 5-step workflow (Download -> Extract Audio -> Transcribe -> Render Composition -> Merge & Export) and track progress states.
- **FR-008**: System MUST expose a REST API server (health check, project creation, pipeline execution, job status polling, subtitle inspection, and demo sample generation) and a CLI entry point.
- **FR-009**: System MUST provide a Windows Desktop Application (native C# .NET WPF Desktop App plus Streamlit/Desktop UI) that communicates with the core backend to configure, run, monitor, and inspect video automation jobs.

### Key Entities

- **VideoProject**: Represents an end-to-end video automation project (`project_id`, `source_url`, `raw_video_path`, `audio_path`, `subtitles`, `final_output_path`, `engine_type`, `template_id`, `status`).
- **SubtitleSegment**: Represents a timed caption segment (`start_time`, `end_time`, `text`, `words`).
- **MediaAsset**: Metadata for downloaded or intermediate media files (`asset_id`, `file_path`, `media_type`, `duration_seconds`, `resolution`).
- **RenderJob**: Tracks pipeline execution state (`job_id`, `project_id`, `current_step`, `progress_percent`, `status`, `error_message`, `created_at`, `completed_at`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can execute a complete 5-step video production run (from input video/URL to final composited MP4 with animated subtitles) in a single click from the Desktop App or a single CLI/API call.
- **SC-002**: Switching between `Remotion` and `HyperFrames` requires only changing the `engine_type` parameter (`remotion` vs `hyperframes`) with zero changes to pipeline orchestration code.
- **SC-003**: 100% of core domain entities, factories, pipeline steps, adapters, and REST API endpoints are verified by automated unit and integration tests passing with zero failures.
- **SC-004**: Both the Python Core Backend and the Windows C# WPF Desktop Application build and launch cleanly with zero compilation or runtime errors.

## Assumptions

- Local machine has Python 3.11+, `uv`, Node.js 20+, `ffmpeg` in PATH, and .NET SDK for building the Windows WPF desktop client.
- To ensure deterministic, fast testing and offline usability alongside full internet/GPU execution, the system provides a built-in sample media generator (via FFmpeg testsrc + synthesized speech/tone or user-supplied script) in addition to live `yt-dlp` URL downloading and `faster-whisper`/`openai-whisper` model inference.
