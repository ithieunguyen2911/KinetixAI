# TÀI LIỆU HƯỚNG DẪN SỬ DỤNG PHẦN MỀM KINETIX STUDIO v4.0
**Đơn vị:** KINETIXAI (FLOWVIDS-AI) STUDIO WORKSTATION  
**Hệ thống:** KINETIX STUDIO v4.0 AI STORYBOARD, PODCAST, VOICESTUDIO & NLE WORKSTATION  
**Phiên bản:** 4.0 | **Ngày ban hành:** 16/11/2026 | **Biên soạn:** Đội ngũ Kỹ thuật & Sản xuất KinetixAI

---
## MỤC LỤC
- **1.** Giới thiệu tổng quan hệ thống Kinetix Studio v4.0 & Kiến trúc Đa ngôn ngữ (Polyglot Clean Architecture)
  - **1.1** Mục đích, Phạm vi & Đối tượng sử dụng
  - **1.2** Kiến trúc Đa ngôn ngữ (Polyglot Clean Architecture) & Nguyên tắc SOLID
  - **1.3** Hệ sinh thái công nghệ cốt lõi
  - **1.4** Từ điển thuật ngữ nghiệp vụ
- **2.** Khởi động nhanh (.\run_desktop.ps1) & Tổng quan Bố cục 4 Vùng Giao diện Studio
  - **2.1** Điều kiện kỹ thuật & Môi trường vận hành
  - **2.2** Quy trình khởi động nhanh bằng PowerShell
  - **2.3** Tổng quan Bố cục 4 Vùng Giao diện Studio
- **3.** Nhập nguồn Video (Media Ingest), Chọn Render Engine (Remotion / HyperFrames) & Chạy Pipeline 5 Bước
  - **3.1** Nhập nguồn Video & Kiểm tra Siêu dữ liệu (Inspect Source)
  - **3.2** Lựa chọn Render Engine (Remotion / HyperFrames) & Motion Template
  - **3.3** Nhập kịch bản Script hoặc Kích hoạt Auto-Whisper STT
  - **3.4** Chạy Pipeline 5 Bước & Quản lý Kho Dự án (Projects Bin)
- **4.** Hướng dẫn Thao tác Thêm, Sửa, Cắt Đôi, Nhân Bản & Xóa Clip trực tiếp trên Multi-Track NLE Timeline (V2, V1, S1, A1, B1)
  - **4.1** Cấu trúc 5 Track & Điều khiển Program Monitor
  - **4.2** Thanh Sửa Clip Nhanh (Inline Clip Quick-Editor Bar) & Menu Chuột Phải
  - **4.3** Quy trình Thêm, Sửa, Cắt Đôi, Nhân Bản, Xóa & Render Timeline ra MP4
- **5.** Quản lý Phụ đề (Subtitles), Bối cảnh (Context Bible) & Phân cảnh Storyboard (Scenes)
  - **5.1** Tab 1: Quản lý & Chỉnh sửa Phụ đề (PHỤ ĐỀ - SUBTITLES)
  - **5.2** Tab 2 (Phần trên): Thiết lập Bối cảnh Thế giới (Context Bible)
  - **5.3** Tab 2 (Phần dưới): Quản lý Phân cảnh Storyboard (Scenes CRUD + Clone)
- **6.** Quản lý Nhân vật Đồng nhất, Podcast Đa Giọng Kể Chuyện & Công nghệ VoiceStudio (Voice Design, Consent-Gated Voice Cloning, Video Dubbing)
  - **6.1** Tab 3: Quản lý Nhân vật Đồng nhất (NHÂN VẬT ĐỒNG NHẤT)
  - **6.2** Tab 4 (Thẻ 1): Tạo Giọng đọc Neural TTS & Lồng tiếng Nhanh
  - **6.3** Tab 5: Sản xuất Podcast & Kể chuyện Đa Giọng (PODCAST & VOICESTUDIO AI)
  - **6.4** Công nghệ VoiceStudio AI: Expressive Tags, Voice Design, Consent-Gated Cloning & Auto Dubbing
- **7.** Hậu kỳ Chuyên sâu — Chỉnh màu LUT, Tốc độ (Speed), Khung hình (16:9 / 9:16 / 1:1), Chuyển cảnh, Animation, BGM/SFX & Tự động Cắt theo Nhịp (Beat-Cut)
  - **7.1** Thay đổi Khung hình (Aspect Ratio), Tốc độ (Speed) & Hiệu ứng Chuyển cảnh / Animation
  - **7.2** FFprobe Stream Inspector, Chỉnh màu LUT & Cắt/Master Âm thanh (Right Dock)
  - **7.3** Thư viện Nhạc nền (BGM), Chèn SFX & Tự động Cắt theo Nhịp (Auto Beat-Cut)
- **8.** Tự động hóa với AI Antigravity qua 27 MCP Tools (kinetix-ai) & Truy vết Nhật ký Log (Audit Logs)
  - **8.1** Cơ chế kết nối MCP, Bảng lệnh trực tiếp & Đồng bộ thời gian thực 3 giây
  - **8.2** Danh mục đầy đủ 27 MCP Tools (kinetix-ai)
  - **8.3** Tab 6: Truy vết & Xuất Nhật ký Log (NHẬT KÝ LOG - AUDIT)
- **9.** Xử lý sự cố thường gặp & Hướng dẫn khắc phục nhanh
  - **9.1** Bảng Chẩn đoán Sự cố & Hướng dẫn Khắc phục nhanh
  - **9.2** Danh mục Kiểm tra Trước khi Bàn giao Thành phẩm (Pre-Export Checklist)

---

## 1. Giới thiệu tổng quan hệ thống Kinetix Studio v4.0 & Kiến trúc Đa ngôn ngữ (Polyglot Clean Architecture)

**Kinetix Studio v4.0 (KinetixAI / FlowVids-AI)** là trạm làm việc (Workstation) sản xuất video tự động đa ngôn ngữ trên Windows, kết hợp giữa **Ứng dụng Desktop Native C# .NET WPF**, **Lõi điều phối Python FastAPI**, **Hai bộ máy kết xuất đồ họa chuyển động (`Remotion` & `HyperFrames`)**, **Công nghệ xử lý giọng nói `VoiceStudio`**, và **Giao thức AI Antigravity MCP (`kinetix-ai`)**.

Tài liệu này hướng dẫn chi tiết cho người vận hành, biên tập viên nội dung, đạo diễn Storyboard/Podcast và kỹ sư tích hợp AI cách cài đặt, khởi động, thao tác chỉnh sửa phi tuyến (Non-Linear Editing — NLE), tổng hợp giọng nói biểu cảm và điều khiển tự động hóa toàn trình từ nguồn thô đến tệp MP4 thành phẩm.

### 1.1 Mục đích, Phạm vi & Đối tượng sử dụng

Phạm vi tài liệu bao phủ toàn bộ quy trình vận hành trên giao diện đồ họa Windows WPF (`Kinetix Studio v4.0`), API REST (`http://127.0.0.1:8000`), và 27 công cụ MCP (`kinetix-ai`) phục vụ sản xuất video ngắn, video thuyết minh công nghệ, podcast đa giọng kể chuyện và lồng tiếng đa ngôn ngữ.

| Vai trò người dùng | Phân hệ sử dụng chính | Trách nhiệm & Tác vụ cốt lõi |
| --- | --- | --- |
| **Biên tập viên Video (NLE Editor)** | Media Ingest, Program Monitor, Multi-Track Timeline, Right Dock Post-FX | Nhập nguồn video, chỉnh sửa phụ đề, cắt ghép clip trên 5 track (`V2`, `V1`, `S1`, `A1`, `B1`), chỉnh màu LUT, tốc độ và khung hình. |
| **Đạo diễn Storyboard & Podcast** | Context Bible, Scenes, Characters, Podcast & VoiceStudio AI | Xây dựng bối cảnh đồng nhất, hồ sơ nhân vật, thiết kế/nhân bản giọng nói có đồng thuận, tạo Podcast đa giọng và Auto Dubbing. |
| **Trợ lý AI Antigravity (MCP Client)** | 27 MCP Tools (`kinetix-ai`) qua `stdio` hoặc `/api/v1/mcp/command` | Thực thi lệnh ngôn ngữ tự nhiên để sản xuất video, ghép BGM/SFX, Beat-Cut và đồng bộ trực tiếp về Desktop App mỗi 3 giây. |
| **Kỹ sư Hệ thống / Vận hành** | PowerShell Scripts, FastAPI Core, Audit Logs & `pytest` | Khởi động dịch vụ (`run_desktop.ps1`, `run_api.ps1`), kiểm tra sức khỏe công cụ qua `ffprobe`/`kinetix_health_check` và truy vết sự cố. |

### 1.2 Kiến trúc Đa ngôn ngữ (Polyglot Clean Architecture) & Nguyên tắc SOLID

Theo hiến chương kỹ thuật `.specify/memory/constitution.md`, toàn bộ mã nguồn Python cốt lõi trong `src/` tuân thủ nghiêm ngặt **Clean Architecture** gồm 4 tầng đồng tâm độc lập (`domain` -> `application` -> `infrastructure` -> `presentation`) kết hợp nguyên lý **SOLID** và **Dependency Inversion Principle (DIP)**.

