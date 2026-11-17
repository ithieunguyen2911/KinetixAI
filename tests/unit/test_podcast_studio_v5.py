"""Unit & Integration Tests for v5.0 Broadcast Podcast Studio, Structured Script Parser, .ASS Wrapping & Repo Resilience."""

import json
from pathlib import Path

from src.domain.entities.subtitle_segment import SubtitleSegment
from src.domain.entities.video_project import VideoProject
from src.domain.services.podcast_script_parser import PodcastScriptParser
from src.infrastructure.audio.audio_library_adapter import StudioAudioLibraryAdapter
from src.infrastructure.processors.ffmpeg_adapter import FfmpegAdapter
from src.infrastructure.repositories.json_project_repository import JsonProjectRepository
from src.infrastructure.tts.tts_voice_adapter import TtsVoiceAdapter


def test_podcast_script_parser_episode_1_strips_stage_cues_and_notes() -> None:
    """Verify structured podcast script parsing strips timestamps, bracketed SFX/BGM cues & recording notes."""
    sample_file = Path(__file__).resolve().parents[2] / "docs" / "sample_podcast_tap_01_tuoi_30.txt"
    raw_script = sample_file.read_text(encoding="utf-8")

    parsed = PodcastScriptParser.parse(raw_script)

    assert "TẬP 1: TUỔI 30" in parsed.episode_title
    assert parsed.is_structured_narrative is True
    assert parsed.recommended_voice_id == "vi-VN-NamMinhNeural"
    assert len(parsed.chapters) == 5
    assert parsed.bgm_transition_chapter_index == 3
    assert parsed.chapters[0].mood == "melancholic"
    assert parsed.chapters[3].mood == "hopeful"
    assert parsed.chapters[4].mood == "hopeful"

    # Both diegetic Hook SFX cues extracted
    sfx_ids = [c.sfx_id for c in parsed.sfx_cues]
    assert "sfx_fan_shutdown" in sfx_ids
    assert "sfx_phone_vibrate" in sfx_ids
    assert parsed.chapters[0].lead_in_sec >= 2.0

    # Zero stage directions or recording notes leaked into captions or spoken text
    all_captions = " ".join(t.caption_text for t in parsed.turns)
    all_spoken = " ".join(t.spoken_text for t in parsed.turns)
    assert "0:00" not in all_captions
    assert "4:15" not in all_captions
    assert "[Âm thanh" not in all_captions
    assert "[Nhạc nền" not in all_captions
    assert "GỢI Ý THU ÂM" not in all_captions
    assert "Nhịp điệu (Pacing)" not in all_captions
    assert "[Âm thanh" not in all_spoken
    assert "GỢI Ý THU ÂM" not in all_spoken

    # Hook psychological pauses injected on anchor phrases
    hook_spoken = " ".join(t.spoken_text for t in parsed.turns if t.chapter_index == 0)
    assert "[pause" in hook_spoken

    # Every caption phrase is wrapped/chunked to readable length
    for turn in parsed.turns:
        assert 1 <= len(turn.caption_text.split()) <= 30


