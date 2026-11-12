# KinetixAI (FlowVids-AI) Project Rules & Antigravity MCP Guide

1. **Clean Architecture & SOLID**: All code in `src/` strictly follows `.specify/memory/constitution.md` (`domain` -> `application` -> `infrastructure` -> `presentation`).
2. **Antigravity MCP Integration**:
   - The MCP server is implemented at `src/presentation/mcp/mcp_server.py` (`kinetix-ai`) and registered in `~/.gemini/config/mcp_config.json` and `.agents/mcp_config.json`.
   - When the user asks AI Antigravity to produce a video or launch the Desktop App, use the `kinetix-ai` MCP tools (`kinetix_produce_video`, `kinetix_update_subtitles`, `kinetix_launch_desktop_app`) or invoke `src.presentation.mcp.mcp_server` via `uv run`.
   - The C# WPF Desktop App (`desktop_app/KinetixAI.Desktop`) automatically polls `/api/v1/projects` every 3 seconds and updates the UI in real time whenever Antigravity produces a new video.
