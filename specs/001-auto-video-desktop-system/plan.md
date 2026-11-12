# Implementation Plan: KinetixAI (FlowVids-AI) Automated Video Production, Desktop Studio & Antigravity MCP

**Branch**: `001-auto-video-desktop-system` | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-auto-video-desktop-system/spec.md`

---

## 1. Danh Sách Toàn Bộ Tính Năng Hiện Có (Feature Inventory)

Hệ thống **KinetixAI (FlowVids-AI)** bao gồm **7 phân hệ (28 tính năng cụ thể)** kết hợp 5 công cụ GitHub (`yt-dlp`, `Whisper`, `HyperFrames`, `Remotion`, `FFmpeg`) cùng **GitHub Spec Kit** và **Antigravity MCP**:

| Mã Tính Năng | Phân Hệ / Layer | Tên Tính Năng | File Thực Thi Chính | Trạng Thái Kiểm Định |
| :--- | :--- | :--- | :--- | :--- |
| **F1.1** | `yt-dlp` (`IMediaDownloader`) | Tải video/audio từ URL thực tế với bộ lọc format MP4/M4A <= 1080p & progress hook | `src/infrastructure/downloaders/ytdlp_adapter.py` | Đã có & hoạt động |
| **F1.2** | `yt-dlp` (`IMediaDownloader`) | Cắt phân đoạn video trực tiếp khi tải (`download_ranges`: `start_time`..`end_time`) | `src/infrastructure/downloaders/ytdlp_adapter.py` | Đã có & hoạt động |
| **F1.3** | `yt-dlp` (`IMediaDownloader`) | Nhập (Ingest) trực tiếp file video nội bộ từ ổ cứng (`C:\...` hoặc `file://`) | `src/infrastructure/downloaders/ytdlp_adapter.py` | Đã có & hoạt động |
| **F1.4** | `yt-dlp` (`IMediaDownloader`) | Tạo video phát sóng mẫu `demo://sample` có **giọng nói tiếng Anh thực tế** (`SpeechSynthesizer` + FFmpeg HD 720p) | `src/infrastructure/downloaders/ytdlp_adapter.py` | Đã có & hoạt động |
| **F1.5** | `yt-dlp` (`IMediaDownloader`) | Trích xuất Metadata nguồn video trước khi tải (`extract_metadata`: title, resolution, fps, duration) | `src/infrastructure/downloaders/ytdlp_adapter.py` | Cần nối thêm API `/api/v1/sources/inspect` & nút UI |
| **F2.1** | `FFmpeg` (`IVideoProcessor`) | Phân tích thông số kỹ thuật luồng video/audio bằng `ffprobe` (`probe_media`: codec, FPS, Hz, size, duration) | `src/infrastructure/processors/ffmpeg_adapter.py` | Đã có & hoạt động |
| **F2.2** | `FFmpeg` (`IVideoProcessor`) | Tách âm thanh WAV 16kHz Mono chuẩn Whisper kèm bộ lọc thoại `highpass=f=80,lowpass=f=7600` (`extract_audio`) | `src/infrastructure/processors/ffmpeg_adapter.py` | Đã có & hoạt động |
| **F2.3** | `FFmpeg` (`IVideoProcessor`) | Cắt ngắn (Trim) video thành phẩm không cần render lại (`trim_video`) + chống khóa file Windows | `src/infrastructure/processors/ffmpeg_adapter.py` | Cần bổ sung cơ chế chống khóa file khi đang phát trên WPF |
| **F2.4** | `FFmpeg` (`IVideoProcessor`) | Trộn đa luồng âm thanh (Audio Ducking / Mixing giọng đọc + nhạc nền `mix_audio_tracks`) | `src/infrastructure/processors/ffmpeg_adapter.py` | Cần khai báo vào `IVideoProcessor` ABC |
| **F2.5** | `FFmpeg` (`IVideoProcessor`) | Ghép lớp phủ đồ họa chuyển động (`colorkey` overlay compositing) + xuất phụ đề kép `.srt` & `.vtt` (`merge_and_export`) | `src/infrastructure/processors/ffmpeg_adapter.py` | Đã có & hoạt động |
| **F3.1** | `Whisper` (`ITranscriber`) | Nhận diện giọng nói AI (`faster-whisper` với `vad_filter=True`, `word_timestamps=True` & `openai-whisper`) | `src/infrastructure/transcribers/whisper_adapter.py` | Đã có & hoạt động |
| **F3.2** | `Whisper` (`ITranscriber`) | Nhận diện giọng nói Offline tức thì trên Windows (`System.Speech.Recognition`) khi để trống Script và chưa tải model nặng | `src/infrastructure/transcribers/whisper_adapter.py` | Cần nâng cấp để tự động nghe file WAV khi để trống Script |
| **F3.3** | `Whisper` (`ITranscriber`) | Căn chỉnh phụ đề theo kịch bản (`_align_script_to_duration`) kèm tính toán `WordTimestamp` từng từ | `src/infrastructure/transcribers/whisper_adapter.py` | Cần tự động đồng bộ lại `words` khi người dùng sửa chữ trên UI |
| **F3.4** | `Whisper` (`ITranscriber`) | Xuất file `.transcript.json` chuẩn HyperFrames (`words: [{id, text, start, end}]`) | `src/infrastructure/transcribers/whisper_adapter.py` | Đã có & hoạt động |
| **F4.1** | `Application` (`RendererFactory`) | Chuyển đổi linh hoạt giữa `RemotionAdapter` và `HyperFramesAdapter` qua `RenderEngineType` | `src/application/factories/renderer_factory.py` | Đã có & hoạt động |
| **F4.2** | `Remotion` (`IVisualRenderer`) | Dựng đồ họa React/TypeScript (`CaptionTemplate.tsx` dùng `<Sequence>`, `spring()`, tô sáng từng từ Karaoke) | `render_engines/remotion_engine/` | Cần đồng bộ `duration_seconds` theo thời lượng thực của video gốc |
| **F4.3** | `HyperFrames` (`IVisualRenderer`) | Sinh HTML composition chuẩn 12-Rule HyperFrames Contract (`index.html` + `compositions/captions.html`, `<template>`, `class="clip"`, `gsap.fromTo`, `window.__timelines`) | `render_engines/hyperframes_engine/` | Cần đồng bộ `duration_seconds` theo thời lượng thực của video gốc |
| **F5.1** | `Application` (`AutoVideoPipeline`) | Điều phối luồng 5 bước tự động qua Dependency Injection kèm callback tiến độ thời gian thực | `src/application/pipelines/auto_video_pipeline.py` | Đã có & hoạt động |
| **F5.2** | `Presentation` (`FastAPI`) | REST API Server (`/api/v1/health`, `/projects`, `/subtitles`, `/probe`, `/trim`, `/sources/inspect`, `/video`, `/mcp/*`) | `src/presentation/api/main.py` | Cần bổ sung `/api/v1/sources/inspect` |
| **F5.3** | `Presentation` (`MCP Server`) | MCP Server `kinetix-ai` (`kinetix_produce_video`, `kinetix_update_subtitles`, `kinetix_probe_media`, `kinetix_trim_video`, `kinetix_inspect_source`, `kinetix_launch_desktop_app`) + cờ `--self-test` | `src/presentation/mcp/mcp_server.py` | Cần sửa `--self-test` không bị treo `stdio` và thêm 3 MCP tools mới |
| **F6.1** | `Desktop App` (`KinetixAI.Desktop`) | Giao diện Studio NLE 3 cột chuyên nghiệp (Dark Slate `#090A0F`/`#11131A`/`#3B82F6`), 100% Custom Dark Templates cho `ComboBox`, `DataGrid`, `ListBox`, `Slider` | `desktop_app/KinetixAI.Desktop/App.xaml` | Đã có & hoạt động |
| **F6.2** | `Desktop App` (`KinetixAI.Desktop`) | Màn hình **16:9 Program Video Monitor (`MediaElement`)** tích hợp sẵn kèm Play/Pause, Stop, Scrub Bar & Timecode | `desktop_app/KinetixAI.Desktop/MainWindow.xaml` | Đã có & hoạt động |
| **F6.3** | `Desktop App` (`KinetixAI.Desktop`) | Bảng **Whisper Subtitle & Word-Timing Editor (`DataGrid`)** + nút Thêm/Xóa dòng + nút **Re-Render Subtitles** | `desktop_app/KinetixAI.Desktop/MainWindow.xaml.cs` | Cần gọi `GridSubtitles.CommitEdit()` trước khi gửi API |
| **F6.4** | `Desktop App` (`KinetixAI.Desktop`) | Công cụ **Non-Linear Trim Clip (FFmpeg)**, **FFprobe Stream Inspector**, nút **Inspect Source**, và nút **Auto-Whisper (Clear Script)** | `desktop_app/KinetixAI.Desktop/MainWindow.xaml.cs` | Cần thêm nút `Inspect` và `Auto-Whisper` trên UI |

