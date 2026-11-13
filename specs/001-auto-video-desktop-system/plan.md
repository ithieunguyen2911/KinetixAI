# Implementation Plan: KinetixAI (FlowVids-AI) v2.0 — Professional Non-Linear Video Editor (NLE) & Polyglot Automation Studio

**Branch**: `001-auto-video-desktop-system` | **Date**: 2026-11-13 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-auto-video-desktop-system/spec.md`

---

## 1. Summary & Architectural Vision

Transform **KinetixAI (FlowVids-AI)** into a full-featured **Professional Non-Linear Video Editor (NLE Workstation v2.0)** modeled after DaVinci Resolve / Premiere Pro / CapCut Pro while strictly enforcing the **Polyglot Modular Monolith + Clean Architecture + SOLID** rules established in `.specify/memory/constitution.md`:

1. **Core Backend & Orchestrator (`Python 3.11+` + `FastAPI` + `Pydantic v2`)**:
   - Encapsulates `yt-dlp` and `Whisper` (`faster-whisper` / `openai-whisper` / Windows Speech STT) via pure OOP Adapters (`YtDlpAdapter`, `WhisperAdapter`) inheriting from `src/domain/interfaces/`.
2. **Visual Render Engines (`Node.js 20+` / `TypeScript`)**:
   - Encapsulates `remotion-dev/remotion` (React) and `heygen-com/hyperframes` (HTML/CSS/GSAP) via `RemotionAdapter`, `HyperFramesAdapter`, and `RendererFactory` supporting **4 Professional Motion Templates** (`CaptionTemplate`, `KineticTitleCard`, `SocialPopCaptions`, `TechCalloutHUD`).
3. **Media & Non-Linear Editing Engine (`FFmpeg` + `ffprobe`)**:
   - Encapsulates all timeline editing, color grading, reframing, speed ramping, transition concatenation, silence jump-cut removal, audio loudness mastering, BGM ducking, and frame snapshots inside `FfmpegAdapter(IVideoProcessor)`.
4. **Native Windows Desktop Client (`C# .NET WPF` — `KinetixAI.Desktop`)**:
   - 4-Zone Studio Workstation with **Left Media Pool & FX Tabs**, **Center Program Monitor** (Frame Step `-1f`/`+1f`, Set In/Out, Razor Split, Snapshot PNG), **Right Inspector & Subtitle Cue Dock**, and **Bottom Visual Multi-Track Timeline (`V2 Motion Overlay`, `V1 Video Track`, `S1 Subtitle Track`, `A1 Audio & Waveform Track`)**.

---

## 2. Quy Hoạch 8 Phân Hệ Chức Năng Chỉnh Sửa Video Chuyên Nghiệp (NLE Feature Architecture)