| Tầng kiến trúc (Layer) | Thư mục / Thành phần | Vai trò & Ràng buộc cô lập |
| --- | --- | --- |
| **1. Domain** | `src/domain/entities/` & `src/domain/interfaces/` | Chứa thực thể nghiệp vụ (`VideoProject`, `SubtitleSegment`, `TimelineClip`, `VoiceProfile`, `PodcastTurn`, `StoryScene`, `CharacterProfile`, `SceneContext`, `AuditLogEntry`) và các interface trừu tượng (`IMediaDownloader`, `ITranscriber`, `IVisualRenderer`, `IVideoProcessor`, `IVoiceSynthesizer`, `IAudioAssetLibrary`). Không phụ thuộc thư viện ngoài. |
| **2. Application** | `src/application/` (`AutoVideoPipeline`, `ProjectService`, `RendererFactory`) | Điều phối luồng sản xuất 5 bước, quản lý Timeline CRUD, Podcast, VoiceStudio và chuyển đổi linh hoạt giữa `Remotion` và `HyperFrames` qua Factory Pattern. |
| **3. Infrastructure** | `src/infrastructure/` (`YtDlpAdapter`, `WhisperAdapter`, `FfmpegAdapter`, `RemotionAdapter`, `HyperFramesAdapter`, `TtsVoiceAdapter`, `StudioAudioLibraryAdapter`, `JsonProjectRepository`) | Đóng gói toàn bộ lệnh CLI/thư viện bên thứ ba (`yt-dlp`, `faster-whisper`, `ffmpeg/ffprobe`, `edge-tts`, Node.js renderers) và lưu trữ trạng thái dự án tại `workspace/projects.json`. |
| **4. Presentation & Clients** | `src/presentation/` (`api/`, `mcp/`, `cli/`, `ui/`) & `desktop_app/KinetixAI.Desktop/` | Cung cấp FastAPI REST API (`127.0.0.1:8000`), FastMCP Server (`kinetix-ai`), CLI (`kinetix`), Streamlit Dashboard và ứng dụng Windows C# .NET 10 WPF. |

### 1.3 Hệ sinh thái công nghệ cốt lõi

| Thành phần công nghệ | Bộ chuyển đổi / Vị trí | Chức năng chính trong Kinetix Studio v4.0 |
| --- | --- | --- |
| **`yt-dlp`** | `YtDlpAdapter` (`IMediaDownloader`) | Kiểm tra siêu dữ liệu URL không cần tải full (`extract_info`), tải video tối đa 1080p MP4, cắt khoảng thời gian, nạp file cục bộ và sinh mẫu thử `demo://sample`. |
| **`Whisper` (`faster-whisper` + Windows Speech STT)** | `WhisperAdapter` (`ITranscriber`) | Nhận dạng giọng nói với `vad_filter=True`, lọc ảo giác im lặng (`no_speech_threshold=0.6`), tách `WordTimestamp` từng từ và xuất `.transcript.json`. |
| **`Remotion` (React/TS)** | `RemotionAdapter` & `render_engines/remotion_engine/` | Kết xuất overlay đồ họa chuyển động bằng React (`<Composition>`, `<Sequence>`, `useCurrentFrame()`, `spring()`) ở chuẩn `1280×720 @ 30fps`. |
| **`HyperFrames` (HTML/CSS/GSAP)** | `HyperFramesAdapter` & `render_engines/hyperframes_engine/` | Tạo composition chuẩn HTML5/GSAP (`data-composition-id`, `class="clip"`, `data-track-kind="captions"`, `gsap.fromTo`, `window.__timelines`) và render MP4. |
| **`FFmpeg` / `ffprobe`** | `FfmpegAdapter` (`IVideoProcessor`) | Phân tích stream (`probe_media`), tách WAV 16kHz mono (`highpass=80,lowpass=7600`), ghép overlay `colorkey`, cắt/nối, chỉnh màu LUT, tốc độ, khung hình, Beat-Cut và Audio Mastering. |
| **`edge-tts` / `VoiceStudio` Architecture** | `TtsVoiceAdapter` (`IVoiceSynthesizer`) | Tổng hợp giọng nói Neural (`edge-tts` + fallback Windows SAPI Offline), thiết kế giọng theo mô tả & seed, nhân bản giọng có kiểm soát đồng thuận, thẻ cảm xúc `[emotion:...]`, `[pause ...]` và Video Dubbing. |
| **`FastAPI` & 27 MCP Tools** | `src/presentation/api/main.py` & `mcp_server.py` | Cung cấp REST API tại `http://127.0.0.1:8000` và 27 công cụ `kinetix_*` kết nối AI Antigravity qua `stdio` hoặc HTTP Bridge. |
| **Windows C# .NET WPF Workstation** | `desktop_app/KinetixAI.Desktop/` (`net10.0-windows`) | Giao diện studio nền tối (`#0B0D10`), tích hợp `MediaElement` monitor, Timeline 5 track tương tác, 6 Tab chức năng và đồng bộ 3 giây với MCP. |

### 1.4 Từ điển thuật ngữ nghiệp vụ

| Thuật ngữ | Giải thích áp dụng trong Kinetix Studio v4.0 |
| --- | --- |
| **Pipeline 5 Bước** | Quy trình khép kín tự động: (1) Tải/Nạp nguồn (`yt-dlp`) -> (2) Tách WAV 16kHz (`FFmpeg`) -> (3) Tạo phụ đề (`Whisper`) -> (4) Render Overlay (`Remotion`/`HyperFrames`) -> (5) Trộn & Xuất MP4 (`FFmpeg`). |
| **Playhead** | Đường con trỏ màu đỏ trên thanh thời gian (`PlayheadLine`), xác định vị trí giây hiện tại để phát thử, đặt điểm `Set In [` / `Set Out ]`, chèn SFX hoặc `Cắt Đôi` clip. |
| **Context Bible** | Tài liệu quy chuẩn bối cảnh toàn cục (`World Setting`, `Visual Style`, `Lighting & Lens`, `Continuity Notes`) giúp duy trì phong cách nhất quán xuyên suốt các phân cảnh. |
| **Consent-Gated Voice Cloning** | Cơ chế nhân bản giọng nói từ tệp ghi âm tham chiếu chỉ được phép thực thi khi người dùng xác nhận đồng thuận (`consent_verified = True`). |
| **Seeded Voice Design** | Thiết kế hồ sơ giọng nói nhân tạo (`VoiceProfile`) bằng mô tả ngôn ngữ tự nhiên kết hợp giá trị `seed` cố định để tái lập sắc thái âm thanh. |
| **Expressive Speech Tags** | Các thẻ điều khiển nhịp ngắt và cảm xúc nhúng trực tiếp trong lời thoại, ví dụ `[pause 500ms]`, `[emotion:warm]`, `[emotion:dramatic]`, `[laughter]`, `[breath]`. |
| **EBU R128 (`loudnorm`)** | Chuẩn chuẩn hóa độ lớn âm thanh phát sóng truyền hình (`I=-16 LUFS`, `TP=-1.5 dBTP`, `LRA=11 LU`) đảm bảo âm lượng ổn định giữa các phân cảnh. |

## 2. Khởi động nhanh (.\run_desktop.ps1) & Tổng quan Bố cục 4 Vùng Giao diện Studio

Chương này hướng dẫn các điều kiện môi trường cần thiết, cách khởi chạy nhanh toàn hệ thống bằng một lệnh PowerShell duy nhất và làm quen với 4 vùng giao diện chính trên trạm làm việc **Kinetix Studio v4.0**.

### 2.1 Điều kiện kỹ thuật & Môi trường vận hành

- **Hệ điều hành & Khung hiển thị:** Windows 10/11 (64-bit); kích thước cửa sổ mặc định `1640 × 960` (tối thiểu `1360 × 800`).
- **Nền tảng thực thi:** `.NET 10 SDK` (`net10.0-windows` cho WPF Desktop), `Python >= 3.11` quản lý qua `uv`, `Node.js 20+` (cho `Remotion` & `HyperFrames`).
- **Công cụ media hệ thống:** `ffmpeg` và `ffprobe` đã được cài đặt và khai báo trong biến môi trường `PATH` của Windows.
- **Kết nối mạng (tùy chọn):** Cần Internet khi tải URL qua `yt-dlp` hoặc dùng giọng `edge-tts`; hệ thống vẫn hoạt động ngoại tuyến hoàn toàn với `demo://sample`, file nội bộ và giọng `win-sapi-studio`.

### 2.2 Quy trình khởi động nhanh bằng PowerShell

1. **Bước 1:** Mở cửa sổ **PowerShell** và di chuyển vào thư mục gốc dự án (`D:\AI_Learning_Repository\KinetixAI`).
2. **Bước 2:** Chạy lệnh khởi động ứng dụng Desktop: `.\run_desktop.ps1`. Script sẽ tự động dọn các tiến trình `KinetixAI.Desktop` và Core API cũ còn treo, biên dịch `desktop_app/KinetixAI.Desktop/KinetixAI.Desktop.csproj` bằng `dotnet build` và mở `KinetixAI.Desktop.exe`.
3. **Bước 3:** Khi cửa sổ Studio mở lên, hàm `MainWindow_Loaded` tự kiểm tra `http://127.0.0.1:8000/api/v1/health`. Nếu FastAPI Core chưa chạy, ứng dụng tự động khởi chạy ngầm lệnh `uv run uvicorn src.presentation.api.main:app --host 127.0.0.1 --port 8000`.
4. **Bước 4:** Quan sát góc phải thanh trên cùng: khi đèn `DotBackend` chuyển xanh lá kèm chữ **Core API: Online** và bộ đếm **MCP: 27 Tools** sáng xanh dương, trạm làm việc đã sẵn sàng.

