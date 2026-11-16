"""Integration tests for FastAPI REST API endpoints."""

from pathlib import Path
from fastapi.testclient import TestClient

from src.presentation.api.main import create_app


def test_fastapi_health_and_project_lifecycle(tmp_path: Path) -> None:
    app = create_app(workspace_root=tmp_path)
    client = TestClient(app)

    # 1. Health endpoint
    health_res = client.get("/api/v1/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["status"] == "ok"
    assert "remotion" in health_data["supported_engines"]
    assert "hyperframes" in health_data["supported_engines"]

    # 1b. Inspect source metadata endpoint
    inspect_res = client.post("/api/v1/sources/inspect", json={"source_url": "demo://sample"})
    assert inspect_res.status_code == 200
    assert inspect_res.json()["source_type"] == "demo"
    assert inspect_res.json()["resolution"] == "1280x720"

    # 2. Create and run project via POST /api/v1/projects
    create_res = client.post(
        "/api/v1/projects",
        json={
            "project_id": "api_test_01",
            "source_url": "demo://sample",
            "engine_type": "hyperframes",
            "template_id": "CaptionTemplate",
            "script_text": "API Line 1|API Line 2",
        },
    )
    assert create_res.status_code == 200
    proj_data = create_res.json()
    assert proj_data["project_id"] == "api_test_01"
    assert proj_data["status"] == "completed"
    assert proj_data["progress_percent"] == 100
    assert len(proj_data["subtitles"]) == 2

    # 3. Get project details
    get_res = client.get("/api/v1/projects/api_test_01")
    assert get_res.status_code == 200
    assert get_res.json()["engine_type"] == "hyperframes"

    # 4. Update subtitles and switch engine to remotion
    update_res = client.post(
        "/api/v1/projects/api_test_01/subtitles",
        json={
            "engine_type": "remotion",
            "subtitles": [
                {"start_time": 0.0, "end_time": 3.0, "text": "Updated Remotion Line 1", "words": []},
                {"start_time": 3.0, "end_time": 6.0, "text": "Updated Remotion Line 2", "words": []},
            ],
        },
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["engine_type"] == "remotion"
    assert updated_data["subtitles"][0]["text"] == "Updated Remotion Line 1"

    # 5. Probe media via ffprobe endpoint
    probe_res = client.get("/api/v1/projects/api_test_01/probe")
    assert probe_res.status_code == 200
    probe_data = probe_res.json()
    assert probe_data["width"] == 1280
    assert probe_data["height"] == 720
    assert probe_data["video_codec"] == "h264"

    # 6. Trim final video via FFmpeg trim endpoint
    trim_res = client.post(
        "/api/v1/projects/api_test_01/trim",
        json={"start_time": 0.0, "end_time": 4.0},
    )
    assert trim_res.status_code == 200
    assert trim_res.json()["status"] == "completed"

    # 7. NLE Speed, Color Grade, Reframe, Audio Master & Snapshot endpoints
    speed_res = client.post(
        "/api/v1/projects/api_test_01/speed",
        json={"speed_factor": 1.25},
    )
    assert speed_res.status_code == 200

    grade_res = client.post(
        "/api/v1/projects/api_test_01/color-grade",
        json={"look_preset": "teal_orange", "brightness": 0.03, "contrast": 1.08, "saturation": 1.12},
    )
    assert grade_res.status_code == 200

    reframe_res = client.post(
        "/api/v1/projects/api_test_01/reframe",
        json={"aspect_ratio": "9:16", "blur_background": True},
    )
    assert reframe_res.status_code == 200

    audio_res = client.post(
        "/api/v1/projects/api_test_01/audio-master",
        json={"remove_silences": False, "normalize_loudness": True, "mix_bgm": True, "bgm_volume": 0.15},
    )
    assert audio_res.status_code == 200

    snap_res = client.post(
        "/api/v1/projects/api_test_01/snapshot",
        json={"timestamp_sec": 1.0},
    )
    assert snap_res.status_code == 200
    assert Path(snap_res.json()["snapshot_path"]).exists()

    # 7b. Split, Concat & Multi-format Subtitle Export (.srt, .vtt, .transcript.json)
    split_res = client.post(
        "/api/v1/projects/api_test_01/split",
        json={"split_time": 1.5},
    )
    assert split_res.status_code == 200
    split_data = split_res.json()
    assert Path(split_data["part_a_path"]).exists()
    assert Path(split_data["part_b_path"]).exists()

    concat_res = client.post(
        "/api/v1/projects/api_test_01/concat",
        json={"clip_paths": [split_data["part_a_path"], split_data["part_b_path"]], "transition": "none"},
    )
    assert concat_res.status_code == 200

    for fmt in ("srt", "vtt", "json"):
        exp_res = client.get(f"/api/v1/projects/api_test_01/subtitles/export?fmt={fmt}")
        assert exp_res.status_code == 200
        assert Path(exp_res.json()["export_path"]).exists()

    # 7c. v3.0 Studio Catalog, Context, Scenes CRUD+Clone, Characters CRUD+Clone, Voiceover, Sound Library, FX, Beat-Cut & Project Clone/Delete
    catalog_res = client.get("/api/v1/catalog/studio")
    assert catalog_res.status_code == 200
    assert len(catalog_res.json()["bgm_presets"]) >= 5

    ctx_res = client.post(
        "/api/v1/projects/api_test_01/context",
        json={"world_setting": "Futuristic Broadcast Room", "lighting_mood": "Cyan Key"},
    )
    assert ctx_res.status_code == 200
    assert ctx_res.json()["scene_context"]["world_setting"] == "Futuristic Broadcast Room"

    char_res = client.post(
        "/api/v1/projects/api_test_01/characters",
        json={
            "action": "upsert",
            "character": {"character_id": "char_vip", "name": "Hieu Nguyen", "role": "Director", "voice_id": "win-sapi-studio"},
        },
    )
    assert char_res.status_code == 200
    assert any(c["character_id"] == "char_vip" for c in char_res.json()["characters"])

    scene_res = client.post(
        "/api/v1/projects/api_test_01/scenes",
        json={
            "action": "upsert",
            "scene": {"scene_id": "scene_custom", "title": "Opening Hook", "character_id": "char_vip", "narration_text": "Hook line"},
        },
    )
    assert scene_res.status_code == 200
    assert any(s["scene_id"] == "scene_custom" for s in scene_res.json()["scenes"])

    vo_res = client.post(
        "/api/v1/projects/api_test_01/voiceover",
        json={"voice_id": "win-sapi-studio", "rate": 1.0, "text": "Testing studio voiceover"},
    )
    assert vo_res.status_code == 200

    snd_res = client.post(
        "/api/v1/projects/api_test_01/sound-library",
        json={"bgm_preset": "bgm_cyber_pulse", "bgm_volume": 0.15, "sfx_id": "sfx_whoosh_fast", "sfx_timestamp": 0.2},
    )
    assert snd_res.status_code == 200

    fx_res = client.post(
        "/api/v1/projects/api_test_01/fx-motion",
        json={"transition_preset": "fade_black", "animation_preset": "neon_glow_pulse"},
    )
    assert fx_res.status_code == 200

    beat_res = client.post(
        "/api/v1/projects/api_test_01/beat-cut",
        json={"bpm": 120, "align_subtitles": True, "pulse_flash": True},
    )
    assert beat_res.status_code == 200
    assert len(beat_res.json()["beat_timestamps"]) >= 4
    assert len(beat_res.json()["audit_logs"]) >= 5

    clone_res = client.post("/api/v1/projects/api_test_01/clone", json={"new_project_id": "api_test_01_cloned"})
    assert clone_res.status_code == 200
    assert clone_res.json()["project_id"] == "api_test_01_cloned"

    # 7d. v4.0 Interactive Timeline Clip CRUD (Add / Update / Split / Clone / Delete / Render)
    add_clip = client.post(
        "/api/v1/projects/api_test_01/timeline-clips",
        json={"action": "add", "clip": {"track_id": "S1", "label": "Added Caption Clip", "start_time": 0.0, "end_time": 1.8}},
    )
    assert add_clip.status_code == 200
    added_id = add_clip.json()["timeline_clips"][-1]["clip_id"]

    split_clip = client.post(
        "/api/v1/projects/api_test_01/timeline-clips",
        json={"action": "split", "clip_id": added_id, "split_time": 0.9},
    )
    assert split_clip.status_code == 200

    clone_clip = client.post(
        "/api/v1/projects/api_test_01/timeline-clips",
        json={"action": "clone", "clip_id": added_id},
    )
    assert clone_clip.status_code == 200

    # 7e. VoiceStudio Voice Design, Podcast Generation & Auto Dubbing
    vd_res = client.post(
        "/api/v1/voices/design",
        json={"name": "TechStoryVoice", "prompt_description": "Giọng nam trầm ấm kể chuyện công nghệ", "seed": 12},
    )
    assert vd_res.status_code == 200
    assert vd_res.json()["mode"] == "designed"

    pod_res = client.post(
        "/api/v1/projects/api_test_01/podcast",
        json={
            "raw_content": "Host: Câu mở đầu podcast.|Guest: Phần trả lời đầy cảm hứng.",
            "genre": "podcast_dialogue",
            "host_voice_id": "win-sapi-studio",
            "guest_voice_id": "win-sapi-studio",
        },
    )
    assert pod_res.status_code == 200
    assert len(pod_res.json()["podcast_turns"]) == 2

    dub_res = client.post(
        "/api/v1/projects/api_test_01/dubbing",
        json={"target_language": "en-US", "voice_id": "win-sapi-studio", "translated_lines": ["Hello World"]},
    )
    assert dub_res.status_code == 200

    del_res = client.delete("/api/v1/projects/api_test_01_cloned")
    assert del_res.status_code == 200 and del_res.json()["deleted"] is True

    # 8. Download final video stream
    video_res = client.get("/api/v1/projects/api_test_01/video")
    assert video_res.status_code == 200
    assert len(video_res.content) > 1000
