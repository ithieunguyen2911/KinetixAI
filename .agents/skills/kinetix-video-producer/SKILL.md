---
name: kinetix-video-producer
description: >-
  Command KinetixAI (FlowVids-AI) to produce automated MP4 videos, switch between
  Remotion (React) and HyperFrames (HTML/GSAP) visual render engines, edit Whisper
  subtitles, and launch/sync with the Windows C# WPF Desktop App via MCP or CLI.
---

# KinetixAI Video Producer Skill (Antigravity MCP Integration)

Use this skill whenever the user asks to produce, render, edit, or preview a video in KinetixAI, or asks to launch/control the KinetixAI Desktop App.

## 1. Available MCP Tools (`kinetix-ai` MCP Server)

If the `kinetix-ai` MCP server is active in the session, call these MCP tools directly:

- `kinetix_produce_video(project_id, source_url, engine_type, script_text, template_id)`
  - Runs the 5-step Clean Architecture pipeline (`yt-dlp` -> `FFmpeg` -> `Whisper` -> `Remotion` or `HyperFrames` -> `FFmpeg` MP4).
- `kinetix_update_subtitles(project_id, subtitles_input, engine_type)`
  - Updates the subtitle segments (`Line 1|Line 2` or JSON array) and re-renders the visual overlay and final MP4.
- `kinetix_list_projects()` / `kinetix_get_project(project_id)`
  - Lists or inspects projects in `workspace/projects.json`.
- `kinetix_launch_desktop_app()`
  - Launches the native Windows C# WPF Desktop App (`KinetixAI.Desktop.exe`), which auto-syncs with `workspace/projects.json` every 3 seconds.

## 2. Direct Python / CLI Execution (Instant Fallback)

You can also invoke the MCP tools or CLI directly from the workspace root `D:\AI_Learning_Repository\KinetixAI`:

```powershell
# Produce a video via MCP tool function directly
uv run python -c "from src.presentation.mcp.mcp_server import kinetix_produce_video; print(kinetix_produce_video('ai_video_01', 'demo://sample', 'hyperframes', 'Xin chào KinetixAI|Điều khiển trực tiếp bởi AI Antigravity qua MCP|Render siêu tốc với HyperFrames & FFmpeg'))"

# Launch the Windows WPF Desktop App
uv run python -c "from src.presentation.mcp.mcp_server import kinetix_launch_desktop_app; print(kinetix_launch_desktop_app())"
```