> **[TIP] CHẾ ĐỘ CHẠY BACKEND ĐỘC LẬP & KIỂM TRA NHANH:** Trong quá trình phát triển hoặc khi muốn xem log HTTP trực tiếp, bạn có thể chạy trước `.\run_api.ps1` (khởi động Uvicorn với `--reload` tại `http://127.0.0.1:8000`). Để kiểm tra nhanh MCP Server, chạy `uv run python -m src.presentation.mcp.mcp_server --self-test`.

### 2.3 Tổng quan Bố cục 4 Vùng Giao diện Studio

Giao diện **Kinetix Studio** sử dụng tông màu tối chuyên dụng cho hậu kỳ truyền hình (`#0B0D10` / `#12151B` / `#2563EB`), chia thành **4 vùng thao tác trực quan** cùng thanh trạng thái dưới cùng (`Clean Architecture Status Bar`).

![Hình 2.1 – Phân bổ 4 vùng chức năng chính trên giao diện Kinetix Studio Workstation](C:/Users/HUU HIEU/.gemini/antigravity/brain/4fc2cfaf-15d2-43c8-8969-750c33aa2f92/scratch/assets/fig_ui_4_zones.png)
*Hình 2.1 – Phân bổ 4 vùng chức năng chính trên giao diện Kinetix Studio Workstation*

> **[INFO] LƯU Ý PHIÊN BẢN GIAO DIỆN:** Ảnh chụp thực tế trên minh họa bố cục 4 vùng chuẩn của Kinetix Studio Workstation. Ở phiên bản **v4.0**, giao diện bổ sung thêm nút `Hướng Dẫn (User Guide)` và nhãn `MCP: 27 Tools` trên Vùng 1, **Thanh Sửa Clip Nhanh** ngay phía trên Timeline 5 Track ở Vùng 3, và Tab thứ 6 `PODCAST & VOICESTUDIO AI`.

![Hình 2.2 – Vùng 1: Thanh công cụ nhanh Top NLE Bar (Aspect, Speed, Transition, Anim, MCP Status & Sync)](C:/Users/HUU HIEU/.gemini/antigravity/brain/4fc2cfaf-15d2-43c8-8969-750c33aa2f92/scratch/assets/fig_top_bar.png)
*Hình 2.2 – Vùng 1: Thanh công cụ nhanh Top NLE Bar (Aspect, Speed, Transition, Anim, MCP Status & Sync)*

| Số vùng | Tên vùng trên giao diện | Thành phần & Nhiệm vụ chính |
| --- | --- | --- |
| **Vùng 1** | **Top NLE Workstation Bar** | Hiển thị logo `KINETIX STUDIO v4.0 NLE`, thanh tác vụ nhanh (`ASPECT: 16:9 / 9:16 / 1:1`, `SPEED`, `TRANS`, `ANIM`, `Apply FX`), nút mở tài liệu `Hướng Dẫn (User Guide)`, trạng thái `MCP: 27 Tools`, `Core API: Online` và nút `Sync`. |
| **Vùng 2** | **Left Dock (Ingest & Projects Bin)** | Chứa thẻ `MEDIA INGEST & MOTION ENGINE` (nhập Project ID, Engine, Template, Source URL/File, Script) và `PROJECTS BIN` (danh sách dự án trong workspace, nút `Clone` và `Delete`). |
| **Vùng 3** | **Center Dock (Monitor, Timeline & 6 Tabs)** | Bao gồm: (1) `PROGRAM MONITOR` phát video 16:9 kèm transport bar; (2) `INTERACTIVE MULTI-TRACK NLE TIMELINE` 5 track (`V2`, `V1`, `S1`, `A1`, `B1`) kèm Quick-Editor Bar; (3) Khu vực **6 Tab Studio** (`PHỤ ĐỀ`, `BỐI CẢNH & PHÂN CẢNH`, `NHÂN VẬT ĐỒNG NHẤT`, `GIỌNG ĐỌC, ÂM THANH & BEAT`, `PODCAST & VOICESTUDIO AI`, `NHẬT KÝ LOG`). |
| **Vùng 4** | **Right Dock (Inspector, Post-FX & MCP)** | Gồm 4 bảng xếp dọc: `PIPELINE & FFPROBE INSPECTOR` (tiến độ & thông số kỹ thuật), `COLOR GRADING & LUT STUDIO`, `NON-LINEAR TRIM & AUDIO MASTERING`, và `ANTIGRAVITY MCP & CONSOLE LOG`. |

## 3. Nhập nguồn Video (Media Ingest), Chọn Render Engine (Remotion / HyperFrames) & Chạy Pipeline 5 Bước

Mọi quy trình sản xuất video mới đều bắt đầu từ bảng **MEDIA INGEST & MOTION ENGINE** tại Vùng 2 (Left Dock), cho phép kiểm tra nhanh nguồn video đầu vào, chọn bộ máy kết xuất và kích hoạt Pipeline 5 bước hoàn toàn tự động.

![Hình 3.1 – Khung Media Ingest & Motion Engine và Kho Dự án (Projects Bin) tại Left Dock](C:/Users/HUU HIEU/.gemini/antigravity/brain/4fc2cfaf-15d2-43c8-8969-750c33aa2f92/scratch/assets/fig_media_ingest_panel.png)
*Hình 3.1 – Khung Media Ingest & Motion Engine và Kho Dự án (Projects Bin) tại Left Dock*

### 3.1 Nhập nguồn Video & Kiểm tra Siêu dữ liệu (Inspect Source)

Ô `Source Input (URL, File, or demo://sample)` hỗ trợ 3 loại nguồn đầu vào thông qua `YtDlpAdapter` và `FfmpegAdapter`:

| Loại nguồn | Giá trị nhập hợp lệ | Cơ chế xử lý của hệ thống |
| --- | --- | --- |
| **Mẫu thử Studio** | `demo://sample` (hoặc `sample`) | Tự động tạo video thử nghiệm `1280×720 @ 30fps` dài 6 giây với lưới studio tối và giọng đọc tổng hợp offline. |
| **Tệp video cục bộ** | Đường dẫn `.mp4`, `.mov`, `.mkv`, `.webm` (chọn qua nút `Browse`) | Sao chép an toàn vào thư mục dự án trong `workspace/<project_id>/` và phân tích stream bằng `ffprobe`. |
| **Liên kết trực tuyến** | URL YouTube hoặc trang hỗ trợ `yt-dlp` | Tải video tốt nhất chuẩn MP4 (`height<=1080`) và ghép luồng âm thanh `m4a` tự động qua `YtDlpAdapter`. |

1. **Bước 1:** Nhập mã định danh dự án duy nhất vào ô **Project ID `*`** (ví dụ `studio_master_v4`, không chứa khoảng trắng hoặc ký tự đặc biệt).
2. **Bước 2:** Dán URL vào ô **Source Input `*`**, nhấn **Browse** để chọn tệp từ ổ đĩa, hoặc giữ nguyên `demo://sample`.
3. **Bước 3:** Nhấn nút **Inspect** để kiểm tra trước siêu dữ liệu (tiêu đề, thời lượng, độ phân giải, FPS) qua `POST /api/v1/sources/inspect` mà chưa cần tải toàn bộ tệp video.

### 3.2 Lựa chọn Render Engine (Remotion / HyperFrames) & Motion Template

Nhờ `RendererFactory` áp dụng nguyên lý Liskov Substitution (LSP), Kinetix Studio v4.0 cho phép chọn hoặc hoán đổi hai Render Engine độc lập bất cứ lúc nào mà không thay đổi cấu trúc dự án.

| Render Engine | Công nghệ nền tảng | Đặc điểm & Trường hợp ưu tiên |
| --- | --- | --- |
| **`remotion`** | React / TypeScript (`CaptionTemplate.tsx`, `render.mjs`) | Khuyên dùng cho đồ họa component React, chuyển động vật lý `spring()`, lower-third và karaoke từng từ (`useCurrentFrame()`). |
| **`hyperframes`** | HTML5 / CSS3 / GSAP (`index.html`, `compositions/captions.html`) | Khuyên dùng cho hiệu ứng web mượt với `gsap.fromTo`, cấu trúc clip phân lớp `data-track-kind="captions"` và kiểm chuẩn `window.__timelines`. |

Tại danh sách **Motion Graphics Template**, chọn một trong 4 mẫu có sẵn: `CaptionTemplate` (Phụ đề thanh dưới chuẩn broadcast), `KineticTitleCard` (Thẻ tiêu đề mở đầu `KINETIX STUDIO PRESENTATION`), `SocialPopCaptions` (Hộp phụ đề nổi bật phong cách mạng xã hội), hoặc `TechCalloutHUD` (Giao diện HUD kỹ thuật kèm thanh tiến trình đáy màn hình).

### 3.3 Nhập kịch bản Script hoặc Kích hoạt Auto-Whisper STT

- **Chế độ nhập kịch bản chủ động:** Gõ nội dung vào ô `Script / Captions`, phân tách từng câu phụ đề bằng ký tự gạch đứng `|`, xuống dòng, hoặc viết đoạn văn có dấu chấm câu (`.`, `!`, `?`). Hệ thống tự động chia đều thời lượng và tính mốc `WordTimestamp` cho từng từ.
- **Chế độ Auto-Whisper STT:** Nhấn nút **Auto-Whisper** (`BtnClearScript`) để xóa trắng ô Script. Khi chạy Pipeline, `WhisperAdapter` sẽ tự động nhận dạng giọng nói theo thứ tự ưu tiên: `faster-whisper` (kèm `vad_filter=True` và lọc im lặng) -> `openai-whisper` -> Windows `SpeechRecognitionEngine` offline -> kịch bản dự phòng nếu video câm.

