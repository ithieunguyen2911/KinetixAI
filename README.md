# KinetixAI (FlowVids-AI) — Polyglot Automated Video Production Studio

**KinetixAI** is a Polyglot Modular Monolith desktop video production system built with **Clean Architecture** and **SOLID** principles, managed via **GitHub Spec Kit (`specify-cli`)**, and integrated with **AI Antigravity MCP (`kinetix-ai`)**.

---

## Core Tech Stack & 5 GitHub Ecosystems

| Layer / Role | Technology / Repository | Implementation Details |
| :--- | :--- | :--- |
| **1. Media Ingestion** | [`yt-dlp/yt-dlp`](https://github.com/yt-dlp/yt-dlp) | `YtDlpAdapter` (`IMediaDownloader`): Remote URL downloading, `extract_info(download=False)` metadata inspection, `download_ranges` time-range clipping, subtitle extraction, local file ingestion, and synthesized spoken-voice sample generation (`SpeechSynthesizer` + FFmpeg HD test broadcast). |
| **2. Speech-to-Text & Timestamps** | [`openai/whisper`](https://github.com/openai/whisper) & `faster-whisper` | `WhisperAdapter` (`ITranscriber`): 16kHz mono speech transcription with Voice Activity Detection (`vad_filter=True`), silence hallucination filtering (`no_speech_threshold`), word-level timestamps (`WordTimestamp`), and HyperFrames-compatible `.transcript.json` export (`[{id, text, start, end}]`). |
| **3. HTML/CSS/GSAP Motion Engine** | [`heygen-com/hyperframes`](https://github.com/heygen-com/hyperframes) | `HyperFramesAdapter` (`IVisualRenderer`): Generates spec-compliant HyperFrames HTML compositions (`data-composition-id`, `class="clip"`, `data-start`, `data-duration`, `data-track-kind="captions"`, `<template>` partial injection, `gsap.fromTo` on child elements, `window.__timelines`) and renders deterministic 30fps MP4 overlays. |
| **4. React/TypeScript Video Engine** | [`remotion-dev/remotion`](https://github.com/remotion-dev/remotion) | `RemotionAdapter` (`IVisualRenderer`): Declarative React compositions (`CaptionTemplate.tsx`) with `<Composition>`, `<Sequence>`, `useCurrentFrame()`, `spring()` physics entrance animations, and active word-by-word karaoke highlighting. |
| **5. Media Processing & Compositing** | [`FFmpeg`](https://ffmpeg.org/) (`ffmpeg` + `ffprobe`) | `FfmpegAdapter` (`IVideoProcessor`): `probe_media()` JSON stream inspection via `ffprobe`, speech-bandpass 16kHz mono WAV extraction (`highpass=f=80,lowpass=f=7600`), non-linear video trimming (`trim_video`), multi-track audio ducking/mixing (`mix_audio_tracks`), `.srt` + `.vtt` subtitle generation, and `colorkey` overlay compositing (`libx264` + `aac`). |
| **6. Desktop Client UI** | **C# / .NET WPF (`KinetixAI.Desktop`)** | Dark slate broadcast NLE workstation UI (`#090A0F` / `#11131A` / `#3B82F6`) with custom dark control templates, built-in 16:9 `MediaElement` video monitor & transport scrub bar, `ffprobe` stream inspector, non-linear FFmpeg trim controls, editable Whisper subtitle table, and 3-second real-time MCP synchronization. |
| **7. Spec-Driven Governance** | [`github/spec-kit`](https://github.com/github/spec-kit) (`specify-cli`) | Governed by `.specify/memory/constitution.md` and full SDD artifacts under `specs/001-auto-video-desktop-system/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, `tasks.md`). |

---

## Clean Architecture Directory Structure

```text
KinetixAI/
├── .specify/                         # GitHub Spec Kit Constitution, templates & scripts
├── .agents/skills/                   # Installed Spec Kit (speckit-*) & HyperFrames official skills
├── specs/001-auto-video-desktop-system/ # Spec-Driven Development artifacts (spec, plan, tasks, contracts)
├── render_engines/
│   ├── remotion_engine/              # React/TypeScript compositions (Root.tsx, CaptionTemplate.tsx)
│   └── hyperframes_engine/           # HTML/CSS/GSAP compositions (index.html, compositions/captions.html)
├── src/
│   ├── domain/                       # Enterprise Entities & ABC Interfaces (zero external dependencies)
│   │   ├── entities/                 # VideoProject, SubtitleSegment, WordTimestamp, MediaAsset, RenderJob
│   │   └── interfaces/               # IMediaDownloader, ITranscriber, IVisualRenderer, IVideoProcessor
│   ├── application/                  # Use-Case Orchestration & Factories
│   │   ├── factories/                # RendererFactory (switches between Remotion & HyperFrames)
│   │   ├── pipelines/                # AutoVideoPipeline (5-step DI orchestrator)
│   │   └── services/                 # ProjectService (workspace persistence, ffprobe, trim, re-render)
│   ├── infrastructure/               # Concrete Adapters for the 5 GitHub tools
│   │   ├── downloaders/              # YtDlpAdapter
│   │   ├── transcribers/             # WhisperAdapter
│   │   ├── processors/               # FfmpegAdapter
│   │   └── renderers/                # RemotionAdapter, HyperFramesAdapter
│   └── presentation/                 # Delivery Mechanisms
│       ├── api/                      # FastAPI REST API + MCP HTTP Bridge
│       ├── cli/                      # Typer CLI (kinetix)
│       └── mcp/                      # FastMCP / MCPServer (kinetix-ai) for AI Antigravity
├── desktop_app/
│   └── KinetixAI.Desktop/            # Native Windows C# .NET WPF Studio Workstation
└── tests/
    ├── unit/                         # Domain, Factory, Pipeline & Adapter unit tests
    └── integration/                  # End-to-End Pipeline, FastAPI & MCP Server integration tests
```

---

## Quickstart

### 1. Run Automated Tests
```powershell
uv run pytest -v
```

### 2. Start Python FastAPI Orchestrator
```powershell
uv run uvicorn src.presentation.api.main:app --host 127.0.0.1 --port 8000
```

### 3. Build & Launch Windows WPF Desktop Studio
```powershell
dotnet build desktop_app/KinetixAI.Desktop/KinetixAI.Desktop.csproj
dotnet run --project desktop_app/KinetixAI.Desktop/KinetixAI.Desktop.csproj
```
*(Note: The WPF Desktop App automatically starts the Python FastAPI backend if port `8000` is not already running.)*

### 4. Command via AI Antigravity MCP (`kinetix-ai`)
```powershell
uv run python -m src.presentation.mcp.mcp_server --self-test
```
Available MCP tools:
- `kinetix_produce_video`
- `kinetix_update_subtitles`
- `kinetix_list_projects`
- `kinetix_get_project`
- `kinetix_launch_desktop_app`
- `kinetix_health_check`