| Phân Hệ (Module) | Công Cụ Gốc | Các Chức Năng Chuyên Nghiệp Cụ Thể | Tầng Kiến Trúc (Clean Architecture) |
| :--- | :--- | :--- | :--- |
| **M1. Media Bin & Ingest Studio** | `yt-dlp` + `ffprobe` | • **M1.1**: Tải video/audio từ URL (YouTube/TikTok/Vimeo) chọn độ phân giải <= 1080p<br>• **M1.2**: Cắt khoảng thời gian ngay khi tải (`download_ranges`: `start_time`..`end_time`)<br>• **M1.3**: Kiểm tra Metadata nguồn (`extract_metadata`: codec, FPS, thời lượng) trước khi tải<br>• **M1.4**: Tạo mẫu phát sóng Studio (`demo://sample`) và nhạc nền Ambient (`demo://bgm`) | `Domain`: `IMediaDownloader`<br>`Infra`: `YtDlpAdapter`<br>`API`: `POST /api/v1/sources/inspect` |
| **M2. Non-Linear Timeline Editing (NLE)** | `FFmpeg` (`IVideoProcessor`) | • **M2.1**: **Trim In / Out** cắt chính xác điểm đầu – điểm cuối không làm hỏng luồng<br>• **M2.2**: **Razor Split at Playhead** chia đôi clip tại đúng vị trí con trỏ thời gian (`split_video`)<br>• **M2.3**: **Multi-Clip Concat & Transitions** nối nhiều clip kèm hiệu ứng chuyển cảnh (`fade`, `wipeleft`, `dissolve` qua `xfade` / `acrossfade`)<br>• **M2.4**: **Speed Ramping (`0.25x` – `4.0x`)** tua nhanh/chậm đồng bộ cả hình (`setpts`) và tiếng (`atempo`) | `Domain`: `IVideoProcessor`<br>`Infra`: `FfmpegAdapter`<br>`API`: `/trim`, `/split`, `/concat`, `/speed` |
| **M3. Color Grading & Visual FX Studio** | `FFmpeg` (`eq`, `curves`, `unsharp`, `hue`) | • **M3.1**: Thanh trượt chỉnh màu chuyên sâu: **Brightness**, **Contrast**, **Saturation**, **Gamma**<br>• **M3.2**: **5 Bộ Lọc Màu Điện Ảnh (LUT / Look Presets)**:<br>  1. `natural` (Chuẩn Rec.709)<br>  2. `teal_orange` (Điện ảnh Teal & Orange)<br>  3. `warm_vintage` (Màu phim ấm cổ điển)<br>  4. `noir_bw` (Đen trắng tương phản cao)<br>  5. `studio_crisp` (Tăng độ nét `unsharp` + tương phản phát sóng) | `Domain`: `ColorLookPreset`, `ColorGradeSpec`<br>`Infra`: `FfmpegAdapter.apply_color_grade`<br>`API`: `POST /api/v1/projects/{id}/color-grade` |
| **M4. Smart Aspect Ratio & Social Reframe** | `FFmpeg` (`scale`, `crop`, `boxblur`, `overlay`) | • **M4.1**: **`16:9` Landscape (`1280x720` / `1920x1080`)** chuẩn YouTube / Desktop<br>• **M4.2**: **`9:16` Vertical Shorts/Reels/TikTok (`720x1280`)** tự động tạo nền mờ (`boxblur=20:10`) phía sau video chính, không bị viền đen<br>• **M4.3**: **`1:1` Square (`720x720`)** chuẩn bài đăng mạng xã hội | `Domain`: `AspectRatioPreset`<br>`Infra`: `FfmpegAdapter.reframe_aspect_ratio`<br>`API`: `POST /api/v1/projects/{id}/reframe` |
| **M5. Dual Motion Graphics & 4 Studio Templates** | `Remotion` (React) & `HyperFrames` (HTML/GSAP) | • **M5.1**: `CaptionTemplate` — Phụ đề Lower-Third truyền hình + Karaoke từng từ<br>• **M5.2**: `KineticTitleCard` — Màn hình tiêu đề mở đầu (Intro Title Card) + Lower-Third<br>• **M5.3**: `SocialPopCaptions` — Phụ đề nổi bật giữa/dưới màn hình kiểu Shorts/Reels<br>• **M5.4**: `TechCalloutHUD` — Hộp thông tin góc trên + phụ đề + thanh tiến trình chạy dọc đáy video | `Domain`: `TemplatePreset`, `IVisualRenderer`<br>`App`: `RendererFactory`<br>`Infra`: `RemotionAdapter`, `HyperFramesAdapter` |
| **M6. AI Speech, Silence Cut & Audio Mastering** | `Whisper` + `FFmpeg` (`silenceremove`, `loudnorm`, `amix`) | • **M6.1**: Nhận diện giọng nói `faster-whisper` (VAD + Word Timestamps) & Windows Speech STT<br>• **M6.2**: **Auto-Silence Jump-Cut (`remove_silences`)** tự động cắt bỏ khoảng lặng ngập ngừng trong video nói chuyện<br>• **M6.3**: **Broadcast Loudness Normalization (`normalize_audio`)** chuẩn hóa âm lượng EBU R128 (`loudnorm`)<br>• **M6.4**: **Multi-Track Audio Mixer & Ducking (`mix_audio_tracks`)** trộn giọng nói chính với nhạc nền (có sẵn `demo://bgm` hoặc file MP3/WAV ngoài) | `Domain`: `ITranscriber`, `IVideoProcessor`<br>`Infra`: `WhisperAdapter`, `FfmpegAdapter`<br>`API`: `/audio-master`, `/mix-audio` |
| **M7. Frame Snapshot & Master Export Presets** | `FFmpeg` (`vframes`, `libx264`) | • **M7.1**: **Capture Frame Snapshot (`capture_snapshot`)** chụp ảnh tĩnh PNG độ nét cao tại đúng giây Playhead đang dừng<br>• **M7.2**: Xuất phụ đề đa định dạng: `.srt`, `.vtt`, và `.transcript.json` chuẩn HyperFrames | `Infra`: `FfmpegAdapter.capture_snapshot`<br>`API`: `POST /api/v1/projects/{id}/snapshot` |
| **M8. Windows WPF NLE Workstation UI & MCP Bridge** | `C# .NET WPF` + `MCP Server` (`kinetix-ai`) | • **M8.1**: **Visual Multi-Track Timeline (`V2 Overlay`, `V1 Video`, `S1 Subtitles`, `A1 Audio`)** hiển thị trực quan các khối clip/phụ đề theo trục thời gian, click vào khối để nhảy Playhead<br>• **M8.2**: **Program Monitor Deck** với nút nhích từng khung hình (`-1f`, `+1f`), nút đặt điểm cắt `Set In [` / `Set Out ]`, nút chụp ảnh `Snapshot PNG`<br>• **M8.3**: **Color Grading, Speed, Aspect Ratio & Audio Mastering Panel** ngay trên giao diện Studio<br>• **M8.4**: Đồng bộ thời gian thực 2 chiều với **AI Antigravity MCP (`kinetix-ai`)** | `Presentation`: `desktop_app/KinetixAI.Desktop` & `src/presentation/mcp/mcp_server.py` |