### 3.4 Chạy Pipeline 5 Bước & Quản lý Kho Dự án (Projects Bin)

Khi nhấn nút **Execute 5-Step Production Pipeline**, `AutoVideoPipeline` sẽ thực thi tuần tự 5 giai đoạn và cập nhật thanh tiến trình trên `PIPELINE & FFPROBE INSPECTOR`:

| Bước | Tiến độ | Tác vụ thực thi & Đầu ra tạo thành |
| --- | --- | --- |
| **Bước 1** | `15%` | **Media Ingest (`yt-dlp`):** Tải/nạp hoặc tạo video gốc `raw_video_path` vào `workspace/<project_id>/`. |
| **Bước 2** | `35%` | **Audio Extraction (`FFmpeg`):** Trích xuất luồng âm thanh WAV chuẩn `16000 Hz` mono với bộ lọc giọng `highpass=f=80,lowpass=7600`. |
| **Bước 3** | `60%` | **Transcription & Storyboard (`Whisper`):** Tạo danh sách `SubtitleSegment`, xuất `.transcript.json`, và tự khởi tạo `StoryScene` + `TimelineClip` mặc định. |
| **Bước 4** | `80%` | **Visual Overlay Render (`Remotion`/`HyperFrames`):** Kết xuất lớp đồ họa chuyển động 1280×720@30fps (`_overlay.mp4`) theo Template & Nhân vật. |
| **Bước 5** | `92%–100%` | **Compositing & Export (`FFmpeg`):** Tách nền đen bằng `colorkey=0x000000:0.06:0.05`, ghép chồng lên video gốc và xuất `_final.mp4`, `.srt`, `.vtt`. |

1. **Bước 1:** Nhấn **Execute 5-Step Production Pipeline** và theo dõi tiến độ đến `100%` (`Completed: Final MP4 exported`). Video hoàn chỉnh sẽ tự động phát trên `PROGRAM MONITOR`.
2. **Bước 2:** Sau khi sửa phụ đề hoặc đổi Engine/Template, nhấn **Re-Render Overlay** để chỉ chạy lại Bước 4 và Bước 5 mà không phải tải lại video gốc.
3. **Bước 3:** Nhấn **Reveal Folder** để mở nhanh thư mục `workspace/<project_id>/` trong Windows Explorer.
4. **Bước 4:** Tại danh sách **PROJECTS BIN**, nhấp chọn bất kỳ dự án nào để nạp toàn bộ trạng thái vào Studio; nhấn **Clone** để nhân bản dự án sang ID mới (`POST /api/v1/projects/{id}/clone`), hoặc nhấn **Delete** để xóa dự án (`DELETE /api/v1/projects/{id}`).

> **[WARN] CẢNH BÁO XÓA DỰ ÁN VĨNH VIỄN:** Thao tác **Delete** trong `PROJECTS BIN` sẽ xóa bản ghi khỏi `projects.json` và xóa vĩnh viễn toàn bộ thư mục tệp media tại `workspace/<project_id>/` sau khi bạn xác nhận hộp thoại `Yes`. Hãy dùng nút **Clone** để sao lưu trước khi thử nghiệm thay đổi lớn.

## 4. Hướng dẫn Thao tác Thêm, Sửa, Cắt Đôi, Nhân Bản & Xóa Clip trực tiếp trên Multi-Track NLE Timeline (V2, V1, S1, A1, B1)

Trái tim của trạm chỉnh sửa phi tuyến Kinetix Studio v4.0 là khu vực **INTERACTIVE MULTI-TRACK NLE TIMELINE** với 5 làn track song song theo thời gian thực và thanh **Inline Timeline Clip Quick-Editor Bar** cho phép thao tác CRUD trực tiếp lên từng khối clip.

![Hình 4.1 – Chi tiết 5 Track đồng bộ (V2, V1, S1, A1, B1), thước thời gian và con trỏ Playhead đỏ](C:/Users/HUU HIEU/.gemini/antigravity/brain/4fc2cfaf-15d2-43c8-8969-750c33aa2f92/scratch/assets/fig_timeline_5_tracks.png)
*Hình 4.1 – Chi tiết 5 Track đồng bộ (V2, V1, S1, A1, B1), thước thời gian và con trỏ Playhead đỏ*

### 4.1 Cấu trúc 5 Track & Điều khiển Program Monitor

| Track ID | Tên hiển thị & Màu nhận diện | Dữ liệu quản lý trên Timeline |
| --- | --- | --- |
| **`V2`** | `V2 OVERLAY` (Xanh dương `#60A5FA`) | Lớp đồ họa chuyển động, tiêu đề và HUD được kết xuất bởi `Remotion` hoặc `HyperFrames`. |
| **`V1`** | `V1 VIDEO` (Xanh ngọc `#34D399`) | Luồng video nền chủ đạo (`raw_video_path` / các đoạn clip đã cắt ghép thứ tự). |
| **`S1`** | `S1 CAPTIONS` (Vàng hổ phách `#FBBF24`) | Từng khối câu phụ đề hiển thị theo mốc thời gian chính xác, đồng bộ hai chiều với bảng Tab 1 (`PHỤ ĐỀ`). |
| **`A1`** | `A1 AUDIO` (Tím `#A78BFA`) | Luồng âm thanh gốc, giọng đọc Neural TTS hoặc Podcast tổng hợp kèm dạng sóng minh họa. |
| **`B1`** | `B1 BEATS/SFX` (Xanh lơ `#38BDF8`) | Các điểm đánh dấu nhịp trống (Beat Grid Markers) sinh ra từ Auto Beat-Cut và các mốc chèn hiệu ứng SFX. |

Phía trên Timeline là **Program Monitor & Transport Deck** gồm các nút: `Play`/`Pause` (phát/tạm dừng), `Stop` (dừng về `00.00s`), `-1f` / `+1f` (nhích chính xác ±1 khung hình ở `30fps`), `Set In [` / `Set Out ]` (đánh dấu điểm đầu/cuối cho vùng Trim), thanh trượt `SliderScrub`, nút `Snapshot PNG` (chụp khung hình hiện tại ra ảnh PNG) và `External Player` (mở bằng trình phát mặc định của Windows).

### 4.2 Thanh Sửa Clip Nhanh (Inline Clip Quick-Editor Bar) & Menu Chuột Phải

Ở phiên bản **Kinetix Studio v4.0**, ngay phía trên thước thời gian (`00:00.0` .. `00:06.0`) có thanh công cụ chỉnh sửa clip trực tiếp gồm:

- **Ô chọn Track (`CmbClipTrack`):** Chọn làn đích `V2`, `V1`, `S1`, `A1`, hoặc `B1`.
- **Ô `Start` (`TxtClipStart`) & `End` (`TxtClipEnd`):** Nhập hoặc xem mốc thời gian bắt đầu/kết thúc tính bằng giây (ví dụ `0.00` đến `2.00`).
- **Ô nhãn / nội dung (`TxtClipLabel`):** Nhập tên clip hoặc nội dung lời thoại phụ đề (đối với track `S1`).
- **6 Nút tác vụ nhanh:** `+ Thêm`, `Sửa`, `Cắt Đôi`, `Nhân Bản`, `Xóa` và nút xanh nổi bật **Áp Dụng Timeline**.
- **Menu chuột phải (`ContextMenu`):** Nhấp chuột phải trực tiếp lên một khối clip ở track `V2`, `V1` hoặc `S1` để gọi nhanh `Cắt đôi tại Playhead`, `Nhân bản Clip` / `Nhân bản Cue`, hoặc `Xóa Clip` / `Xóa Cue`.

### 4.3 Quy trình Thêm, Sửa, Cắt Đôi, Nhân Bản, Xóa & Render Timeline ra MP4

1. **Bước 1:** **Chọn & Nhảy tới vị trí (Seek):** Nhấp vào thước thời gian hoặc vùng trống trên Timeline để di chuyển **Playhead đỏ** tới giây mong muốn. Nhấp vào một khối clip bất kỳ để chọn clip đó; toàn bộ thông tin (`Track`, `Start`, `End`, `Label`) sẽ tự động hiển thị trên thanh Quick-Editor.
2. **Bước 2:** **Thêm Clip mới (`+ Thêm`):** Chọn Track trong danh sách (ví dụ `S1` hoặc `V1`), nhập mốc `Start`, `End`, nội dung vào ô `TxtClipLabel`, rồi nhấn **+ Thêm**. Hệ thống gọi `POST /api/v1/projects/{id}/timeline-clips` với `action="add"`.
3. **Bước 3:** **Sửa Clip đang chọn (`Sửa`):** Sau khi nhấp chọn khối clip trên Timeline, chỉnh sửa lại thời gian `Start`/`End` hoặc nhãn `Label` trên Quick-Editor Bar, rồi nhấn **Sửa** (`action="update"`).
4. **Bước 4:** **Cắt Đôi Clip tại Playhead (`Cắt Đôi`):** Kéo hoặc click thanh thời gian để đặt **Playhead đỏ** nằm lọt vào bên trong khoảng thời gian của clip cần cắt (cách 2 đầu ít nhất `0.15s`), chọn clip và nhấn **Cắt Đôi** (hoặc chuột phải -> `Cắt đôi tại Playhead`). Hệ thống tự động chia clip thành 2 phần liên tiếp (phần `A` và `B`, hoặc tự tách đôi câu phụ đề trên track `S1`) đồng thời bảo toàn `source_start`/`source_end` của video nguồn.
5. **Bước 5:** **Nhân Bản Clip (`Nhân Bản`):** Chọn khối clip cần sao chép và nhấn **Nhân Bản** (`action="clone"`). Hệ thống tạo bản sao có cùng độ dài nối tiếp ngay sau mốc `end_time` của clip gốc.
6. **Bước 6:** **Xóa Clip (`Xóa`):** Chọn khối clip không cần thiết và nhấn **Xóa** (`action="delete"`).
7. **Bước 7:** **Kết xuất toàn bộ chỉnh sửa ra MP4 (`Áp Dụng Timeline`):** Sau khi hoàn tất sắp xếp các khối trên 5 track, nhấn nút **Áp Dụng Timeline** (`render_timeline=True`). Hệ thống tự cắt từng đoạn `V1` theo `source_start..source_end`, nối tuần tự qua `concat_clips`, đồng bộ lại overlay phụ đề từ track `S1` và xuất tệp `_final.mp4` mới.