---

## 2. Technical Context

- **Language/Version**: Python 3.11+ (managed via `uv`), Node.js 24+ / TypeScript 5+, C# 12 / .NET 10.0 (`net10.0-windows` WPF Desktop)
- **Primary Dependencies**:
  - **Python Core & API**: `fastapi`, `uvicorn`, `pydantic` (v2), `yt-dlp`, `faster-whisper`, `openai-whisper`, `ffmpeg-python`, `httpx`, `streamlit`, `mcp`, `pytest`
  - **Visual Render Engines**: `remotion`, `@remotion/cli`, `@remotion/renderer`, `react`, `react-dom`, `hyperframes` (HTML/CSS/GSAP deterministic renderer + CLI bridge)
  - **Media Processing**: `FFmpeg` 8.x CLI (`ffmpeg`, `ffprobe`) + `ffmpeg-python`
  - **Windows Desktop Client**: .NET WPF (`System.Net.Http.Json`, custom dark NLE control templates, integrated `MediaElement` monitor, process manager for FastAPI backend)
- **Storage**: File-system workspace (`workspace/` for project artifacts, raw downloads, extracted WAV audio, `.transcript.json`, `.srt`, `.vtt`, rendered overlay MP4s, and final composited MP4s) + JSON project state persistence (`workspace/projects.json`).
- **Testing**: `pytest` (unit tests + integration tests) + `dotnet build` verification for the WPF Desktop Client.

