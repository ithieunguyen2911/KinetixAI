"""StudioAudioLibraryAdapter - Deterministic Curated BGM & SFX Sound Engine (HyperFrames media-use pattern)."""

from pathlib import Path
import subprocess
from typing import Any, Dict, List

from src.domain.interfaces.audio_library import IAudioAssetLibrary


class StudioAudioLibraryAdapter(IAudioAssetLibrary):
    """Generates and resolves curated royalty-free studio BGM beds & SFX audio cues via FFmpeg synthesis."""

    BGM_CATALOG: List[Dict[str, Any]] = [
        {
            "preset_id": "bgm_ambient_pad",
            "name": "Warm Ambient Pad (A Minor)",
            "bpm": 90,
            "mood": "Clean Studio / Explainer",
            "expr": "0.18*sin(2*PI*220*t)+0.14*sin(2*PI*261.63*t)+0.14*sin(2*PI*329.63*t)+0.08*sin(2*PI*440*t)",
        },
        {
            "preset_id": "bgm_cyber_pulse",
            "name": "Tech Pulse 120 BPM",
            "bpm": 120,
            "mood": "Energetic / Tech Demo",
            "expr": "(0.24*sin(2*PI*110*t)+0.14*sin(2*PI*220*t))*(0.35+0.65*pow(sin(2*PI*2*t),2))+0.10*sin(2*PI*440*t)",
        },
        {
            "preset_id": "bgm_lofi_chill",
            "name": "Lo-Fi Study Warmth",
            "bpm": 85,
            "mood": "Relaxed / Narrative",
            "expr": "0.16*sin(2*PI*196*t)+0.13*sin(2*PI*246.94*t)+0.11*sin(2*PI*293.66*t)+0.06*sin(2*PI*392*t)",
        },
        {
            "preset_id": "bgm_news_broadcast",
            "name": "Newsroom Clock Tick 128 BPM",
            "bpm": 128,
            "mood": "Broadcast / Updates",
            "expr": "0.20*sin(2*PI*146.83*t)*(0.5+0.5*sin(2*PI*4.26*t))+0.12*sin(2*PI*293.66*t)+0.08*sin(2*PI*880*t)*exp(-4*mod(t,0.468))",
        },
        {
            "preset_id": "bgm_dramatic_rise",
            "name": "Cinematic Tension Swell",
            "bpm": 100,
            "mood": "Dramatic / Reveal",
            "expr": "min(0.9,0.2+0.1*t)*(0.22*sin(2*PI*82.41*t)+0.18*sin(2*PI*123.47*t)+0.12*sin(2*PI*246.94*t))",
        },
    ]

    SFX_CATALOG: List[Dict[str, Any]] = [
        {
            "sfx_id": "sfx_whoosh_fast",
            "name": "Transition Whoosh",
            "category": "Transition",
            "duration_sec": 0.45,
            "expr": "0.45*sin(2*PI*(180+720*t)*t)*exp(-5.5*t)",
        },
        {
            "sfx_id": "sfx_pop_bubble",
            "name": "UI Caption Pop",
            "category": "UI / Caption",
            "duration_sec": 0.22,
            "expr": "0.55*sin(2*PI*(320+900*t)*t)*exp(-16*t)",
        },
        {
            "sfx_id": "sfx_glitch_digital",
            "name": "Digital Glitch Zap",
            "category": "Tech / Cut",
            "duration_sec": 0.35,
            "expr": "0.45*(sin(2*PI*980*t)+0.7*sin(2*PI*1420*t)*sin(2*PI*45*t))*exp(-7*t)",
        },
        {
            "sfx_id": "sfx_cinematic_hit",
            "name": "Sub Bass Impact Boom",
            "category": "Impact / Title",
            "duration_sec": 0.85,
            "expr": "0.65*sin(2*PI*(110*exp(-2.8*t)+40)*t)*exp(-2.9*t)",
        },
        {
            "sfx_id": "sfx_camera_shutter",
            "name": "Camera Snap Click",
            "category": "Snapshot / Frame",
            "duration_sec": 0.18,
            "expr": "0.60*sin(2*PI*1200*t)*exp(-28*t)+0.35*sin(2*PI*850*t)*exp(-25*max(0,t-0.06))*gt(t,0.06)",
        },
        {
            "sfx_id": "sfx_chime_ding",
            "name": "Highlight Crystal Chime",
            "category": "Accent",
            "duration_sec": 0.65,
            "expr": "0.40*(sin(2*PI*1046.5*t)+0.6*sin(2*PI*1567.98*t))*exp(-4.5*t)",
        },
    ]

    def list_bgm_presets(self) -> List[Dict[str, Any]]:
        return [
            {"preset_id": b["preset_id"], "name": b["name"], "bpm": b["bpm"], "mood": b["mood"]}
            for b in self.BGM_CATALOG
        ]

    def list_sfx_presets(self) -> List[Dict[str, Any]]:
        return [
            {
                "sfx_id": s["sfx_id"],
                "name": s["name"],
                "category": s["category"],
                "duration_sec": s["duration_sec"],
            }
            for s in self.SFX_CATALOG
        ]

    def resolve_bgm(
        self,
        preset_id: str,
        output_dir: Path,
        duration_sec: float = 8.0,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        item = next((b for b in self.BGM_CATALOG if b["preset_id"] == preset_id), self.BGM_CATALOG[0])
        target = output_dir / f"{item['preset_id']}.wav"
        dur = max(2.0, float(duration_sec))
        fade_out_st = max(0.5, dur - 0.8)
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"aevalsrc='{item['expr']}':s=16000:d={dur:.2f}",
            "-af",
            f"afade=t=in:st=0:d=0.4,afade=t=out:st={fade_out_st:.2f}:d=0.8",
            "-ac",
            "1",
            "-acodec",
            "pcm_s16le",
            str(target),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return target

    def resolve_sfx(
        self,
        sfx_id: str,
        output_dir: Path,
    ) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        item = next((s for s in self.SFX_CATALOG if s["sfx_id"] == sfx_id), self.SFX_CATALOG[0])
        target = output_dir / f"{item['sfx_id']}.wav"
        dur = float(item["duration_sec"])
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"aevalsrc='{item['expr']}':s=16000:d={dur:.2f}",
            "-ac",
            "1",
            "-acodec",
            "pcm_s16le",
            str(target),
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return target