> **[TIP] ĐỒNG BỘ HAI CHIỀU GIỮA TRACK S1 VÀ TAB PHỤ ĐỀ:** Mỗi thao tác Thêm, Sửa, Cắt Đôi, Nhân Bản hoặc Xóa clip trên track `S1` đều được `ProjectService.manage_timeline_clip()` đồng bộ tức thời vào danh sách `project.subtitles` và `WordTimestamp` để đảm bảo bảng Tab 1 (`PHỤ ĐỀ`) và file `.srt`/`.vtt` luôn khớp 100%.

## 5. Quản lý Phụ đề (Subtitles), Bối cảnh (Context Bible) & Phân cảnh Storyboard (Scenes)

Khu vực **6-Tab Studio Workstation** nằm ở nửa dưới Vùng 3 (Center Dock) cung cấp môi trường biên tập bảng dữ liệu chi tiết cho phụ đề, quy chuẩn bối cảnh và từng phân cảnh Storyboard.

### 5.1 Tab 1: Quản lý & Chỉnh sửa Phụ đề (PHỤ ĐỀ - SUBTITLES)

Bảng `GridSubtitles` hiển thị từng câu phụ đề kèm 5 cột: `IN (SEC)` (có thể sửa), `OUT (SEC)` (có thể sửa), `DUR` (thời lượng tự tính), `WORDS` (số từ `WordTimestamp`), và `CAPTION DIALOGUE TEXT (EDITABLE)` (nội dung hiển thị).

1. **Bước 1:** **Chỉnh sửa trực tiếp nội dung/thời gian:** Nhấp đúp vào ô `IN (SEC)`, `OUT (SEC)` hoặc `CAPTION DIALOGUE TEXT` trên bảng, sửa nội dung rồi nhấn `Enter` để hoàn tất ô đang sửa.
2. **Bước 2:** **Thêm / Nhân bản / Tách / Xóa Cue:** Dùng các nút trên góc phải Tab 1 gồm `+ Thêm Cue` (nối thêm câu 2 giây vào cuối), `Nhân bản Cue` (sao chép dòng đang chọn), `Tách tại Playhead` (tách đôi câu phụ đề đang nằm dưới Playhead đỏ), hoặc `Xóa Cue`.
3. **Bước 3:** **Xuất tệp phụ đề chuẩn công nghiệp:** Nhấn **Xuất SRT / VTT** để gọi API `/api/v1/projects/{id}/subtitles/export` tạo đồng thời 3 tệp `<project_id>.srt`, `<project_id>.vtt` và `<project_id>.transcript.json` trong thư mục dự án.
4. **Bước 4:** **Cập nhật lên video thành phẩm:** Nhấn nút **Re-Render Overlay** ở Left Dock (`POST /api/v1/projects/{id}/subtitles`) để dựng lại lớp chữ mới và xuất MP4 cập nhật (có thể đổi Engine hoặc Template ngay trước khi bấm Re-Render).

### 5.2 Tab 2 (Phần trên): Thiết lập Bối cảnh Thế giới (Context Bible)

Khung **Global Scene Context** lưu giữ bộ quy chuẩn nghệ thuật (`SceneContext`) truyền vào mọi phân cảnh và Render Engine nhằm bảo đảm tính nhất quán thị giác:

| Trường thiết lập | Tên biến hệ thống | Giá trị mặc định & Ý nghĩa |
| --- | --- | --- |
| **Bối cảnh thế giới** | `world_setting` | `Modern AI Production Studio — Dark Slate Workstation` — Mô tả không gian chủ đạo. |
| **Phong cách hình ảnh** | `visual_style` | `Cinematic Clean UI, Subtle Tech Grid, High Broadcast Contrast` — Định hướng đồ họa. |
| **Ánh sáng & Ống kính** | `lighting_mood` / `camera_lens` | `Cool Cobalt Rim Light + Crisp Key Fill` (`35mm Anamorphic Studio Framing`) — Không khí ánh sáng và tiêu cự. |

Sau khi nhập thay đổi vào các ô văn bản, nhấn nút **Lưu Bối Cảnh** (`POST /api/v1/projects/{id}/context`) để lưu vào dự án và ghi nhận vào Audit Log.

### 5.3 Tab 2 (Phần dưới): Quản lý Phân cảnh Storyboard (Scenes CRUD + Clone)

Bảng `GridScenes` liên kết chặt chẽ giữa **Bối cảnh** (`setting_context`), **Nhân vật** (`CharacterId`), **Mốc thời gian** (`Start`, `Dur`), **Hiệu ứng chuyển cảnh** (`TransitionIn`), **Âm thanh** (`SfxId`), và **Lời thoại chi tiết** (`NarrationText`).

1. **Bước 1:** Nhấn **+ Thêm Cảnh** để chèn một phân cảnh mới nối tiếp ngay sau phân cảnh cuối cùng (mặc định thời lượng `2.0s`, lấy Transition & Animation đang chọn trên Top Bar).
2. **Bước 2:** Chọn một phân cảnh và nhấn **Nhân bản** (`BtnCloneScene`) để sao chép nhanh cấu hình chuyển cảnh, nhân vật và SFX sang cảnh kế tiếp.
3. **Bước 3:** Nhấp đúp vào các cột trên bảng `GridScenes` để chỉnh `TÊN CẢNH`, `NHÂN VẬT` (khớp với `CHAR ID` ở Tab 3), `START`, `DUR`, `CHUYỂN CẢNH`, `SFX`, và `LỜI THOẠI`.
4. **Bước 4:** Dùng nút **Xóa Cảnh** để bỏ dòng đang chọn, và luôn nhấn nút xanh **Lưu Phân Cảnh** (`POST /api/v1/projects/{id}/scenes` với `action="replace_all"`) để lưu toàn bộ Storyboard xuống ổ đĩa.

## 6. Quản lý Nhân vật Đồng nhất, Podcast Đa Giọng Kể Chuyện & Công nghệ VoiceStudio (Voice Design, Consent-Gated Voice Cloning, Video Dubbing)

Kinetix Studio v4.0 tích hợp bộ máy giọng nói lấy cảm hứng từ kiến trúc **`debpalash/VoiceStudio`** kết hợp `edge-tts` và Windows SAPI Offline, hỗ trợ quản lý hồ sơ nhân vật xuyên suốt, sản xuất Podcast/Audiobook nhiều giọng và lồng tiếng đa ngôn ngữ có kiểm soát đạo đức AI.

### 6.1 Tab 3: Quản lý Nhân vật Đồng nhất (NHÂN VẬT ĐỒNG NHẤT)

Mỗi dự án được khởi tạo sẵn 2 nhân vật chuẩn (`char_host` — *Minh Anh (Host)* màu `#3B82F6` dùng giọng `vi-VN-HoaiMyNeural`; và `char_architect` — *Kien Quoc (Architect)* màu `#10B981` dùng giọng `vi-VN-NamMinhNeural`). Hồ sơ nhân vật quy định badge HUD và giọng đọc đồng bộ khi Render Overlay.

1. **Bước 1:** Mở Tab **NHÂN VẬT ĐỒNG NHẤT**, nhấn **+ Thêm Nhân Vật** để tạo hồ sơ mới (hoặc **Nhân bản** từ nhân vật đang chọn).
2. **Bước 2:** Chỉnh sửa trực tiếp các cột: `CHAR ID`, `TÊN NHÂN VẬT`, `VAI TRÒ`, `GIỌNG ĐỌC TTS` (chọn mã giọng tích hợp hoặc ID giọng tùy biến vừa thiết kế/nhân bản), `BADGE` (nhãn tối đa 6 ký tự trên HUD), `MÀU` (mã hex như `#3B82F6`), và `MÔ TẢ NGOẠI HÌNH ĐỒNG NHẤT (VISUAL BIBLE)`.
3. **Bước 3:** Nhấn **Lưu Nhân Vật** (`POST /api/v1/projects/{id}/characters`) để lưu danh sách xuống `projects.json`. Dùng nút **Xóa** khi muốn loại bỏ nhân vật thừa.

### 6.2 Tab 4 (Thẻ 1): Tạo Giọng đọc Neural TTS & Lồng tiếng Nhanh

![Hình 6.1 – Tab Giọng đọc, Âm thanh & Beat-Cut với 4 thẻ chức năng chuyên biệt](C:/Users/HUU HIEU/.gemini/antigravity/brain/4fc2cfaf-15d2-43c8-8969-750c33aa2f92/scratch/assets/fig_audio_beat_tab.png)
*Hình 6.1 – Tab Giọng đọc, Âm thanh & Beat-Cut với 4 thẻ chức năng chuyên biệt*

