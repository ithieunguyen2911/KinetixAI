"""StudioAudioLibraryAdapter - Deterministic Curated BGM & SFX Sound Engine (HyperFrames media-use pattern)."""

from pathlib import Path
import subprocess
from typing import Any, Dict, List

from src.domain.interfaces.audio_library import IAudioAssetLibrary


def _felt_piano_chord_expr(root_hz: float, third_hz: float, fifth_hz: float, color_hz: float) -> str:
    """Build rich felt-hammer piano harmonic overtone voicing (0.5x bass + 1x + 0.42*2x + 0.16*3x)."""
    bass_hz = round(root_hz * 0.5, 2)
    r2, r3 = round(root_hz * 2.0, 2), round(root_hz * 3.0, 2)
    t2, t3 = round(third_hz * 2.0, 2), round(third_hz * 3.0, 2)
    f2 = round(fifth_hz * 2.0, 2)
    c2 = round(color_hz * 2.0, 2)
    return (
        f"(0.13*sin(2*PI*{bass_hz}*t)"
        f"+0.16*(sin(2*PI*{root_hz}*t)+0.42*sin(2*PI*{r2}*t)+0.16*sin(2*PI*{r3}*t))"
        f"+0.12*(sin(2*PI*{third_hz}*t)+0.42*sin(2*PI*{t2}*t)+0.16*sin(2*PI*{t3}*t))"
        f"+0.10*(sin(2*PI*{fifth_hz}*t)+0.42*sin(2*PI*{f2}*t))"
        f"+0.07*(sin(2*PI*{color_hz}*t)+0.32*sin(2*PI*{c2}*t)))"
    )


class StudioAudioLibraryAdapter(IAudioAssetLibrary):
    """Generates and resolves curated royalty-free studio BGM beds & SFX audio cues via FFmpeg synthesis."""

    SAMPLE_RATE: int = 24000

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
        {
            "preset_id": "bgm_piano_melancholic",
            "name": "Ambient Piano Melancholic (Late Night)",
            "bpm": 68,
            "mood": "Melancholic / Storytelling",
            "post_filter": "lowpass=f=2100,highpass=f=55,aecho=0.8:0.86:72|138:0.30|0.20",
            "expr": (
                "(1-exp(-35*mod(t,1.75)))*(0.28+0.72*exp(-1.15*mod(t,1.75)))*min(1,28*(1.75-mod(t,1.75)))*("
                f"lt(mod(t,14),3.5)*{_felt_piano_chord_expr(220.00, 261.63, 329.63, 493.88)}"
                f"+gte(mod(t,14),3.5)*lt(mod(t,14),7.0)*{_felt_piano_chord_expr(174.61, 220.00, 261.63, 329.63)}"
                f"+gte(mod(t,14),7.0)*lt(mod(t,14),10.5)*{_felt_piano_chord_expr(146.83, 220.00, 293.66, 349.23)}"
                f"+gte(mod(t,14),10.5)*{_felt_piano_chord_expr(164.81, 207.65, 246.94, 329.63)}"
                ")"
            ),
        },
        {
            "preset_id": "bgm_inspiring_acoustic",
            "name": "Inspiring Warm Acoustic & Piano (Hopeful)",
            "bpm": 76,
            "mood": "Hopeful / Turnaround",
            "post_filter": "lowpass=f=2100,highpass=f=55,aecho=0.8:0.86:72|138:0.30|0.20",
            "expr": (
                "(1-exp(-35*mod(t,1.6)))*(0.28+0.72*exp(-1.15*mod(t,1.6)))*min(1,28*(1.6-mod(t,1.6)))*("
                f"lt(mod(t,12.8),3.2)*{_felt_piano_chord_expr(261.63, 329.63, 392.00, 493.88)}"
                f"+gte(mod(t,12.8),3.2)*lt(mod(t,12.8),6.4)*{_felt_piano_chord_expr(196.00, 246.94, 293.66, 392.00)}"
                f"+gte(mod(t,12.8),6.4)*lt(mod(t,12.8),9.6)*{_felt_piano_chord_expr(220.00, 261.63, 329.63, 392.00)}"
                f"+gte(mod(t,12.8),9.6)*{_felt_piano_chord_expr(174.61, 220.00, 261.63, 392.00)}"
                ")"
            ),
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
        {
            "sfx_id": "sfx_fan_shutdown",
            "name": "PC Cooling Fan Spin-Down",
            "category": "Diegetic / Podcast",
            "duration_sec": 2.35,
            "post_filter": "lowpass=f=1500,highpass=f=40,afade=t=in:st=0:d=0.04,afade=t=out:st=2.05:d=0.30",
            "expr": (
                "(0.38*sin(2*PI*(45*t+143.33*(1-exp(-1.5*t))))"
                "+0.18*sin(4*PI*(45*t+143.33*(1-exp(-1.5*t))))"
                "+0.24*(random(0)-0.5)*exp(-1.3*max(0,t-0.2)))"
                "*exp(-1.35*max(0,t-0.22))"
            ),
        },
        {
            "sfx_id": "sfx_phone_vibrate",
            "name": "Phone Notification Vibrate",
            "category": "Diegetic / Podcast",
            "duration_sec": 1.40,
            "post_filter": "lowpass=f=2800,afade=t=out:st=1.28:d=0.12",
            "expr": (
                "0.36*(sin(2*PI*145*t)+0.55*sin(2*PI*290*t)+0.20*sin(2*PI*435*t))"
                "*(0.82+0.18*sin(2*PI*28*t))"
                "*(between(t,0.0,0.32)+between(t,0.48,0.80)+between(t,0.96,1.28))"
                "+0.15*sin(2*PI*880*t)*exp(-14*t)"
                "+0.17*sin(2*PI*1174.66*t)*exp(-9*max(0,t-0.09))*gt(t,0.09)"
            ),
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
        af_parts: List[str] = []
        if item.get("post_filter"):
            af_parts.append(str(item["post_filter"]))
        af_parts.append(f"afade=t=in:st=0:d=0.4,afade=t=out:st={fade_out_st:.2f}:d=0.8")
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"aevalsrc='{item['expr']}':s={self.SAMPLE_RATE}:d={dur:.2f}",
            "-af",
            ",".join(af_parts),
            "-ar",
            str(self.SAMPLE_RATE),
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
            f"aevalsrc='{item['expr']}':s={self.SAMPLE_RATE}:d={dur:.2f}",
        ]
        if item.get("post_filter"):
            cmd.extend(["-af", str(item["post_filter"])])
        cmd.extend(
            [
                "-ar",
                str(self.SAMPLE_RATE),
                "-ac",
                "1",
                "-acodec",
                "pcm_s16le",
                str(target),
            ]
        )
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return target