def test_json_project_repository_per_item_fault_isolation_and_hot_reload(tmp_path: Path) -> None:
    """Verify a corrupt JSON project entry never wipes valid projects, and external writes hot-reload."""
    db_file = tmp_path / "projects.json"
    repo_a = JsonProjectRepository(db_file)
    valid_proj = VideoProject(project_id="valid_01", source_url="demo://sample")
    repo_a.save(valid_proj)

    # Inject a corrupt item alongside valid_01 and a second valid item externally
    raw_items = json.loads(db_file.read_text(encoding="utf-8"))
    corrupt_entry = {"project_id": "", "engine_type": "non_existent_engine_xyz"}
    second_valid = VideoProject(project_id="valid_02", source_url="demo://sample").to_dict()
    db_file.write_text(
        json.dumps([corrupt_entry, raw_items[0], second_valid], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # repo_a must hot-reload on list_all() and isolate the corrupt entry without losing valid_01 & valid_02
    loaded_ids = [p.project_id for p in repo_a.list_all()]
    assert "valid_01" in loaded_ids
    assert "valid_02" in loaded_ids
    assert len(loaded_ids) == 2


def test_new_piano_acoustic_bgm_and_diegetic_sfx_presets(tmp_path: Path) -> None:
    """Verify new musical BGM beds and diegetic Hook SFX synthesize valid WAV files."""
    lib = StudioAudioLibraryAdapter()
    bgm_ids = [b["preset_id"] for b in lib.list_bgm_presets()]
    sfx_ids = [s["sfx_id"] for s in lib.list_sfx_presets()]

    assert "bgm_piano_melancholic" in bgm_ids
    assert "bgm_inspiring_acoustic" in bgm_ids
    assert "sfx_fan_shutdown" in sfx_ids
    assert "sfx_phone_vibrate" in sfx_ids

    p_mel = lib.resolve_bgm("bgm_piano_melancholic", tmp_path, duration_sec=3.0)
    p_ins = lib.resolve_bgm("bgm_inspiring_acoustic", tmp_path, duration_sec=3.0)
    s_fan = lib.resolve_sfx("sfx_fan_shutdown", tmp_path)
    s_vib = lib.resolve_sfx("sfx_phone_vibrate", tmp_path)

    for wav_file in (p_mel, p_ins, s_fan, s_vib):
        assert wav_file.exists()
        assert wav_file.stat().st_size > 2000


def test_tts_mid_sentence_pause_and_lead_in_podcast_synthesis(tmp_path: Path) -> None:
    """Verify mid-sentence [pause] splicing and lead_in_sec silence offset in podcast synthesis."""
    tts = TtsVoiceAdapter(profiles_file=tmp_path / "profiles.json")
    turns = [
        {
            "turn_id": "turn_001",
            "chapter_index": 0,
            "chapter_title": "HOOK",
            "speaker_name": "Narrator",
            "voice_id": "win-sapi-studio",
            "emotion": "late_night",
            "rate": 0.95,
            "text": "30 tuổi. [pause 500ms] Kể chuyện lại từ đầu.",
            "caption_text": "30 tuổi. Kể chuyện lại từ đầu.",
            "pause_after_ms": 300,
            "lead_in_sec": 1.5,
        }
    ]
    out_wav, segs = tts.synthesize_podcast_script(turns, tmp_path / "pod.wav", genre="late_night_story")
    assert out_wav.exists()
    assert len(segs) == 1
    assert segs[0]["start_time"] >= 1.45
    assert segs[0]["end_time"] > segs[0]["start_time"] + 0.5
    assert "[pause" not in segs[0]["text"]


def test_ffmpeg_render_podcast_video_with_wrapped_ass_and_waveform(tmp_path: Path) -> None:
    """Verify broadcast podcast video compositor generates H.264/AAC MP4 + .ass/.srt/.vtt with live waveform."""
    lib = StudioAudioLibraryAdapter()
    ffmpeg = FfmpegAdapter()

    voice_wav = lib.resolve_bgm("bgm_ambient_pad", tmp_path, duration_sec=4.0)
    bgm_1 = lib.resolve_bgm("bgm_piano_melancholic", tmp_path, duration_sec=4.0)
    bgm_2 = lib.resolve_bgm("bgm_inspiring_acoustic", tmp_path, duration_sec=4.0)
    sfx_fan = lib.resolve_sfx("sfx_fan_shutdown", tmp_path)

    subs = [
        SubtitleSegment(
            start_time=0.2,
            end_time=2.0,
            text="Còn tôi thức dậy nhìn dàn máy đào tiền ảo đã tắt ngấm, và một khoản nợ dài hơn cả thanh xuân của mình.",
        ),
        SubtitleSegment(
            start_time=2.0,
            end_time=3.9,
            text="Tuổi 30 không phải là dấu chấm hết mà là lúc bắt đầu xây dựng lại từ nền móng vững chắc.",
        ),
    ]
    chapters = [
        {"chapter_index": 0, "title": "HOOK: CÚ NGÃ Ở TUỔI 30", "mood": "melancholic", "start_time": 0.0, "end_time": 2.0},
        {"chapter_index": 1, "title": "BƯỚC NGOẶT: LÀM LẠI TỪ ĐẦU", "mood": "hopeful", "start_time": 2.0, "end_time": 4.0},
    ]

    out_mp4 = tmp_path / "podcast_render_test.mp4"
    actual = ffmpeg.render_podcast_video(
        voice_audio_path=voice_wav,
        output_path=out_mp4,
        subtitles=subs,
        episode_title="TẬP 1: TUỔI 30 VÀ KHOẢN NỢ",
        speaker_label="VOICE • NAM MINH",
        chapters=chapters,
        bgm_primary_path=bgm_1,
        bgm_secondary_path=bgm_2,
        bgm_transition_sec=2.0,
        bgm_volume=0.14,
        sfx_events=[{"path": sfx_fan, "timestamp_sec": 0.0, "volume": 0.7}],
    )

    assert actual.exists()
    probe = ffmpeg.probe_media(actual)
    assert probe["width"] == 1280
    assert probe["height"] == 720
    assert probe["video_codec"] == "h264"
    assert probe["duration_seconds"] >= 3.5
    assert actual.with_suffix(".srt").exists()
    assert actual.with_suffix(".vtt").exists()