| Mã giọng (`voice_id`) | Ngôn ngữ & Giới tính | Phong cách & Cơ chế hoạt động |
| --- | --- | --- |
| `vi-VN-HoaiMyNeural` | Tiếng Việt — Nữ | Giọng dẫn chuyện ấm áp, truyền cảm (`edge-tts` Neural). |
| `vi-VN-NamMinhNeural` | Tiếng Việt — Nam | Giọng tài liệu, phân tích kỹ thuật trầm ổn (`edge-tts` Neural). |
| `en-US-AriaNeural` | Tiếng Anh (Mỹ) — Nữ | Giọng phát thanh viên / Explainer chuyên nghiệp. |
| `en-US-GuyNeural` | Tiếng Anh (Mỹ) — Nam | Giọng Podcast / Bản tin thời sự. |
| `en-US-JennyNeural` | Tiếng Anh (Mỹ) — Nữ | Giọng hội thoại thân thiện. |
| `win-sapi-studio` | Nội bộ (Offline) | 100% ngoại tuyến bằng Windows `System.Speech.Synthesis` kết hợp `FFmpeg` tinh chỉnh cao độ/tốc độ. |

Tại Thẻ 1 (`1. GIỌNG ĐỌC TTS (VOICEOVER)`), chọn giọng đọc, kéo thanh trượt tốc độ đọc (`0.75x – 1.50x`), rồi nhấn **Tạo Giọng Đọc & Lồng Tiếng**. Hệ thống tổng hợp lời từ danh sách phụ đề hiện tại thành tệp WAV 16kHz và tự động kéo dài khung hình cuối (`tpad=stop_mode=clone`) nếu thời lượng giọng đọc dài hơn video gốc.

### 6.3 Tab 5: Sản xuất Podcast & Kể chuyện Đa Giọng (PODCAST & VOICESTUDIO AI)

Thẻ bên trái của Tab 5 (`TẠO PODCAST & KỂ CHUYỆN ĐA THỂ LOẠI`) cho phép biến kịch bản văn bản thô thành video Podcast hoặc Sách nói nhiều lượt thoại (`PodcastTurn`), tự động chia phân cảnh Storyboard, đồng bộ phụ đề, lồng nhạc nền tương ứng thể loại và xuất MP4 hoàn chỉnh.

| Mã thể loại (`genre`) | Tên trên giao diện | Cảm xúc & Nhạc nền tự động áp dụng |
| --- | --- | --- |
| `podcast_dialogue` | Podcast Đối thoại 2 người | Cảm xúc `warm`, xen kẽ 2 giọng Host/Guest, ngắt nghỉ `350ms`, BGM `bgm_lofi_chill`. |
| `late_night_story` | Kể chuyện Đêm khuya | Cảm xúc `late_night` (trầm sâu, tốc độ `0.86x`), ngắt nghỉ `550ms`, BGM `bgm_ambient_pad`. |
| `thriller_mystery` | Trinh thám / Kỳ bí | Cảm xúc `mysterious` (lọc trầm, bí ẩn), ngắt nghỉ `480ms`, BGM `bgm_dramatic_rise`. |
| `audiobook_narration` | Sách nói (Audiobook) | Cảm xúc `calm` (nhẹ nhàng, tốc độ `0.90x`), ngắt nghỉ `420ms`, BGM `bgm_ambient_pad`. |
| `tech_explainer` | Thuyết minh Công nghệ | Cảm xúc `excited` (sôi nổi `1.12x`), đối thoại 2 người, ngắt nghỉ `300ms`, BGM `bgm_cyber_pulse`. |
| `motivational_epic` | Truyền cảm hứng | Cảm xúc `dramatic` (uy lực, nhấn trầm `f=150Hz`), ngắt nghỉ `400ms`, BGM `bgm_dramatic_rise`. |

1. **Bước 1:** Chọn **Thể loại**, **Giọng Host** và **Giọng Guest** tại 3 hộp chọn trên cùng của Thẻ Podcast.
2. **Bước 2:** Nhập kịch bản vào ô nội dung theo cú pháp phân lượt `Host: Lời thoại 1 | Guest: Lời thoại 2` hoặc xuống dòng mỗi lượt nói (có thể chèn thẻ `[pause 400ms]`, `[emotion:warm]`).
3. **Bước 3:** Nhấn **Tạo Podcast Đa Giọng & Đồng Bộ Video** (`POST /api/v1/projects/{id}/podcast`). Hệ thống tự động tổng hợp từng lượt thoại WAV, ghép nối tuần tự, xây dựng lại `SubtitleSegment`, `StoryScene`, `TimelineClip`, render overlay và trộn BGM theo tỷ lệ mặc định `0.14`.

### 6.4 Công nghệ VoiceStudio AI: Expressive Tags, Voice Design, Consent-Gated Cloning & Auto Dubbing

Hai thẻ bên phải của Tab 5 (`VOICESTUDIO: THIẾT KẾ GIỌNG` và `VOICESTUDIO: NHÂN BẢN & LỒNG TIẾNG`) cung cấp đầy đủ 4 năng lực cốt lõi của kiến trúc VoiceStudio:

| Thẻ biểu cảm (Expressive Tag) | Hiệu ứng xử lý âm thanh (`TtsVoiceAdapter`) |
| --- | --- |
| `[pause 500ms]` / `[pause 1.5s]` / `[pause]` | Chèn khoảng lặng cuối câu bằng bộ lọc `apad=pad_dur=...` (tối đa `4.0s` mỗi lượt). |
| `[emotion:warm]` / `[emotion:calm]` / `[emotion:late_night]` | Giảm nhẹ tốc độ (`0.86x–0.96x`), hạ cao độ (`-2` đến `-6 Hz`) và tăng dải trầm ấm (`equalizer f=180–220Hz`). |
| `[emotion:excited]` / `[emotion:dramatic]` | `excited`: tăng tốc `1.12x`, `+6Hz`, sáng dải cao `2800Hz`; `dramatic`: `0.92x`, `-8Hz`, uy lực `150Hz +5dB`. |
| `[emotion:mysterious]` / `[emotion:whisper]` | `mysterious`: cắt cao `lowpass=4500`; `whisper`: lọc băng thông `highpass=450,lowpass=3200,volume=0.82`. |
| `[laughter]`, `[sigh]`, `[breath]` | Được phân tách sạch khỏi văn bản phụ đề hiển thị để giữ màn hình tinh gọn trong khi điều tiết nhịp đọc. |

- **Seeded Voice Design (`VOICESTUDIO: THIẾT KẾ GIỌNG`):** Nhập tên Profile mới (`TxtVoiceDesignName`) và mô tả bằng ngôn ngữ tự nhiên (`TxtVoiceDesignPrompt`, ví dụ *"Giọng nam trầm ấm, kể chuyện đêm khuya truyền cảm"*), rồi nhấn **Thiết Kế & Lưu Giọng Mới** (`POST /api/v1/voices/design`). Hệ thống phân tích từ khóa ngữ âm (giới tính, ngôn ngữ, trầm ấm, bí ẩn, sôi nổi, thì thầm) kết hợp `seed` để tạo ID `design_<slug>_<seed>` lưu bền vững tại `workspace/voice_profiles.json`.
- **Consent-Gated Voice Cloning (`Nhân Bản Giọng`):** Nhập tên giọng (`TxtCloneVoiceName`), nhấn nút **WAV** để chọn tệp ghi âm mẫu sạch (`.wav`/`.mp3`), đánh dấu chọn ô **Có sự đồng ý của chủ giọng nói** (`ChkCloneConsent`), rồi nhấn **Nhân Bản Giọng** (`POST /api/v1/voices/clone`). Hồ sơ tạo ra có mã `clone_<slug>_<seed>`.
- **Auto Dub Video (`Auto Dub Video`):** Nhấn nút **Auto Dub Video** (`POST /api/v1/projects/{id}/dubbing`) để hệ thống lồng tiếng lại toàn bộ dự án hiện tại theo ngôn ngữ mục tiêu (`vi-VN`, `en-US`...) và tự động căn chỉnh lại mốc thời gian phụ đề.

> **[DANGER] CHÍNH SÁCH KIỂM SOÁT ĐỒNG THUẬN (CONSENT-GATED POLICY):** Theo quy chuẩn đạo đức AI của **VoiceStudio**, thao tác nhân bản giọng nói bắt buộc phải bật `consent_verified = True` (tick chọn ô **Có sự đồng ý của chủ giọng nói**). Nếu bỏ trống ô xác nhận này hoặc đường dẫn tệp âm thanh không tồn tại, API và MCP Tool (`kinetix_clone_voice`) sẽ từ chối thực thi ngay lập tức (HTTP 400).

## 7. Hậu kỳ Chuyên sâu — Chỉnh màu LUT, Tốc độ (Speed), Khung hình (16:9 / 9:16 / 1:1), Chuyển cảnh, Animation, BGM/SFX & Tự động Cắt theo Nhịp (Beat-Cut)

Sau khi hoàn tất dựng thô và lồng tiếng, Kinetix Studio v4.0 cung cấp bộ công cụ hậu kỳ toàn diện bằng **FFmpeg** tại **Top NLE Bar**, **Right Dock** và **Tab 4** mà không cần phần mềm biên tập ngoài.

### 7.1 Thay đổi Khung hình (Aspect Ratio), Tốc độ (Speed) & Hiệu ứng Chuyển cảnh / Animation