---

## 3. Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Gate 1 - Clean Architecture & Layer Isolation (Principle I)**: PASS. `src/domain`, `src/application`, `src/infrastructure`, `src/presentation`, `render_engines/`, and `desktop_app/` are strictly separated.
- **Gate 2 - SOLID & Dependency Inversion (Principle II)**: PASS. All adapter methods (`download`, `extract_metadata`, `extract_audio`, `probe_media`, `trim_video`, `mix_audio_tracks`, `merge_and_export`, `transcribe`, `render_composition`) are declared on the Domain ABC interfaces (`IMediaDownloader`, `IVideoProcessor`, `ITranscriber`, `IVisualRenderer`).
- **Gate 3 - Adapter Pattern for 5 External Tools (Principle III)**: PASS. All 5 tools (`YtDlpAdapter`, `WhisperAdapter`, `FfmpegAdapter`, `RemotionAdapter`, `HyperFramesAdapter`) inherit from `src/domain/interfaces/` ABCs.
- **Gate 4 - Strict Type Hinting & Data Contracts (Principle IV)**: PASS. Python 3.11+ type hints and Pydantic v2 models enforce all API and subprocess JSON contracts.
- **Gate 5 - Test-Driven Quality & Pytest Coverage (Principle V)**: PASS. Unit and integration test suites under `tests/unit/` and `tests/integration/` cover all layers and edge cases.

---

## 4. Project Structure

```text
KinetixAI/
├── .specify/                         # GitHub Spec Kit configuration, constitution, templates, scripts
├── .agents/skills/                   # Spec Kit (speckit-*) & HyperFrames (heygen-com/hyperframes) skills
├── specs/001-auto-video-desktop-system/
│   ├── spec.md                       # Feature Specification
│   ├── plan.md                       # Implementation Plan & Feature Inventory (this file)
│   ├── research.md                   # Phase 0 Architecture & Tooling Research
│   ├── data-model.md                 # Phase 1 Domain Entities & Validation Rules
│   ├── quickstart.md                 # Phase 1 Validation & Run Guide
│   ├── contracts/
│   │   └── api-and-render-contracts.md
│   └── tasks.md                      # Phase 2 Executable Task Checklist
├── render_engines/
│   ├── remotion_engine/              # React/TypeScript compositions (Root.tsx, CaptionTemplate.tsx, render.mjs)
│   └── hyperframes_engine/           # HTML/CSS/GSAP compositions (index.html, compositions/captions.html, render.mjs)
├── src/
│   ├── domain/
│   │   ├── entities/                 # enums.py, subtitle_segment.py, media_asset.py, render_job.py, video_project.py
│   │   └── interfaces/               # media_downloader.py, transcriber.py, visual_renderer.py, video_processor.py
│   ├── application/
│   │   ├── factories/                # renderer_factory.py
│   │   ├── pipelines/                # auto_video_pipeline.py
│   │   └── services/                 # project_service.py
│   ├── infrastructure/
│   │   ├── downloaders/              # ytdlp_adapter.py
│   │   ├── transcribers/             # whisper_adapter.py
│   │   ├── processors/               # ffmpeg_adapter.py
│   │   ├── renderers/                # remotion_adapter.py, hyperframes_adapter.py
│   │   └── repositories/             # json_project_repository.py
│   └── presentation/
│       ├── schemas/                  # project_schemas.py
│       ├── api/                      # main.py
│       ├── cli/                      # main.py
│       ├── mcp/                      # mcp_server.py
│       └── ui/                       # streamlit_app.py
├── desktop_app/
│   └── KinetixAI.Desktop/            # App.xaml, MainWindow.xaml, MainWindow.xaml.cs, Models/ApiModels.cs
└── tests/
    ├── unit/                         # test_domain_entities.py, test_renderer_factory.py, test_adapters.py, test_auto_video_pipeline.py
    └── integration/                  # test_end_to_end_pipeline.py, test_fastapi_endpoints.py, test_mcp_server.py
```
