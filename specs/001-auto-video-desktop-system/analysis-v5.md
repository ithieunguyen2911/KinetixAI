# Specification & Codebase Quality Analysis Report (`/speckit-analyze` — v5.0 Deep Audit)

**Feature**: `001-auto-video-desktop-system` | **Date**: 2026-11-18 | **Constitution**: `.specify/memory/constitution.md` (v1.0.0)

## 1. Executive Summary
Following the user's observation (*"Tôi thấy nó chỉ có cái vỏ chứ chưa có thật sự hoạt động"*, evidenced by `PROJECTS BIN (0)` in screenshot `media_1794935596685_4198fd38.jpg`) and the `/goal` requirement to produce the real full-length podcast episode **`TẬP 1: TUỔI 30 VÀ KHOẢN NỢ CỦA GIẤC MƠ ĐỔI ĐỜI`**, a full cross-artifact and runtime audit was executed across `spec.md`, `plan.md`, `tasks.md`, `src/`, `render_engines/`, and `desktop_app/`.

---

## 2. Findings Table

| ID | Category | Severity | Location(s) | Summary | Remediation |
|----|----------|----------|-------------|---------|-------------|
| C1 | Runtime / Startup Bug | **CRITICAL** | `MainWindow.xaml.cs:L280-305`, `run_desktop.ps1:L19-21`, `json_project_repository.py:L32-38` | WPF `EnsureBackendRunningAsync` invoked bare `uv` (failing when `.local\bin` is absent from GUI PATH or timing out at 10s), leaving `PROJECTS BIN (0)` empty. `JsonProjectRepository._load` also wiped all projects if any single JSON item failed parsing. | Launch `.venv\Scripts\python.exe -m uvicorn` directly, pre-start & health-check FastAPI in `run_desktop.ps1`, and isolate `try/except` per item in `JsonProjectRepository._load`. |
| C2 | Underspecification / Parser Bug | **CRITICAL** | `project_service.py:L1070-1109` | `generate_project_podcast` naively split lines by `\|` and `:`, causing timestamps (`0:00 – 0:20`), bracketed SFX cues (`[Âm thanh: ...]`), and recording tips (`GỢI Ý THU ÂM...`) to be spoken aloud by TTS! | Implement `PodcastScriptParser` in `src/domain/services/podcast_script_parser.py` to strip non-spoken stage cues/notes, extract chapter markers, inject Hook pauses, and chunk long paragraphs into natural caption turns. |
| C3 | TTS Reliability & Pacing | **CRITICAL** | `tts_voice_adapter.py:L313,L346-420` | `edge_tts` had a strict `12.0s` timeout and bare `except Exception: pass` that silently fell back to English Windows SAPI or a 330Hz sine tone on longer Vietnamese paragraphs. | Increase timeout to `45s` with retry, synthesize chunked turns concurrently (`max_workers=3`), add Hook pause tags (`"30 tuổi"`, `"tắt ngấm"`, `"con số âm"`), and shape `vi-VN-NamMinhNeural` with warm late-night EQ. |
| C4 | Visual Rendering Defect | **CRITICAL** | `remotion_engine/render.mjs:L114-123`, `hyperframes_engine/render.mjs:L212-220`, `ffmpeg_adapter.py:L836` | Single-line `drawtext` clipped any Vietnamese sentence >55 chars off-screen; `colorkey=0x000000` created jagged text edges; podcast video cloned a static frame for 5 minutes with no audio waveform or chapter progression. | Add UTF-8 multi-line wrapped `.ass` subtitle generator and `FfmpegAdapter.render_podcast_video` with real `showwaves` voice visualizer, Episode/Chapter HUDs, progress bar, and 2-stage mood color shift. |
| H5 | Audio Realism Gap | **HIGH** | `audio_library_adapter.py:L13-94`, `project_service.py:L1179-1182` | BGM presets used static continuous sine waves instead of musical chord progressions; missing diegetic Hook SFX (`sfx_fan_shutdown`, `sfx_phone_vibrate`) and missing 2-stage BGM crossfade (`Ambient Piano` -> `Inspiring Acoustic` at `BƯỚC NGOẶT`). | Add chord-progression piano/acoustic BGM (`bgm_piano_melancholic`, `bgm_inspiring_acoustic`), diegetic SFX (`sfx_fan_shutdown`, `sfx_phone_vibrate`), and 2-stage crossfaded BGM + SFX mixing in podcast export. |
| M6 | Artifact Drift & UI Sync | **MEDIUM** | `spec.md`, `plan.md`, `tasks.md`, `MainWindow.xaml` | `spec.md` & `plan.md` stopped at v3.0 while `tasks.md` header said v2.0; Context/Character saves did not offer immediate visual sync; Tab 4/5 dropdowns lacked the new acoustic/piano & diegetic SFX presets. | Synchronize all Spec Kit docs to v5.0 (`T069`–`T080`), add new presets & 1-click Episode 1 script loader in WPF UI, and sync Context/Character HUD updates cleanly. |

---

## 3. Requirement-to-Task Coverage Summary

| Requirement Key | Has Task? | Task IDs | Notes |
|-----------------|-----------|----------|-------|
| `FR-001` (5-Step Pipeline) | Yes | `T010`–`T019`, `T028`–`T035` | Verified |
| `FR-002` (NLE Post-Production) | Yes | `T036`–`T045` | Verified |
| `FR-003` (Context, Scenes, Characters, Audit) | Yes | `T046`, `T051`–`T055`, `T076` | Enhanced visual sync in Phase 18 |
| `FR-004` (Curated & Diegetic BGM/SFX) | Yes | `T049`, `T071` | Upgraded with chord piano & Hook SFX |
| `FR-005` (Interactive Timeline CRUD) | Yes | `T059`, `T063`, `T065` | Verified |
| `FR-006` (VoiceStudio Clone/Design/Dub) | Yes | `T060`, `T062`–`T065` | Verified |
| `FR-007` (Structured Podcast Script Parser) | Yes | `T069`, `T070`, `T074` | Phase 18 remediation |
| `FR-008` (Broadcast Waveform & Wrapped `.ass` Subtitles) | Yes | `T072`, `T073`, `T074` | Phase 18 remediation |
| `FR-009` (Desktop Startup & Repo Fault Isolation) | Yes | `T075`, `T076`, `T079` | Phase 18 remediation |

## 4. Constitution Alignment
- **Zero Constitution Violations**: All remediations strictly preserve `domain` -> `application` -> `infrastructure` -> `presentation` isolation, ABC Dependency Inversion, strict typing, and `pytest` verification.