| Nhóm công cụ (Top Bar) | Các tùy chọn hỗ trợ | Cơ chế xử lý FFmpeg bên dưới |
| --- | --- | --- |
| **`ASPECT` (Reframe)** | `16:9` (Ngang 1280×720)<br>`9:16` (Dọc 720×1280 Shorts/TikTok)<br>`1:1` (Vuông 720×720) | Tỉ lệ `9:16` và `1:1` tự động tạo nền mờ (`boxblur=20:8` / `18:6`) phủ kín khung và đặt video gốc sắc nét ở chính giữa. |
| **`SPEED` (Speed Ramp)** | UI: `0.50x`, `0.75x`, `1.00x`, `1.25x`, `1.50x`, `2.00x` (API/MCP: `0.25x–4.0x`) | Biến đổi đồng bộ tốc độ hình ảnh (`setpts`) và cao độ âm thanh không méo tiếng bằng chuỗi lọc `atempo` nối tiếp. |
| **`TRANS` (Chuyển cảnh)** | `none`, `fade_black`, `cross_dissolve`, `wipe_left`, `slide_up`, `glitch_flash` | Áp dụng hiệu ứng vào/ra khung hình (`fade`, quét `drawbox` hoặc lệch kênh màu `rgbashift`) qua nút **Apply FX**. |
| **`ANIM` (Chuyển động)** | `spring_pop`, `ken_burns_zoom`, `typewriter_reveal`, `neon_glow_pulse`, `slide_up_bounce`, `camera_shake_impact` | Tạo chuyển động zoom máy quay (`zoompan`), viền neon nhấp nháy, rung chấn impact (`crop+sin/cos`) và truyền preset sang Render Engine. |

### 7.2 FFprobe Stream Inspector, Chỉnh màu LUT & Cắt/Master Âm thanh (Right Dock)

![Hình 7.1 – Bảng PIPELINE & FFPROBE INSPECTOR, COLOR GRADING & LUT STUDIO và NON-LINEAR TRIM & AUDIO MASTERING](C:/Users/HUU HIEU/.gemini/antigravity/brain/4fc2cfaf-15d2-43c8-8969-750c33aa2f92/scratch/assets/fig_right_post_panels.png)
*Hình 7.1 – Bảng PIPELINE & FFPROBE INSPECTOR, COLOR GRADING & LUT STUDIO và NON-LINEAR TRIM & AUDIO MASTERING*

| Bảng LUT Preset (`ColorLookPreset`) | Đặc trưng màu sắc & Bộ lọc FFmpeg |
| --- | --- |
| `natural` (Rec.709 Standard) | Màu gốc tiêu chuẩn, chỉ áp dụng 3 thanh trượt `Brightness` (`-0.4..0.4`), `Contrast` (`0.5..2.0`), `Saturation` (`0.0..2.5`). |
| `teal_orange` (Cinematic Grade) | Tăng tương phản `1.15×`, bão hòa `1.25×` và cân bằng màu điện ảnh xanh mòng két/cam (`colorbalance`). |
| `warm_vintage` (Golden Film) | Tăng sáng nhẹ `+0.03`, giảm bão hòa `0.85×`, phủ tông phim vàng cổ điển ấm áp. |
| `noir_bw` (High-Contrast B&W) | Triệt tiêu bão hòa (`S=0.0`), tăng tương phản mạnh `1.30×` tạo chất phim đen trắng tương phản cao. |
| `studio_crisp` (Broadcast Sharp) | Tăng tương phản `1.12×`, bão hòa `1.10×` và làm nét cạnh bằng bộ lọc `unsharp=5:5:0.8:5:5:0.0`. |

1. **Bước 1:** **Kiểm tra thông số kỹ thuật:** Quan sát khung `PIPELINE & FFPROBE INSPECTOR` để xác minh `RES`, `FPS`, `VID`, `AUD` (codec & sample rate), `DUR` và `SIZE` sau mỗi bước hậu kỳ.
2. **Bước 2:** **Chỉnh màu LUT:** Chọn `LUT Preset`, tinh chỉnh 3 thanh trượt `Brightness` / `Contrast` / `Saturation` (nhấn `Reset` để về mặc định), rồi bấm **Apply Color Grade to Master**.
3. **Bước 3:** **Cắt đoạn đầu/cuối (Trim MP4):** Nhập số giây vào 2 ô Start/End (hoặc dùng nút `Set In [` và `Set Out ]` ở Monitor) và bấm **Trim MP4**.
4. **Bước 4:** **Audio Mastering 1 chạm:** Tích chọn `Silence Cut` (cắt khoảng lặng dưới `-35dB` kéo dài `>= 0.35s`), `EBU R128` (chuẩn hóa `-16 LUFS`), `+ Mix BGM`, rồi bấm **Execute Audio Mastering & BGM Mix**.

### 7.3 Thư viện Nhạc nền (BGM), Chèn SFX & Tự động Cắt theo Nhịp (Auto Beat-Cut)

Tại **Tab 4 (`GIỌNG ĐỌC, ÂM THANH & BEAT`)**, ba thẻ bên phải (xem lại *Hình 6.1*) cung cấp hệ thống trộn nhạc nền chuẩn hóa, chèn hiệu ứng âm thanh theo mốc Playhead và động cơ cắt ghép theo nhịp BPM.

| Nhóm âm thanh | Danh sách Preset tích hợp (`StudioAudioLibraryAdapter`) | Tùy chọn điều khiển |
| --- | --- | --- |
| **Nhạc nền (BGM)** | `bgm_ambient_pad` (90 BPM Warm)<br>`bgm_cyber_pulse` (120 BPM Tech)<br>`bgm_lofi_chill` (85 BPM Lo-Fi)<br>`bgm_news_broadcast` (128 BPM)<br>`bgm_dramatic_rise` (100 BPM Tension) | Thanh trượt `Ducking Volume` (`0.05 – 0.50`, mặc định `0.18`), nút **Trộn Nhạc Nền (Mix BGM)**. |
| **Hiệu ứng (SFX)** | `sfx_whoosh_fast` (`0.45s` Transition)<br>`sfx_pop_bubble` (`0.22s` Caption)<br>`sfx_glitch_digital` (`0.35s` Tech)<br>`sfx_cinematic_hit` (`0.85s` Boom)<br>`sfx_camera_shutter` (`0.18s` Snap)<br>`sfx_chime_ding` (`0.65s` Accent) | Ô `Tại giây (s)` tự động đồng bộ theo vị trí Playhead, nút **Chèn SFX Tại Playhead** (trộn qua `adelay`). |

1. **Bước 1:** Tại thẻ **4. NHỊP CẮT TỰ ĐỘNG (BEAT)**, chọn nhịp điệu mục tiêu (`90`, `110`, `120`, `128`, hoặc `140 BPM`).
2. **Bước 2:** Giữ chọn **Khớp phụ đề theo Beat** (`align_subtitles=True`) để tự động kéo các mốc `start_time`/`end_time` của từng câu phụ đề khớp đúng vào phách nhạc gần nhất.
3. **Bước 3:** Giữ chọn **Nháy nhịp thị giác** (`pulse_flash=True`) nếu muốn thêm vạch nhấn ánh sáng xanh cobalt tại các phách mạnh (downbeats).
4. **Bước 4:** Nhấn **Tự Động Cắt Theo Nhịp** (`POST /api/v1/projects/{id}/beat-cut`). Hệ thống xuất tệp `.beats.json` và hiển thị toàn bộ các điểm nhịp xanh lơ trên **Track B1** của Timeline.

## 8. Tự động hóa với AI Antigravity qua 27 MCP Tools (kinetix-ai) & Truy vết Nhật ký Log (Audit Logs)

Kinetix Studio v4.0 đóng vai trò là một **MCP Server (`kinetix-ai`)** hoàn chỉnh, cho phép AI Antigravity hoặc các agent lập trình khác điều khiển toàn bộ dây chuyền sản xuất video từ xa mà kết quả vẫn tự động hiển thị đồng bộ trên màn hình Desktop App.

### 8.1 Cơ chế kết nối MCP, Bảng lệnh trực tiếp & Đồng bộ thời gian thực 3 giây

![Hình 8.1 – Khung Antigravity MCP & Console Log ở góc dưới bên phải giao diện Studio](C:/Users/HUU HIEU/.gemini/antigravity/brain/4fc2cfaf-15d2-43c8-8969-750c33aa2f92/scratch/assets/fig_right_mcp_console.png)
*Hình 8.1 – Khung Antigravity MCP & Console Log ở góc dưới bên phải giao diện Studio*

- **Cấu hình `stdio` MCP Server:** Được khai báo tại `.agents/mcp_config.json` và `~/.gemini/config/mcp_config.json` với lệnh `uv --directory D:\AI_Learning_Repository\KinetixAI run python -m src.presentation.mcp.mcp_server`.
- **Khung Dispatch lệnh AI tại chỗ:** Trên Right Dock, nhập yêu cầu tự nhiên vào ô `ANTIGRAVITY MCP & CONSOLE LOG` (ví dụ *"Render HyperFrames promo video"*) và nhấn **Dispatch** để gọi `POST /api/v1/mcp/command`.
- **Đồng bộ thời gian thực 3 giây:** Bộ đếm `_mcpSyncTimer` trong WPF Desktop App kiểm tra `/api/v1/projects` mỗi 3 giây. Khi AI Antigravity tạo hoặc cập nhật dự án qua MCP, Desktop App tự nạp dự án mới vào `PROJECTS BIN` và phát trên `PROGRAM MONITOR`.

### 8.2 Danh mục đầy đủ 27 MCP Tools (kinetix-ai)

Dưới đây là toàn bộ **27 công cụ MCP** được đăng ký tại `src/presentation/mcp/mcp_server.py` và `/api/v1/mcp/tools`:

| Nhóm chức năng | Tên MCP Tool | Mô tả & Tham số chính |
| --- | --- | --- |
| **Hệ thống & Dự án (7)** | `kinetix_health_check`<br>`kinetix_inspect_source`<br>`kinetix_list_projects`<br>`kinetix_get_project`<br>`kinetix_clone_project`<br>`kinetix_delete_project`<br>`kinetix_launch_desktop_app` | Kiểm tra sẵn sàng 5 công cụ + Desktop EXE; soi siêu dữ liệu `source_url`; liệt kê/lấy/nhân bản/xóa dự án trong `workspace/projects.json`; mở cửa sổ WPF `KinetixAI.Desktop.exe`. |
| **Sản xuất & Timeline (3)** | `kinetix_produce_video`<br>`kinetix_update_subtitles`<br>`kinetix_manage_timeline_clip` | Chạy Pipeline 5 bước (`project_id`, `source_url`, `engine_type`, `script_text`, `template_id`); cập nhật phụ đề & re-render; thao tác `add`/`update`/`split`/`clone`/`delete`/`render` clip trên 5 track (`V2`, `V1`, `S1`, `A1`, `B1`). |
| **Hậu kỳ & Kỹ thuật (7)** | `kinetix_probe_media`<br>`kinetix_trim_video`<br>`kinetix_change_speed`<br>`kinetix_apply_color_grade`<br>`kinetix_reframe_video`<br>`kinetix_apply_transition_animation`<br>`kinetix_capture_snapshot` | Đọc thông số `ffprobe`; cắt MP4 (`start_time`, `end_time`); đổi tốc độ (`0.25–4.0`); áp LUT (`preset`, `brightness`, `contrast`, `saturation`, `gamma`); đổi khung hình (`16:9`, `9:16`, `1:1`); áp chuyển cảnh & animation; chụp ảnh PNG tại `timestamp_sec`. |
| **Âm thanh & Beat (3)** | `kinetix_master_audio`<br>`kinetix_apply_sound_library`<br>`kinetix_apply_beat_cut` | Cắt im lặng + `EBU R128` + trộn BGM (`bg_volume`); ghép `bgm_preset` & chèn `sfx_id` tại `sfx_timestamp`; tạo lưới nhịp `bpm` + khớp phụ đề + pulse flash. |
| **Storyboard & Nhân vật (2)** | `kinetix_manage_character`<br>`kinetix_manage_scene` | Thực hiện `upsert`/`clone`/`delete` hồ sơ nhân vật đồng nhất (`character_id`, `voice_id`, `theme_color`) và phân cảnh Storyboard (`scene_id`, `transition_in`, `animation_preset`, `sfx_id`). |
| **VoiceStudio & Podcast (5)** | `kinetix_generate_voiceover`<br>`kinetix_produce_podcast`<br>`kinetix_design_voice`<br>`kinetix_clone_voice`<br>`kinetix_dub_video` | Tạo thuyết minh TTS; dựng Podcast đa giọng theo `genre` & `raw_content`; thiết kế giọng bằng mô tả + `seed`; nhân bản giọng yêu cầu `consent_verified=True`; lồng tiếng video theo `target_language`. |

### 8.3 Tab 6: Truy vết & Xuất Nhật ký Log (NHẬT KÝ LOG - AUDIT)

Mọi thao tác trên Pipeline, Timeline, Storyboard, VoiceStudio hay lệnh từ MCP đều được ghi lại thành từng bản ghi `AuditLogEntry` (lưu tối đa 200 bản ghi gần nhất mỗi dự án) và hiển thị theo thứ tự mới nhất lên đầu tại **Tab 6 (`NHẬT KÝ LOG (AUDIT)`)**.

- **5 Cột dữ liệu truy vết:** `THỜI GIAN` (`YYYY-MM-DD HH:MM:SS`), `PHÂN HỆ` (`PIPELINE`, `INGEST`, `TRANSCRIBE`, `SUBTITLE`, `CONTEXT`, `SCENE`, `CHARACTER`, `AUDIO`, `COLOR`, `FX`, `BEAT`, `TIMELINE`, `PODCAST`, `DUBBING`, `NLE`, `PROJECT`), `THAO TÁC`, `TRẠNG THÁI` (`OK` / `ERROR`), và `CHI TIẾT THỰC THI`.
- **Xuất hồ sơ kiểm toán:** Nhấn nút **Xuất File Audit Log (.json)** (`BtnExportAuditLog`) để lưu tệp `workspace/<project_id>/<project_id>_audit_logs.json` và mở xem trực tiếp.

## 9. Xử lý sự cố thường gặp & Hướng dẫn khắc phục nhanh

Bảng dưới đây tổng hợp các tình huống lỗi thực tế có thể phát sinh trong quá trình vận hành **Kinetix Studio v4.0** cùng nguyên nhân gốc rễ và hướng xử lý nhanh tại chỗ.

### 9.1 Bảng Chẩn đoán Sự cố & Hướng dẫn Khắc phục nhanh

| Triệu chứng / Thông báo lỗi | Nguyên nhân gốc rễ | Hướng dẫn khắc phục nhanh |
| --- | --- | --- |
| **Đèn đỏ `Core API: Offline` trên Top Bar** | Tiến trình `uv` chưa có trong PATH hoặc cổng `127.0.0.1:8000` bị chặn/chiếm dụng. | Chạy thủ công `.\run_api.ps1` để xem log lỗi chi tiết, kiểm tra `uv --version`, sau đó nhấn nút **Sync** trên Top Bar. |
| **Xuất hiện file `*_rev1.mp4`, `*_rev2.mp4`** | Video gốc đang bị trình phát ngoài hoặc `MediaElement` giữ khóa ghi trên Windows. | Đóng trình phát ngoài (nếu đang mở). `FfmpegAdapter._safe_finalize_output` tự động xoay vòng tên `_revN` để không làm mất bản render mới. |
| **Lỗi khi chọn giọng Neural (`edge-tts`) hoặc mất Internet** | Kết nối mạng chậm hoặc dịch vụ `edge_tts` vượt ngưỡng timeout `12s`. | Hệ thống tự động chuyển về Windows `System.Speech.Synthesis`; bạn cũng có thể chọn chủ động `win-sapi-studio` để chạy offline 100%. |
| **Nhân bản giọng (`clone_voice`) báo lỗi HTTP 400 / ValueError** | Chưa đánh dấu ô xác nhận đồng thuận (`consent_verified=False`) hoặc tệp WAV/MP3 không tồn tại. | Kiểm tra lại đường dẫn tệp âm thanh mẫu qua nút **WAV** và bắt buộc đánh dấu ô **Có sự đồng ý của chủ giọng nói**. |
| **`Auto-Whisper` chỉ trả về câu mẫu mặc định** | Chưa có trọng số `faster-whisper` cache cục bộ và audio nguồn không phải tiếng Anh rõ hoặc bị im lặng. | Nhập thủ công câu kịch bản ngăn cách bởi `|` hoặc tải trước mô hình `faster-whisper` (`base`) về máy. |
| **`Cắt Đôi` / `split_video` báo lỗi không thể tách** | Vị trí Playhead quá gần mép đầu hoặc mép cuối của clip (nhỏ hơn `0.12s – 0.15s`). | Di chuyển Playhead đỏ vào vùng giữa của clip cần tách (cách 2 đầu tối thiểu `0.20s`) rồi bấm **Cắt Đôi** lại. |
| **Sửa dữ liệu trong bảng `DataGrid` nhưng lưu vẫn giữ giá trị cũ** | Ô đang sửa trên `GridSubtitles` / `GridScenes` / `GridCharacters` chưa thoát trạng thái Focus Edit. | Nhấn phím `Enter` hoặc nhấp sang ô khác sau khi gõ xong, rồi mới bấm **Lưu Phân Cảnh**, **Lưu Nhân Vật** hoặc **Re-Render Overlay**. |
| **`kinetix_launch_desktop_app` báo chưa tìm thấy `.exe`** | Dự án C# WPF chưa được biên dịch ra thư mục `bin/Debug/net10.0-windows/`. | Chạy `.\run_desktop.ps1` hoặc chạy `dotnet build desktop_app/KinetixAI.Desktop/KinetixAI.Desktop.csproj`. |
| **Lỗi ở Bước 4 (`Remotion`/`HyperFrames`)** | Thiếu `Node.js` trong `PATH` hoặc chưa cài đặt gói phụ thuộc tại `render_engines/`. | Chạy `kinetix_health_check` kiểm tra `"node": true`, kiểm tra cài đặt Node 20+ và chạy `npm install` trong thư mục engine tương ứng. |

### 9.2 Danh mục Kiểm tra Trước khi Bàn giao Thành phẩm (Pre-Export Checklist)

- Kiểm tra **FFprobe Inspector** đảm bảo độ phân giải đích (`1280×720`, `720×1280` hoặc `720×720`), tốc độ khung hình `30.00 fps` và âm thanh `aac / 16000Hz`.
- Rà soát tất cả các dòng trên Tab **PHỤ ĐỀ (SUBTITLES)** (hoặc track `S1`) không bị sai chính tả, chồng chéo mốc thời gian hoặc tràn ra ngoài tổng thời lượng video.
- Xác nhận đã chạy **Audio Mastering (`EBU R128`)** nếu ghép nhiều đoạn giọng đọc/Podcast và nhạc nền để tránh chênh lệch âm lượng.
- Xuất kèm bộ tệp `.srt` / `.vtt` và tệp `_audit_logs.json` khi cần lưu hồ sơ sản xuất doanh nghiệp.
