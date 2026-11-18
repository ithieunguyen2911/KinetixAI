"""Unit & Integration Tests for v6.0 Soulful Prosody, VieNeu/Cloud Providers, AI Storyboard B-Roll & Sidechain Audio."""

from pathlib import Path
from fastapi.testclient import TestClient

from src.domain.entities.subtitle_segment import SubtitleSegment
from src.domain.services.podcast_script_parser import PodcastScriptParser
from src.infrastructure.audio.audio_library_adapter import StudioAudioLibraryAdapter
from src.infrastructure.processors.ffmpeg_adapter import FfmpegAdapter
from src.infrastructure.tts.tts_voice_adapter import TtsVoiceAdapter
from src.infrastructure.visuals.storyboard_visual_adapter import StoryboardVisualAdapter
from src.presentation.api.main import create_app


def test_v6_paragraph_beats_and_8_visual_storyboard_scenes() -> None:
    """Verify Episode 1 produces coherent paragraph beats (not 70 isolated calls) and 8 visual storyboard scenes."""
    sample_file = Path(__file__).resolve().parents[2] / "docs" / "sample_podcast_tap_01_tuoi_30.txt"
    parsed = PodcastScriptParser.parse(sample_file.read_text(encoding="utf-8"))

    assert 12 <= len(parsed.paragraph_beats) <= 22
    assert len(parsed.visual_scenes) == 8
    assert parsed.visual_scenes[0]["scene_id"] == "scene_01"
    assert parsed.visual_scenes[-1]["scene_id"] == "scene_08"
    assert parsed.visual_scenes[-1]["end_ratio"] == 1.0

    # Dynamic prosody variations exist across beats (Hook slower & deeper than collapse/turnaround)
    hook_turns = [t for t in parsed.turns if t.chapter_index == 0]
    turnaround_turns = [t for t in parsed.turns if t.chapter_index == 3]
    assert hook_turns[0].rate < turnaround_turns[0].rate
    assert hook_turns[0].pitch_hz <= -4


def test_v6_tts_providers_acoustic_cloning_and_breath_tags(tmp_path: Path) -> None:
    """Verify VieNeu/Gemini/ElevenLabs provider registry, real F0 voice cloning, and [breath] cue synthesis."""
    tts = TtsVoiceAdapter(profiles_file=tmp_path / "profiles.json")
    providers = tts.list_providers()
    provider_ids = {p["provider_id"] for p in providers}
    assert {"edge_prosody_v6", "vieneu_local", "gemini_tts", "elevenlabs_tts"}.issubset(provider_ids)

    voice_ids = {v["voice_id"] for v in tts.list_voices()}
    assert "vieneu-nam-truyen-cam" in voice_ids
    assert "gemini-charon-acting" in voice_ids

    # Configure provider safely into workspace/tmp profiles dir
    cfg = tts.configure_provider("gemini_tts", api_key="", model_id="gemini-2.5-flash-preview-tts")
    assert cfg["provider_id"] == "gemini_tts"

    # Real F0 acoustic voice cloning from clean reference WAV
    lib = StudioAudioLibraryAdapter()
    ref_wav = lib.resolve_bgm("bgm_ambient_pad", tmp_path, duration_sec=2.5)
    cloned = tts.clone_voice("My Podcast Baritone", ref_wav, consent_verified=True, language="vi-VN")
    assert cloned["mode"] == "cloned"
    assert cloned["consent_verified"] is True

    # Breath tag synthesis
    breath_wav = tts.synthesize("[breath] Hôm nay tôi làm lại từ đầu.", tmp_path / "breath.wav", voice_id="win-sapi-studio")
    assert breath_wav.exists() and breath_wav.stat().st_size > 2000


def test_v6_storyboard_visual_adapter_and_ken_burns_sidechain_render(tmp_path: Path) -> None:
    """Verify StoryboardVisualAdapter procedural cinema art + Ken Burns B-roll + sidechain ducked podcast MP4."""
    vis = StoryboardVisualAdapter(allow_remote=False)
    scenes = vis.resolve_storyboard_batch(
        [
            {
                "scene_id": "custom_proc_01",
                "title": "Đêm mưa và dàn máy tắt lịm",
                "visual_prompt": "Late night rain window and desk lamp in city apartment",
                "mood": "melancholic",
                "start_time": 0.0,
                "end_time": 2.2,
            },
            {
                "scene_id": "custom_proc_02",
                "title": "Bình minh bắt đầu lại",
                "visual_prompt": "Tree with deep roots in dark soil growing toward golden sunrise",
                "mood": "hopeful",
                "start_time": 2.2,
                "end_time": 4.4,
            },
        ],
        tmp_path / "storyboard",
    )
    assert len(scenes) == 2
    for sc in scenes:
        img_p = Path(sc["image_path"])
        assert img_p.exists() and img_p.stat().st_size > 15000

    lib = StudioAudioLibraryAdapter()
    ffmpeg = FfmpegAdapter()
    voice_wav = lib.resolve_bgm("bgm_lofi_chill", tmp_path, duration_sec=4.4)
    bgm_1 = lib.resolve_bgm("bgm_piano_melancholic", tmp_path, duration_sec=4.4)
    bgm_2 = lib.resolve_bgm("bgm_inspiring_acoustic", tmp_path, duration_sec=4.4)

    subs = [
        SubtitleSegment(start_time=0.2, end_time=2.1, text="30 tuổi, nhìn lại cú ngã đầu đời."),
        SubtitleSegment(start_time=2.3, end_time=4.2, text="Một cái cây muốn vươn cao thì rễ phải cắm sâu xuống đất tối."),
    ]
    chapters = [
        {"chapter_index": 0, "title": "CHƯƠNG 1: ĐÊM TỐI", "mood": "melancholic", "start_time": 0.0, "end_time": 2.2},
        {"chapter_index": 1, "title": "CHƯƠNG 2: BÌNH MINH", "mood": "hopeful", "start_time": 2.2, "end_time": 4.4},
    ]

    out_mp4 = tmp_path / "v6_broll_podcast.mp4"
    rendered = ffmpeg.render_podcast_video(
        voice_audio_path=voice_wav,
        output_path=out_mp4,
        subtitles=subs,
        episode_title="TẬP 1: TUỔI 30",
        speaker_label="VOICE • VIENEU AI",
        chapters=chapters,
        bgm_primary_path=bgm_1,
        bgm_secondary_path=bgm_2,
        bgm_transition_sec=2.2,
        bgm_volume=0.16,
        scene_visuals=scenes,
    )
    assert rendered.exists()
    probe = ffmpeg.probe_media(rendered)
    assert probe["width"] == 1280
    assert probe["height"] == 720
    assert probe["duration_seconds"] >= 4.0
    ass_text = rendered.with_suffix(".ass").read_text(encoding="utf-8")
    assert "\\fad(" in ass_text


def test_v6_fastapi_voice_providers_and_scene_image_endpoints(tmp_path: Path) -> None:
    """Verify /api/v1/voices/providers GET & POST endpoints in FastAPI."""
    client = TestClient(create_app(workspace_root=tmp_path))
    res = client.get("/api/v1/voices/providers")
    assert res.status_code == 200
    items = res.json()
    assert any(p["provider_id"] == "vieneu_local" for p in items)
