"""Integration tests for the KinetixAI Model Context Protocol (MCP) Server & AI Bridge."""

from pathlib import Path
from fastapi.testclient import TestClient

from src.presentation.api.main import create_app
from src.presentation.mcp.mcp_server import (
    kinetix_get_project,
    kinetix_health_check,
    kinetix_inspect_source,
    kinetix_list_projects,
    kinetix_probe_media,
    kinetix_produce_video,
    kinetix_trim_video,
    kinetix_update_subtitles,
)


def test_mcp_server_tools_produce_and_update_video(tmp_path: Path) -> None:
    ws = str(tmp_path)

    # 1. Health check & Source inspect via MCP tools
    health = kinetix_health_check()
    assert health["status"] == "ok"
    assert health["mcp_server"] == "kinetix-ai"
    assert "remotion" in health["supported_engines"]
    assert "hyperframes" in health["supported_engines"]

    source_meta = kinetix_inspect_source("demo://sample", workspace_dir=ws)
    assert source_meta["source_type"] == "demo"

    # 2. Produce video via MCP tool (Antigravity commanding app to make a video)
    result = kinetix_produce_video(
        project_id="mcp_ai_demo",
        source_url="demo://sample",
        engine_type="hyperframes",
        script_text="Antigravity MCP Command|Automated Video Studio|HyperFrames + FFmpeg",
        workspace_dir=ws,
    )
    assert result["project_id"] == "mcp_ai_demo"
    assert result["status"] == "completed"
    assert result["progress_percent"] == 100
    assert Path(result["final_output_path"]).exists()
    assert len(result["subtitles"]) == 3

    # 3. List, Get & Probe projects via MCP tools
    projects = kinetix_list_projects(workspace_dir=ws)
    assert len(projects) == 1
    fetched = kinetix_get_project("mcp_ai_demo", workspace_dir=ws)
    assert fetched["engine_type"] == "hyperframes"
    probe = kinetix_probe_media("mcp_ai_demo", workspace_dir=ws)
    assert probe["video_codec"] == "h264"

    # 4. Update subtitles and switch engine to Remotion via MCP tool
    updated = kinetix_update_subtitles(
        project_id="mcp_ai_demo",
        subtitles_input="Updated via MCP Line 1|Updated via MCP Line 2",
        engine_type="remotion",
        workspace_dir=ws,
    )
    assert updated["engine_type"] == "remotion"
    assert len(updated["subtitles"]) == 2
    assert updated["subtitles"][0]["text"] == "Updated via MCP Line 1"
    assert len(updated["subtitles"][0]["words"]) == 5

    # 5. Trim video via MCP tool
    trimmed = kinetix_trim_video("mcp_ai_demo", start_time=0.0, end_time=3.0, workspace_dir=ws)
    assert Path(trimmed["final_output_path"]).exists()


def test_fastapi_mcp_command_endpoint(tmp_path: Path) -> None:
    app = create_app(workspace_root=tmp_path)
    client = TestClient(app)

    tools_res = client.get("/api/v1/mcp/tools")
    assert tools_res.status_code == 200
    assert "kinetix_produce_video" in tools_res.json()["tools"]

    cmd_res = client.post(
        "/api/v1/mcp/command",
        json={
            "prompt": "Hãy tạo video quảng cáo KinetixAI bằng HyperFrames",
            "project_id": "antigravity_cmd_01",
            "source_url": "demo://sample",
        },
    )
    assert cmd_res.status_code == 200
    data = cmd_res.json()
    assert data["project_id"] == "antigravity_cmd_01"
    assert data["engine_type"] == "hyperframes"
    assert data["status"] == "completed"
    assert Path(data["final_output_path"]).exists()