---

## 3. Constitution Check (Kiểm Định Tuân Thủ Kiến Trúc)

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Gate 1 - Clean Architecture & Layer Isolation (Principle I)**: **PASS**.
  - `src/domain`: Chỉ chứa Entities (`VideoProject`, `SubtitleSegment`, `WordTimestamp`, `ColorGradeSpec`, `MediaAsset`, `RenderJob`), Enums (`RenderEngineType`, `JobStatus`, `AspectRatioPreset`, `ColorLookPreset`, `TemplatePreset`) và 4 Interfaces (`IMediaDownloader`, `ITranscriber`, `IVisualRenderer`, `IVideoProcessor`).
  - `src/application`: Chỉ chứa `AutoVideoPipeline`, `RendererFactory`, `ProjectService`.
  - `src/infrastructure`: Chứa 5 Adapters (`YtDlpAdapter`, `WhisperAdapter`, `FfmpegAdapter`, `RemotionAdapter`, `HyperFramesAdapter`) + `JsonProjectRepository`.
  - `src/presentation` & `desktop_app/`: Chứa FastAPI, CLI, MCP Server, Streamlit, và C# WPF Client.
- **Gate 2 - SOLID & Dependency Inversion (Principle II)**: **PASS**. Mọi phương thức NLE mới đều được định nghĩa trên `IVideoProcessor` và `IMediaDownloader` ABCs.
- **Gate 3 - Adapter Pattern for 5 External Tools (Principle III)**: **PASS**. Không có bất kỳ lệnh gọi `subprocess`, `ffmpeg`, `yt_dlp`, hay `whisper` nào nằm ngoài `src/infrastructure/`.
- **Gate 4 - Strict Type Hinting & Data Contracts (Principle IV)**: **PASS**. Toàn bộ request/response NLE mới đều được định nghĩa bằng Pydantic v2 (`src/presentation/schemas/project_schemas.py`) và DTO C# (`desktop_app/KinetixAI.Desktop/Models/ApiModels.cs`).
- **Gate 5 - Test-Driven Quality & Pytest Coverage (Principle V)**: **PASS**. Mọi tính năng NLE mới đều có unit test và integration test trong `tests/`.

---

## 4. Project Structure

```text
KinetixAI/
├── .specify/                                    # GitHub Spec Kit Constitution, templates & scripts
├── .agents/skills/                              # Spec Kit (speckit-*) & HyperFrames (heygen-com/hyperframes) skills
├── specs/001-auto-video-desktop-system/
│   ├── spec.md                                  # Feature Specification (v2.0 Professional NLE)
│   ├── plan.md                                  # Implementation Plan (this file)
│   ├── research.md                              # Phase 0 NLE Filtergraph & Timeline Research
│   ├── data-model.md                            # Phase 1 Domain Entities & Enums
│   ├── quickstart.md                            # Phase 1 Validation Guide
│   ├── contracts/
│   │   └── api-and-render-contracts.md          # Phase 1 ABC & REST API Contracts
│   └── tasks.md                                 # Phase 2 Dependency-Ordered Tasks (T001-T045)
├── render_engines/
│   ├── remotion_engine/                         # React/TypeScript compositions (4 Studio Templates)
│   └── hyperframes_engine/                      # HTML/CSS/GSAP compositions (4 Studio Templates, 12-Rule Contract)
├── src/
│   ├── domain/
│   │   ├── entities/                            # enums.py, subtitle_segment.py, nle_specs.py, media_asset.py, render_job.py, video_project.py
│   │   └── interfaces/                          # media_downloader.py, transcriber.py, visual_renderer.py, video_processor.py
│   ├── application/
│   │   ├── factories/                           # renderer_factory.py
│   │   ├── pipelines/                           # auto_video_pipeline.py
│   │   └── services/                            # project_service.py
│   ├── infrastructure/
│   │   ├── downloaders/                         # ytdlp_adapter.py
│   │   ├── transcribers/                        # whisper_adapter.py
│   │   ├── processors/                          # ffmpeg_adapter.py
│   │   ├── renderers/                           # remotion_adapter.py, hyperframes_adapter.py
│   │   └── repositories/                        # json_project_repository.py
│   └── presentation/
│       ├── schemas/                             # project_schemas.py
│       ├── api/                                 # main.py
│       ├── cli/                                 # main.py
│       ├── mcp/                                 # mcp_server.py
│       └── ui/                                  # streamlit_app.py
├── desktop_app/
│   └── KinetixAI.Desktop/                       # App.xaml, MainWindow.xaml, MainWindow.xaml.cs, Models/ApiModels.cs
└── tests/
    ├── unit/                                    # test_domain_entities.py, test_renderer_factory.py, test_adapters.py, test_auto_video_pipeline.py
    └── integration/                             # test_end_to_end_pipeline.py, test_fastapi_endpoints.py, test_mcp_server.py
```
