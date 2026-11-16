"""Integration tests for the KinetixAI Model Context Protocol (MCP) Server & AI Bridge."""

from pathlib import Path
from fastapi.testclient import TestClient

from src.presentation.api.main import create_app
from src.presentation.mcp.mcp_server import (
    kinetix_apply_beat_cut,
    kinetix_apply_color_grade,
    kinetix_apply_sound_library,
    kinetix_apply_transition_animation,
    kinetix_capture_snapshot,
    kinetix_change_speed,
    kinetix_clone_project,
    kinetix_clone_voice,
    kinetix_delete_project,
    kinetix_design_voice,
    kinetix_dub_video,
    kinetix_generate_voiceover,
    kinetix_get_project,
    kinetix_health_check,
    kinetix_inspect_source,
    kinetix_list_projects,
    kinetix_manage_character,
    kinetix_manage_scene,
    kinetix_manage_timeline_clip,
    kinetix_master_audio,
    kinetix_probe_media,
    kinetix_produce_podcast,
    kinetix_produce_video,
    kinetix_reframe_video,
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
    trimmed = kinetix_trim_video("mcp_ai_demo", start_time=0.0, end_time=4.0, workspace_dir=ws)
    assert Path(trimmed["final_output_path"]).exists()

    # 6. Professional NLE MCP tools (Speed, Color Grade, Reframe, Audio Master, Snapshot)
    sped = kinetix_change_speed("mcp_ai_demo", speed_factor=1.5, workspace_dir=ws)
    assert Path(sped["final_output_path"]).exists()

    graded = kinetix_apply_color_grade(
        "mcp_ai_demo",
        preset="teal_orange",
        brightness=0.02,
        contrast=1.08,
        saturation=1.15,
        workspace_dir=ws,
    )
    assert Path(graded["final_output_path"]).exists()

    reframed = kinetix_reframe_video("mcp_ai_demo", aspect_ratio="1:1", workspace_dir=ws)
    assert Path(reframed["final_output_path"]).exists()

    mastered = kinetix_master_audio(
        "mcp_ai_demo",
        remove_silence=False,
        normalize_loudness=True,
        mix_bgm=True,
        bg_volume=0.15,
        workspace_dir=ws,
    )
    assert Path(mastered["final_output_path"]).exists()

    snap = kinetix_capture_snapshot("mcp_ai_demo", timestamp_sec=0.5, workspace_dir=ws)
    assert Path(snap["snapshot_path"]).exists()

    # 7. v3.0 MCP Storyboard, Character, Voiceover, Sound Library, Beat-Cut & Clone/Delete
    ch = kinetix_manage_character(
        "mcp_ai_demo",
        action="upsert",
        character_id="mcp_char",
        name="Alex Host",
        voice_id="win-sapi-studio",
        workspace_dir=ws,
    )
    assert any(c["character_id"] == "mcp_char" for c in ch["characters"])

    sc = kinetix_manage_scene(
        "mcp_ai_demo",
        action="upsert",
        scene_id="mcp_sc1",
        title="Hook",
        character_id="mcp_char",
        workspace_dir=ws,
    )
    assert any(s["scene_id"] == "mcp_sc1" for s in sc["scenes"])

    vo = kinetix_generate_voiceover("mcp_ai_demo", voice_id="win-sapi-studio", text="MCP Voiceover OK", workspace_dir=ws)
    assert Path(vo["final_output_path"]).exists()

    snd = kinetix_apply_sound_library(
        "mcp_ai_demo",
        bgm_preset="bgm_lofi_chill",
        sfx_id="sfx_pop_bubble",
        sfx_timestamp=0.3,
        workspace_dir=ws,
    )
    assert Path(snd["final_output_path"]).exists()

    fx = kinetix_apply_transition_animation(
        "mcp_ai_demo",
        transition_preset="fade_black",
        animation_preset="spring_pop",
        workspace_dir=ws,
    )
    assert Path(fx["final_output_path"]).exists()

    bc = kinetix_apply_beat_cut("mcp_ai_demo", bpm=120, align_subtitles=True, pulse_flash=True, workspace_dir=ws)
    assert len(bc["beat_timestamps"]) >= 4

    cloned = kinetix_clone_project("mcp_ai_demo", new_project_id="mcp_ai_copy", workspace_dir=ws)
    assert cloned["project_id"] == "mcp_ai_copy"
    deleted = kinetix_delete_project("mcp_ai_copy", workspace_dir=ws)
    assert deleted["deleted"] is True

    # 8. v4.0 MCP Timeline Clip CRUD, VoiceStudio Design & Podcast Production
    tl = kinetix_manage_timeline_clip(
        "mcp_ai_demo", action="add", track_id="S1", label="MCP Cue", start_time=0.0, end_time=1.5, workspace_dir=ws
    )
    assert any(c["label"] == "MCP Cue" for c in tl["timeline_clips"])

    dv = kinetix_design_voice(name="MCPNarrator", prompt_description="Giọng kể chuyện truyền cảm", seed=99, workspace_dir=ws)
    assert dv["mode"] == "designed"

    pod = kinetix_produce_podcast(
        project_id="mcp_podcast_demo",
        raw_content="Host: Xin chào!|Guest: Chào mừng đến với Kinetix Podcast!",
        genre="late_night_story",
        host_voice_id="win-sapi-studio",
        guest_voice_id="win-sapi-studio",
        workspace_dir=ws,
    )
    assert Path(pod["final_output_path"]).exists()
    assert len(pod["podcast_turns"]) == 2


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
