"""TtsVoiceAdapter - Soulful Paragraph Prosody, VieNeu Local Neural TTS, Cloud Acting TTS & Acoustic Voice Cloning."""

import asyncio
import base64
import concurrent.futures
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
from typing import Any, Dict, List, Tuple
import uuid
import wave

import numpy as np

from src.domain.entities.studio_entities import VoiceProfile
from src.domain.interfaces.voice_synthesizer import IVoiceSynthesizer


class TtsVoiceAdapter(IVoiceSynthesizer):
    """Multi-provider neural voice synthesizer supporting Edge Paragraph Prosody v6, VieNeu-TTS v3.8 ONNX, Gemini Acting TTS & ElevenLabs."""

    SAMPLE_RATE: int = 24000
    _TICKS_PER_SEC: float = 10_000_000.0

    CURATED_VOICES: List[Dict[str, Any]] = [
        {
            "voice_id": "vi-VN-HoaiMyNeural",
            "name": "Hoai My (Vietnamese Female)",
            "locale": "vi-VN",
            "gender": "Female",
            "style": "Warm Presenter / Storytelling",
            "provider": "edge_prosody_v6",
            "fallback_pitch_mult": 1.06,
        },
        {
            "voice_id": "vi-VN-NamMinhNeural",
            "name": "Nam Minh (Vietnamese Male)",
            "locale": "vi-VN",
            "gender": "Male",
            "style": "Documentary / Late-Night Confessional",
            "provider": "edge_prosody_v6",
            "fallback_pitch_mult": 0.90,
        },
        {
            "voice_id": "en-US-AriaNeural",
            "name": "Aria Neural (US English Female)",
            "locale": "en-US",
            "gender": "Female",
            "style": "Broadcast / Explainer",
            "provider": "edge_prosody_v6",
            "fallback_pitch_mult": 1.04,
        },
        {
            "voice_id": "en-US-GuyNeural",
            "name": "Guy Neural (US English Male)",
            "locale": "en-US",
            "gender": "Male",
            "style": "Podcast / Newsroom",
            "provider": "edge_prosody_v6",
            "fallback_pitch_mult": 0.92,
        },
        {
            "voice_id": "en-US-JennyNeural",
            "name": "Jenny Neural (US Conversational)",
            "locale": "en-US",
            "gender": "Female",
            "style": "Friendly Assistant",
            "provider": "edge_prosody_v6",
            "fallback_pitch_mult": 1.08,
        },
        {
            "voice_id": "win-sapi-studio",
            "name": "Windows Studio Offline Voice",
            "locale": "local",
            "gender": "Neutral",
            "style": "100% Offline SAPI Synthesizer",
            "provider": "offline_sapi",
            "fallback_pitch_mult": 1.00,
        },
        {
            "voice_id": "vieneu-nam-truyen-cam",
            "name": "VieNeu AI Nam Trầm Truyền Cảm (Local Neural)",
            "locale": "vi-VN",
            "gender": "Male",
            "style": "On-Device Vietnamese Storytelling (Anh Khôi)",
            "provider": "vieneu_local",
            "vieneu_voice": "Anh Khôi",
            "fallback_pitch_mult": 0.90,
        },
        {
            "voice_id": "vieneu-nu-truyen-cam",
            "name": "VieNeu AI Nữ Dịu Dàng Kể Chuyện (Local Neural)",
            "locale": "vi-VN",
            "gender": "Female",
            "style": "On-Device Vietnamese Audiobook (Mỹ Duyên)",
            "provider": "vieneu_local",
            "vieneu_voice": "Mỹ Duyên",
            "fallback_pitch_mult": 1.05,
        },
        {
            "voice_id": "gemini-charon-acting",
            "name": "Gemini Charon Nam Đêm Khuya (Acting AI)",
            "locale": "vi-VN",
            "gender": "Male",
            "style": "Native Audio Acting / Confessional Podcast",
            "provider": "gemini_tts",
            "gemini_voice": "Charon",
            "fallback_pitch_mult": 0.89,
        },
        {
            "voice_id": "elevenlabs-multilingual",
            "name": "ElevenLabs Storytelling v2 (Cloud AI)",
            "locale": "vi-VN",
            "gender": "Male",
            "style": "Expressive Multilingual v2",
            "provider": "elevenlabs_tts",
            "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB",
            "fallback_pitch_mult": 0.91,
        },
    ]

    PROVIDER_SPECS: Dict[str, Dict[str, Any]] = {
        "edge_prosody_v6": {
            "name": "Edge Neural Paragraph Prosody v6",
            "requires_key": False,
            "default_model": "edge-tts-paragraph-stream-v6",
            "env_keys": (),
        },
        "vieneu_local": {
            "name": "VieNeu-TTS v3.8 On-Device Neural & Zero-Shot Cloning",
            "requires_key": False,
            "default_model": "v3nano",
            "env_keys": (),
        },
        "gemini_tts": {
            "name": "Gemini Native Audio Acting TTS",
            "requires_key": True,
            "default_model": "gemini-2.5-flash-preview-tts",
            "env_keys": ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
        },
        "elevenlabs_tts": {
            "name": "ElevenLabs Multilingual v2",
            "requires_key": True,
            "default_model": "eleven_multilingual_v2",
            "env_keys": ("ELEVENLABS_API_KEY",),
        },
    }

    EMOTION_PRESETS: Dict[str, Dict[str, Any]] = {
        "warm": {"rate_mult": 0.98, "pitch_offset": -1, "eq": "equalizer=f=220:t=q:w=1.2:g=2.8"},
        "calm": {"rate_mult": 0.92, "pitch_offset": -3, "eq": "equalizer=f=180:t=q:w=1.0:g=2.2"},
        "late_night": {
            "rate_mult": 0.98,
            "pitch_offset": -2,
            "eq": "highpass=f=72,equalizer=f=180:t=q:w=1.1:g=3.4,equalizer=f=3400:t=q:w=1.4:g=1.2",
        },
        "excited": {"rate_mult": 1.12, "pitch_offset": 6, "eq": "equalizer=f=2800:t=q:w=1.2:g=3"},
        "dramatic": {
            "rate_mult": 0.96,
            "pitch_offset": -4,
            "eq": "highpass=f=70,equalizer=f=155:t=q:w=1.0:g=4.2",
        },
        "mysterious": {"rate_mult": 0.88, "pitch_offset": -7, "eq": "equalizer=f=140:t=q:w=1.0:g=4,lowpass=f=4500"},
        "whisper": {"rate_mult": 0.85, "pitch_offset": 4, "eq": "highpass=f=450,lowpass=f=3200,volume=0.82"},
    }

    _PAUSE_TAG_RE = re.compile(r"\[pause(?:\s+(\d+(?:\.\d+)?)(ms|s))?\]", flags=re.IGNORECASE)
    _BREATH_TAG_RE = re.compile(r"\[(breath|sigh)\]", flags=re.IGNORECASE)
    _EMOTION_TAG_RE = re.compile(r"\[emotion:([a-zA-Z_]+)\]", flags=re.IGNORECASE)
    _SILENT_STRIP_TAG_RE = re.compile(r"\[(?:emotion:[^\]]*|laughter)\]", flags=re.IGNORECASE)

    _vieneu_lock = threading.Lock()
    _vieneu_engines: Dict[str, Any] = {}

    def __init__(
        self,
        profiles_file: Path | None = None,
        providers_file: Path | None = None,
    ) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        self.profiles_file = profiles_file or (repo_root / "workspace" / "voice_profiles.json")
        self.providers_file = providers_file or (self.profiles_file.parent / "tts_providers.json")
        self.profiles_file.parent.mkdir(parents=True, exist_ok=True)
        self.providers_file.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._custom_profiles: Dict[str, VoiceProfile] = {}
        self._provider_configs: Dict[str, Dict[str, str]] = {}
        self._load_profiles()
        self._load_providers()

    # ==========================================================
    # PROFILES & MULTI-PROVIDER CONFIGURATION
    # ==========================================================

    def _load_profiles(self) -> None:
        if not self.profiles_file.exists():
            return
        try:
            raw = json.loads(self.profiles_file.read_text(encoding="utf-8"))
            loaded: Dict[str, VoiceProfile] = {}
            for item in raw:
                prof = VoiceProfile.from_dict(item)
                loaded[prof.profile_id] = prof
            with self._lock:
                self._custom_profiles = loaded
        except Exception:
            with self._lock:
                self._custom_profiles = {}

    def _save_profiles(self) -> None:
        with self._lock:
            self.profiles_file.parent.mkdir(parents=True, exist_ok=True)
            payload = [p.to_dict() for p in self._custom_profiles.values()]
            self.profiles_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def _load_providers(self) -> None:
        if not self.providers_file.exists():
            return
        try:
            raw = json.loads(self.providers_file.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                with self._lock:
                    self._provider_configs = {
                        str(k): dict(v) for k, v in raw.items() if isinstance(v, dict)
                    }
        except Exception:
            with self._lock:
                self._provider_configs = {}

    def _save_providers(self) -> None:
        with self._lock:
            self.providers_file.parent.mkdir(parents=True, exist_ok=True)
            self.providers_file.write_text(
                json.dumps(self._provider_configs, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

    def _resolve_provider_secret(self, provider_id: str) -> Tuple[str, str]:
        """Return (api_key, model_id) merging tts_providers.json and environment variables."""
        self._load_providers()
        spec = self.PROVIDER_SPECS.get(provider_id, {})
        with self._lock:
            saved = dict(self._provider_configs.get(provider_id) or {})

        api_key = str(saved.get("api_key") or "").strip()
        if not api_key:
            for env_name in spec.get("env_keys", ()):
                val = os.environ.get(env_name, "").strip()
                if val:
                    api_key = val
                    break

        model_id = str(saved.get("model_id") or spec.get("default_model") or "").strip()
        return api_key, model_id

    def list_providers(self) -> List[Dict[str, Any]]:
        """Return available TTS providers and real-time availability status."""
        results: List[Dict[str, Any]] = []
        vieneu_installed = importlib.util.find_spec("vieneu") is not None

        for pid, spec in self.PROVIDER_SPECS.items():
            api_key, model_id = self._resolve_provider_secret(pid)
            if pid == "edge_prosody_v6":
                available = True
            elif pid == "vieneu_local":
                available = vieneu_installed
            else:
                available = bool(api_key)

            results.append(
                {
                    "provider_id": pid,
                    "name": spec["name"],
                    "available": available,
                    "requires_key": bool(spec["requires_key"]),
                    "has_api_key": bool(api_key),
                    "model_id": model_id,
                }
            )
        return results

    def configure_provider(self, provider_id: str, api_key: str = "", model_id: str = "") -> Dict[str, Any]:
        """Persist API credentials and/or model override for an expressive TTS provider."""
        pid = (provider_id or "").strip()
        if pid not in self.PROVIDER_SPECS:
            raise ValueError(
                f"Unknown TTS provider '{pid}'. Supported: {list(self.PROVIDER_SPECS.keys())}"
            )

        self._load_providers()
        with self._lock:
            entry = dict(self._provider_configs.get(pid) or {})
            if api_key is not None and api_key.strip():
                entry["api_key"] = api_key.strip()
            if model_id is not None and model_id.strip():
                entry["model_id"] = model_id.strip()
            elif "model_id" not in entry:
                entry["model_id"] = str(self.PROVIDER_SPECS[pid]["default_model"])
            self._provider_configs[pid] = entry
        self._save_providers()

        status = next(p for p in self.list_providers() if p["provider_id"] == pid)
        status["status"] = "configured"
        return status

    def list_custom_profiles(self) -> List[Dict[str, Any]]:
        self._load_profiles()
        return [p.to_dict() for p in self._custom_profiles.values()]

    def list_voices(self) -> List[Dict[str, Any]]:
        self._load_profiles()
        voices = [dict(v) for v in self.CURATED_VOICES]
        for prof in self._custom_profiles.values():
            voices.append(
                {
                    "voice_id": prof.profile_id,
                    "name": f"{prof.name} [{prof.mode.upper()}]",
                    "locale": "custom",
                    "gender": prof.emotion_style,
                    "style": prof.prompt_description or f"Base: {prof.base_voice_id}",
                    "fallback_pitch_mult": 1.0 + (prof.pitch_hz / 100.0),
                    "mode": prof.mode,
                }
            )
        return voices

    # ==========================================================
    # VOICE DESIGN & REAL ACOUSTIC VOICE CLONING
    # ==========================================================

    def design_voice(
        self,
        name: str,
        prompt_description: str,
        seed: int = 42,
        language: str = "vi-VN",
    ) -> Dict[str, Any]:
        """Design a synthetic VoiceProfile from natural-language traits & seed (VoiceStudio pattern)."""
        prompt_lower = (prompt_description or "").lower()
        is_english = language.lower().startswith("en") or "english" in prompt_lower or "tiếng anh" in prompt_lower
        is_male = any(k in prompt_lower for k in ("nam", "male", "man", "baritone", "guy", "trầm nam"))

        if is_english:
            base_voice = "en-US-GuyNeural" if is_male else "en-US-AriaNeural"
        else:
            base_voice = "vi-VN-NamMinhNeural" if is_male else "vi-VN-HoaiMyNeural"

        pitch_hz = -6 if is_male else 4
        rate = 1.0
        warmth_eq = 0.0
        emotion = "warm"

        if any(k in prompt_lower for k in ("trầm", "ấm", "deep", "warm", "đêm khuya", "late night")):
            pitch_hz -= 5
            warmth_eq = 0.35
            emotion = "warm"
            rate = 0.94
        if any(k in prompt_lower for k in ("bí ẩn", "trinh thám", "mystery", "horror", "thriller")):
            pitch_hz -= 6
            rate = 0.90
            emotion = "mysterious"
        if any(k in prompt_lower for k in ("nhanh", "sôi nổi", "vui", "energetic", "excited", "upbeat")):
            pitch_hz += 5
            rate = 1.12
            emotion = "excited"
        if any(k in prompt_lower for k in ("thì thầm", "nhẹ nhàng", "whisper", "soft")):
            rate = 0.88
            emotion = "whisper"

        seed_offset = ((abs(int(seed)) % 7) - 3)
        pitch_hz = max(-25, min(25, pitch_hz + seed_offset))

        slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_") or uuid.uuid4().hex[:6]
        profile = VoiceProfile(
            profile_id=f"design_{slug}_{abs(int(seed)) % 1000}",
            name=name.strip(),
            mode="designed",
            base_voice_id=base_voice,
            prompt_description=prompt_description.strip(),
            seed=int(seed),
            pitch_hz=pitch_hz,
            rate=rate,
            warmth_eq=warmth_eq,
            emotion_style=emotion,
            consent_verified=True,
        )
        with self._lock:
            self._custom_profiles[profile.profile_id] = profile
        self._save_profiles()
        return profile.to_dict()

    @classmethod
    def _analyze_reference_acoustics(cls, ref_path: Path) -> Dict[str, float]:
        """Measure real speaker Fundamental Frequency F0 (Hz), spectral centroid warmth & RMS energy."""
        y: np.ndarray | None = None
        sr: int = cls.SAMPLE_RATE

        try:
            import soundfile as sf

            data, read_sr = sf.read(str(ref_path), dtype="float32", always_2d=True)
            y = data.mean(axis=1)
            sr = int(read_sr)
        except Exception:
            try:
                with wave.open(str(ref_path), "rb") as wf:
                    sr = wf.getframerate() or cls.SAMPLE_RATE
                    n_ch = max(1, wf.getnchannels())
                    raw_bytes = wf.readframes(min(wf.getnframes(), sr * 20))
                    if wf.getsampwidth() == 2 and raw_bytes:
                        arr = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                        y = arr.reshape(-1, n_ch).mean(axis=1)
            except Exception:
                y = None

        if y is None or y.size < 256:
            return {"f0_hz": 175.0, "centroid_hz": 1650.0, "rms_db": -20.0}

        # Cap analysis window to first 15s of active audio for deterministic low-latency measurement
        y = np.asarray(y[: sr * 15], dtype=np.float32)
        rms = float(np.sqrt(np.mean(np.square(y)) + 1e-12))
        rms_db = 20.0 * math.log10(max(rms, 1e-6))

        # Spectral centroid via real FFT magnitude spectrum
        win = y * np.hanning(len(y))
        mag = np.abs(np.fft.rfft(win))
        freqs = np.fft.rfftfreq(len(win), d=1.0 / float(sr))
        mag_sum = float(np.sum(mag))
        centroid_hz = float(np.sum(freqs * mag) / mag_sum) if mag_sum > 1e-9 else 1650.0

        # Estimate speaker F0 via librosa.yin on voiced frames (fallback to autocorrelation)
        f0_hz = 175.0
        try:
            import librosa

            f0_track = librosa.yin(y, fmin=65.0, fmax=380.0, sr=sr, frame_length=2048)
            valid_f0 = f0_track[np.isfinite(f0_track) & (f0_track >= 70.0) & (f0_track <= 360.0)]
            if valid_f0.size >= 3:
                f0_hz = float(np.median(valid_f0))
        except Exception:
            # Time-domain autocorrelation fallback over central voiced slice
            mid = y[len(y) // 4 : min(len(y), len(y) // 4 + sr)]
            if mid.size >= 512:
                mid = mid - float(np.mean(mid))
                corr = np.correlate(mid, mid, mode="full")[len(mid) - 1 :]
                min_lag = max(1, int(sr / 360.0))
                max_lag = min(len(corr) - 1, int(sr / 70.0))
                if max_lag > min_lag:
                    peak_lag = min_lag + int(np.argmax(corr[min_lag:max_lag]))
                    f0_hz = float(sr) / float(peak_lag)

        return {
            "f0_hz": round(f0_hz, 2),
            "centroid_hz": round(centroid_hz, 1),
            "rms_db": round(rms_db, 2),
        }

    def clone_voice(
        self,
        name: str,
        reference_audio_path: Path,
        consent_verified: bool = False,
        language: str = "vi-VN",
    ) -> Dict[str, Any]:
        """Consent-gated Acoustic & Zero-Shot Voice Cloning measuring real speaker F0, warmth & reference clip."""
        if not consent_verified:
            raise ValueError(
                "Voice cloning requires explicit speaker consent (consent_verified=True) per VoiceStudio policy."
            )
        ref = Path(reference_audio_path)
        if not ref.exists() or not ref.is_file():
            raise FileNotFoundError(f"Reference audio file not found: {ref}")

        acoustics = self._analyze_reference_acoustics(ref)
        f0_hz = acoustics["f0_hz"]
        centroid_hz = acoustics["centroid_hz"]
        rms_db = acoustics["rms_db"]

        is_english = language.lower().startswith("en")
        is_male = f0_hz < 168.0
        if is_english:
            base_voice = "en-US-GuyNeural" if is_male else "en-US-AriaNeural"
        else:
            base_voice = "vi-VN-NamMinhNeural" if is_male else "vi-VN-HoaiMyNeural"

        anchor_hz = 125.0 if is_male else 210.0
        pitch_hz = int(round(max(-20.0, min(20.0, (f0_hz - anchor_hz) * 0.25))))
        warmth_eq = round(max(0.05, min(0.65, (2500.0 - centroid_hz) / 3200.0)), 2)
        emotion = "late_night" if (is_male and centroid_hz < 1750.0) else "warm"
        file_seed = ref.stat().st_size % 997

        slug = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower()).strip("_") or uuid.uuid4().hex[:6]
        profile = VoiceProfile(
            profile_id=f"clone_{slug}_{file_seed}",
            name=name.strip(),
            mode="cloned",
            base_voice_id=base_voice,
            prompt_description=(
                f"Cloned acoustic profile from {ref.name} "
                f"(F0={f0_hz:.1f}Hz, centroid={centroid_hz:.0f}Hz, rms={rms_db:.1f}dB)"
            ),
            seed=file_seed,
            pitch_hz=pitch_hz,
            rate=0.96 if emotion == "late_night" else 1.0,
            warmth_eq=warmth_eq,
            emotion_style=emotion,
            reference_audio_path=str(ref.resolve()),
            consent_verified=True,
        )
        with self._lock:
            self._custom_profiles[profile.profile_id] = profile
        self._save_profiles()
        return profile.to_dict()

    # ==========================================================
    # TAG PARSING & SUBTLE ACOUSTIC BREATH / SILENCE SYNTHESIS
    # ==========================================================

    @staticmethod
    def parse_expressive_tags(raw_text: str) -> Tuple[str, str | None, float]:
        """Strip VoiceStudio tags ([pause 500ms], [emotion:excited], [laughter], [sigh], [breath]) and extract mood + tail pause."""
        pause_sec = 0.0
        emotion: str | None = None

        for m in re.finditer(r"\[pause(?:\s+(\d+(?:\.\d+)?)(ms|s))?\]", raw_text, flags=re.IGNORECASE):
            if m.group(1):
                val = float(m.group(1))
                pause_sec += val / 1000.0 if (m.group(2) or "").lower() == "ms" else val
            else:
                pause_sec += 0.5

        em_match = re.search(r"\[emotion:([a-zA-Z_]+)\]", raw_text, flags=re.IGNORECASE)
        if em_match:
            emotion = em_match.group(1).strip().lower()

        cleaned = re.sub(
            r"\[(pause[^\]]*|emotion:[^\]]*|laughter|sigh|breath)\]",
            " ",
            raw_text,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned, emotion, min(4.0, pause_sec)

    @classmethod
    def _parse_clauses_and_pauses(cls, raw_text: str) -> Tuple[str | None, float, List[Tuple[str, float]]]:
        """Extract [emotion:...] tag and split text along mid-sentence [pause ...] and [breath]/[sigh] cues."""
        emotion: str | None = None
        em_match = cls._EMOTION_TAG_RE.search(raw_text)
        if em_match:
            emotion = em_match.group(1).strip().lower()

        stripped = cls._SILENT_STRIP_TAG_RE.sub(" ", raw_text)
        leading_pause_sec = 0.0
        clauses: List[List[Any]] = []
        token_re = re.compile(
            r"\[(pause(?:\s+(\d+(?:\.\d+)?)(ms|s))?|breath|sigh)\]",
            flags=re.IGNORECASE,
        )
        last_idx = 0

        for m in token_re.finditer(stripped):
            chunk = re.sub(r"\s+", " ", stripped[last_idx : m.start()]).strip()
            tag_full = m.group(1).strip().lower()

            if tag_full in ("breath", "sigh"):
                if chunk:
                    clauses.append([chunk, 0.04])
                cue_token = "__SIGH__" if tag_full == "sigh" else "__BREATH__"
                clauses.append([cue_token, 0.05])
            else:
                if m.group(2):
                    val = float(m.group(2))
                    p_sec = val / 1000.0 if (m.group(3) or "").lower() == "ms" else val
                else:
                    p_sec = 0.5

                if chunk:
                    clauses.append([chunk, min(4.0, p_sec)])
                else:
                    if clauses:
                        clauses[-1][1] = min(4.0, float(clauses[-1][1]) + p_sec)
                    else:
                        leading_pause_sec = min(4.0, leading_pause_sec + p_sec)

            last_idx = m.end()

        tail_chunk = re.sub(r"\s+", " ", stripped[last_idx:]).strip()
        if tail_chunk:
            clauses.append([tail_chunk, 0.0])

        if not clauses:
            return emotion, 0.0, [("Kinetix Studio", min(4.0, leading_pause_sec))]

        return emotion, leading_pause_sec, [(str(c[0]), float(c[1])) for c in clauses]

    def _generate_breath_wav(self, output_path: Path, kind: str = "breath") -> Path:
        """Synthesize subtle acoustic inhale/sigh (0.28s bandpass 350Hz–1800Hz pink-noise envelope at -26dB)."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dur = 0.36 if kind == "sigh" else 0.28
        fade_out_st = max(0.08, dur - 0.15)
        res = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"anoisesrc=c=pink:r={self.SAMPLE_RATE}:a=0.050:d={dur:.3f}",
                "-af",
                f"highpass=f=350,lowpass=f=1800,afade=t=in:st=0:d=0.09,afade=t=out:st={fade_out_st:.3f}:d=0.15",
                "-ar",
                str(self.SAMPLE_RATE),
                "-ac",
                "1",
                "-acodec",
                "pcm_s16le",
                str(output_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if res.returncode != 0 or not output_path.exists():
            # Pure NumPy bandpass envelope fallback
            n = int(round(dur * self.SAMPLE_RATE))
            rng = np.random.default_rng(108)
            white = rng.standard_normal(n).astype(np.float32)
            spec = np.fft.rfft(white)
            freqs = np.fft.rfftfreq(n, d=1.0 / self.SAMPLE_RATE)
            mask = ((freqs >= 350.0) & (freqs <= 1800.0)).astype(np.float32) / np.sqrt(np.maximum(freqs, 50.0))
            band = np.fft.irfft(spec * mask, n=n)
            peak = float(np.max(np.abs(band)) + 1e-8)
            env = np.sin(np.linspace(0.0, math.pi, n, dtype=np.float32)) ** 1.3
            pcm = np.clip((band / peak) * 0.048 * env * 32767.0, -32767, 32767).astype(np.int16)
            with wave.open(str(output_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.SAMPLE_RATE)
                wf.writeframes(pcm.tobytes())
        return output_path

    # ==========================================================
    # PROVIDER BACKENDS: VIENEU ONNX, GEMINI TTS, ELEVENLABS, EDGE
    # ==========================================================

    @classmethod
    def _get_vieneu_engine(cls, mode: str = "v3nano") -> Any:
        target_mode = mode if mode in ("v3nano", "v3turbo") else "v3nano"
        with cls._vieneu_lock:
            if target_mode not in cls._vieneu_engines:
                from vieneu import Vieneu

                if target_mode == "v3nano":
                    cls._vieneu_engines[target_mode] = Vieneu(mode="v3nano", steps=12)
                else:
                    cls._vieneu_engines[target_mode] = Vieneu(mode="v3turbo")
            return cls._vieneu_engines[target_mode]

    @staticmethod
    def _is_vieneu_clone_cached() -> bool:
        """Check if VieNeu zero-shot reference encoder ONNX graphs are already cached locally."""
        hf_root = Path.home() / ".cache" / "huggingface" / "hub" / "models--pnnbao-ump--VieNeu-TTS-v3-Nano"
        if not hf_root.exists():
            return False
        needed = {"speaker_encoder.onnx", "codec_encoder.onnx", "reference_encoder.onnx"}
        found = {p.name for p in hf_root.rglob("*.onnx")}
        return needed.issubset(found)

    def _synthesize_via_vieneu(
        self,
        text: str,
        raw_wav: Path,
        voice_preset: str,
        eff_rate: float,
        ref_audio: str | None = None,
        uid: str = "vn",
    ) -> bool:
        """Synthesize natural Vietnamese speech on-device via VieNeu-TTS v3.8 ONNX."""
        if importlib.util.find_spec("vieneu") is None:
            return False
        _, model_mode = self._resolve_provider_secret("vieneu_local")
        tmp_vn = raw_wav.with_name(f".vieneu_{uid}.wav")
        try:
            tts = self._get_vieneu_engine(model_mode or "v3nano")
            speed = max(0.76, min(1.32, float(eff_rate)))
            kwargs: Dict[str, Any] = {"speed": speed, "apply_watermark": False}
            if ref_audio and Path(ref_audio).is_file():
                kwargs["ref_audio"] = str(ref_audio)
                kwargs["denoise"] = False
            else:
                kwargs["voice"] = voice_preset

            audio_np = tts.infer(text, **kwargs)
            if audio_np is None or getattr(audio_np, "size", 0) < 400:
                return False

            tts.save(audio_np, str(tmp_vn))
            if not tmp_vn.exists() or tmp_vn.stat().st_size < 600:
                return False

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(tmp_vn),
                    "-ar",
                    str(self.SAMPLE_RATE),
                    "-ac",
                    "1",
                    "-acodec",
                    "pcm_s16le",
                    str(raw_wav),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return raw_wav.exists() and raw_wav.stat().st_size > 600
        except Exception:
            return False
        finally:
            tmp_vn.unlink(missing_ok=True)

    def _synthesize_via_gemini(
        self,
        text: str,
        raw_wav: Path,
        gemini_voice: str = "Charon",
        emotion: str = "late_night",
        uid: str = "gem",
    ) -> bool:
        """Synthesize acting-directed speech via Gemini Native Audio TTS REST API."""
        api_key, model_id = self._resolve_provider_secret("gemini_tts")
        if not api_key:
            return False

        acting_cue = {
            "late_night": "Speak in a warm, intimate, late-night confessional podcast tone, calm and deeply reflective:",
            "dramatic": "Speak with grounded, serious emotional weight and clear dramatic pacing:",
            "warm": "Speak with gentle warmth, sincerity, and quiet encouragement:",
        }.get(emotion, "Speak naturally and expressively:")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": f"{acting_cue}\n{text}"}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": gemini_voice or "Charon"}
                    }
                },
            },
        }
        tmp_gem = raw_wav.with_name(f".gemini_{uid}.pcm")
        try:
            import httpx

            resp = httpx.post(url, params={"key": api_key}, json=payload, timeout=60.0)
            if resp.status_code != 200:
                return False
            data = resp.json()
            inline = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("inlineData", {})
            )
            b64_audio = inline.get("data")
            mime = str(inline.get("mimeType") or "audio/L16;rate=24000")
            if not b64_audio:
                return False

            raw_bytes = base64.b64decode(b64_audio)
            if "wav" in mime.lower():
                tmp_wav = raw_wav.with_name(f".gemini_{uid}.wav")
                tmp_wav.write_bytes(raw_bytes)
                try:
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-i",
                            str(tmp_wav),
                            "-ar",
                            str(self.SAMPLE_RATE),
                            "-ac",
                            "1",
                            "-acodec",
                            "pcm_s16le",
                            str(raw_wav),
                        ],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                finally:
                    tmp_wav.unlink(missing_ok=True)
            else:
                m_rate = re.search(r"rate=(\d+)", mime)
                in_rate = int(m_rate.group(1)) if m_rate else 24000
                tmp_gem.write_bytes(raw_bytes)
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "s16le",
                        "-ar",
                        str(in_rate),
                        "-ac",
                        "1",
                        "-i",
                        str(tmp_gem),
                        "-ar",
                        str(self.SAMPLE_RATE),
                        "-ac",
                        "1",
                        "-acodec",
                        "pcm_s16le",
                        str(raw_wav),
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            return raw_wav.exists() and raw_wav.stat().st_size > 600
        except Exception:
            return False
        finally:
            tmp_gem.unlink(missing_ok=True)

    def _synthesize_via_elevenlabs(
        self,
        text: str,
        raw_wav: Path,
        el_voice_id: str = "pNInz6obpgDQGcFmaJgB",
        uid: str = "el",
    ) -> bool:
        """Synthesize expressive storytelling speech via ElevenLabs Multilingual v2 API."""
        api_key, model_id = self._resolve_provider_secret("elevenlabs_tts")
        if not api_key:
            return False

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{el_voice_id}"
        headers = {"xi-api-key": api_key, "Accept": "audio/mpeg", "Content-Type": "application/json"}
        payload = {
            "text": text,
            "model_id": model_id or "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.48,
                "similarity_boost": 0.80,
                "style": 0.36,
                "use_speaker_boost": True,
            },
        }
        tmp_mp3 = raw_wav.with_name(f".el_{uid}.mp3")
        try:
            import httpx

            resp = httpx.post(url, headers=headers, json=payload, timeout=60.0)
            if resp.status_code != 200 or len(resp.content) < 400:
                return False
            tmp_mp3.write_bytes(resp.content)
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(tmp_mp3),
                    "-ar",
                    str(self.SAMPLE_RATE),
                    "-ac",
                    "1",
                    "-acodec",
                    "pcm_s16le",
                    str(raw_wav),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            return raw_wav.exists() and raw_wav.stat().st_size > 600
        except Exception:
            return False
        finally:
            tmp_mp3.unlink(missing_ok=True)

    def _stream_edge_with_boundaries(
        self,
        utterance_text: str,
        raw_wav: Path,
        edge_voice: str,
        eff_rate: float,
        eff_pitch: int,
        uid: str,
    ) -> Tuple[bool, List[Dict[str, Any]]]:
        """Stream continuous speech from edge-tts while capturing exact SentenceBoundary offsets & durations."""
        mp3_tmp = raw_wav.with_name(f".edge_{uid}.mp3")
        boundaries: List[Dict[str, Any]] = []
        rate_pct = int(round((eff_rate - 1.0) * 100))
        rate_str = f"{rate_pct:+d}%"
        pitch_str = f"{eff_pitch:+d}Hz"

        async def _run_edge_stream() -> List[Dict[str, Any]]:
            import edge_tts

            last_err: Exception | None = None
            for attempt in range(3):
                captured: List[Dict[str, Any]] = []
                try:
                    mp3_tmp.unlink(missing_ok=True)
                    comm = edge_tts.Communicate(
                        utterance_text,
                        voice=edge_voice,
                        rate=rate_str,
                        pitch=pitch_str,
                        boundary="SentenceBoundary",
                    )
                    with open(mp3_tmp, "wb") as audio_fp:
                        async for chunk in comm.stream():
                            ctype = chunk.get("type")
                            if ctype == "audio":
                                data = chunk.get("data")
                                if data:
                                    audio_fp.write(data)
                            elif ctype in ("SentenceBoundary", "WordBoundary"):
                                captured.append(
                                    {
                                        "type": ctype,
                                        "offset_sec": float(chunk.get("offset", 0)) / self._TICKS_PER_SEC,
                                        "duration_sec": float(chunk.get("duration", 0)) / self._TICKS_PER_SEC,
                                        "text": str(chunk.get("text") or "").strip(),
                                    }
                                )
                    if mp3_tmp.exists() and mp3_tmp.stat().st_size > 300:
                        return captured
                    raise RuntimeError("edge-tts stream produced empty MP3.")
                except Exception as exc:
                    last_err = exc
                    if attempt < 2:
                        await asyncio.sleep(0.65 * (attempt + 1))
            if last_err is not None:
                raise last_err
            return []

        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop is not None:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    boundaries = pool.submit(lambda: asyncio.run(_run_edge_stream())).result(timeout=160.0)
            else:
                boundaries = asyncio.run(_run_edge_stream())

            if mp3_tmp.exists() and mp3_tmp.stat().st_size > 300:
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        str(mp3_tmp),
                        "-ar",
                        str(self.SAMPLE_RATE),
                        "-ac",
                        "1",
                        "-acodec",
                        "pcm_s16le",
                        str(raw_wav),
                    ],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                if raw_wav.exists() and raw_wav.stat().st_size > 600:
                    return True, boundaries
        except Exception:
            pass
        finally:
            mp3_tmp.unlink(missing_ok=True)

        return False, []

    def _synthesize_utterance_raw(
        self,
        utterance_text: str,
        raw_wav: Path,
        resolved_voice: str,
        eff_rate: float,
        eff_pitch: int,
        uid: str,
        emotion: str = "warm",
        ref_audio: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Synthesize a clean spoken utterance/paragraph via the selected provider with resilient fallback chain."""
        if utterance_text in ("__BREATH__", "__SIGH__"):
            self._generate_breath_wav(raw_wav, kind="sigh" if utterance_text == "__SIGH__" else "breath")
            return []

        synthesized_ok = False
        boundaries: List[Dict[str, Any]] = []
        sr_str = str(self.SAMPLE_RATE)
        voice_meta = next((v for v in self.CURATED_VOICES if v["voice_id"] == resolved_voice), None)
        provider = str(voice_meta.get("provider") if voice_meta else "edge_prosody_v6")

        # 1A. Specialist Provider: VieNeu Local Neural ONNX (or cloned Vietnamese voice when encoder cached)
        if provider == "vieneu_local":
            vn_preset = str(voice_meta.get("vieneu_voice") or "Anh Khôi") if voice_meta else "Anh Khôi"
            synthesized_ok = self._synthesize_via_vieneu(
                text=utterance_text,
                raw_wav=raw_wav,
                voice_preset=vn_preset,
                eff_rate=eff_rate,
                ref_audio=ref_audio if (ref_audio and self._is_vieneu_clone_cached()) else None,
                uid=uid,
            )
            if not synthesized_ok:
                resolved_voice = "vi-VN-NamMinhNeural" if "nam" in resolved_voice else "vi-VN-HoaiMyNeural"
        elif ref_audio and resolved_voice.startswith("vi-VN") and self._is_vieneu_clone_cached():
            synthesized_ok = self._synthesize_via_vieneu(
                text=utterance_text,
                raw_wav=raw_wav,
                voice_preset="Anh Khôi",
                eff_rate=eff_rate,
                ref_audio=ref_audio,
                uid=uid,
            )

        # 1B. Specialist Provider: Gemini Native Audio Acting TTS
        if not synthesized_ok and provider == "gemini_tts":
            gem_voice = str(voice_meta.get("gemini_voice") or "Charon") if voice_meta else "Charon"
            synthesized_ok = self._synthesize_via_gemini(
                text=utterance_text,
                raw_wav=raw_wav,
                gemini_voice=gem_voice,
                emotion=emotion,
                uid=uid,
            )
            if not synthesized_ok:
                resolved_voice = "vi-VN-NamMinhNeural"

        # 1C. Specialist Provider: ElevenLabs Multilingual v2
        if not synthesized_ok and provider == "elevenlabs_tts":
            el_id = str(voice_meta.get("elevenlabs_voice_id") or "pNInz6obpgDQGcFmaJgB") if voice_meta else "pNInz6obpgDQGcFmaJgB"
            synthesized_ok = self._synthesize_via_elevenlabs(
                text=utterance_text,
                raw_wav=raw_wav,
                el_voice_id=el_id,
                uid=uid,
            )
            if not synthesized_ok:
                resolved_voice = "vi-VN-NamMinhNeural"

        # 2. Microsoft Neural Edge Stream (with SentenceBoundary capture & retries)
        if not synthesized_ok and resolved_voice != "win-sapi-studio":
            synthesized_ok, boundaries = self._stream_edge_with_boundaries(
                utterance_text=utterance_text,
                raw_wav=raw_wav,
                edge_voice=resolved_voice,
                eff_rate=eff_rate,
                eff_pitch=eff_pitch,
                uid=uid,
            )

        # 3. Offline Fallback: Windows System.Speech.Synthesis + FFmpeg formant pitch/rate shaping
        if not synthesized_ok:
            sapi_tmp = raw_wav.with_name(f".sapi_{uid}.wav")
            escaped = utterance_text.replace("'", "''").replace("\n", " ").replace("|", ", ")
            sapi_rate = max(-5, min(5, int(round((eff_rate - 1.0) * 8))))
            ps_script = (
                "Add-Type -AssemblyName System.Speech; "
                "$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$synth.Rate = {sapi_rate}; "
                f"$synth.SetOutputToWaveFile('{str(sapi_tmp)}'); "
                f"$synth.Speak('{escaped}'); "
                "$synth.Dispose();"
            )
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=18,
                )
                if sapi_tmp.exists() and sapi_tmp.stat().st_size > 1000:
                    meta = next((v for v in self.CURATED_VOICES if v["voice_id"] == resolved_voice), None)
                    pitch_mult = float(meta["fallback_pitch_mult"]) if meta else 1.0
                    pitch_mult *= 1.0 + (eff_pitch / 120.0)
                    pitch_mult = max(0.75, min(1.35, pitch_mult))
                    if abs(pitch_mult - 1.0) > 0.01:
                        af = f"asetrate=22050*{pitch_mult:.2f},atempo={1.0/pitch_mult:.2f},aresample={sr_str}"
                    else:
                        af = f"aresample={sr_str}"
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-i",
                            str(sapi_tmp),
                            "-af",
                            af,
                            "-ar",
                            sr_str,
                            "-ac",
                            "1",
                            "-acodec",
                            "pcm_s16le",
                            str(raw_wav),
                        ],
                        check=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    if raw_wav.exists() and raw_wav.stat().st_size > 600:
                        synthesized_ok = True
            except Exception:
                pass
            finally:
                sapi_tmp.unlink(missing_ok=True)

        # 4. Deterministic audio fallback if host has no speech engine
        if not synthesized_ok:
            dur = max(1.2, min(10.0, len(utterance_text.split()) * 0.35))
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    f"aevalsrc=0.14*sin(2*PI*330*t)*(0.5+0.5*sin(2*PI*3*t)):s={sr_str}:d={dur:.2f}",
                    "-ac",
                    "1",
                    "-acodec",
                    "pcm_s16le",
                    str(raw_wav),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        return boundaries

    def _finalize_utterance_wav(
        self,
        raw_wav: Path,
        target_wav: Path,
        eq_filter: str,
        lead_pause_sec: float = 0.0,
        tail_pause_sec: float = 0.0,
    ) -> Path:
        """Apply emotion EQ, optional leading delay, and trailing pause padding onto raw_wav."""
        post_filters: List[str] = []
        if lead_pause_sec > 0.03:
            delay_ms = int(round(lead_pause_sec * 1000))
            post_filters.append(f"adelay={delay_ms}|{delay_ms}")
        if eq_filter:
            post_filters.append(eq_filter)
        if tail_pause_sec > 0.03:
            post_filters.append(f"apad=pad_dur={tail_pause_sec:.3f}")

        if post_filters:
            res = subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(raw_wav),
                    "-af",
                    ",".join(post_filters),
                    "-ar",
                    str(self.SAMPLE_RATE),
                    "-ac",
                    "1",
                    "-acodec",
                    "pcm_s16le",
                    str(target_wav),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if res.returncode == 0 and target_wav.exists():
                raw_wav.unlink(missing_ok=True)
                return target_wav

        if raw_wav.exists():
            if target_wav.exists():
                target_wav.unlink(missing_ok=True)
            raw_wav.replace(target_wav)
        return target_wav

    def _generate_silence_wav(self, output_path: Path, duration_sec: float) -> Path:
        """Generate a clean mono PCM silent WAV of duration_sec for atmospheric SFX lead-ins."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        dur = max(0.05, float(duration_sec))
        res = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"anullsrc=r={self.SAMPLE_RATE}:cl=mono",
                "-t",
                f"{dur:.3f}",
                "-ar",
                str(self.SAMPLE_RATE),
                "-ac",
                "1",
                "-acodec",
                "pcm_s16le",
                str(output_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if res.returncode != 0 or not output_path.exists():
            n_frames = max(1, int(round(dur * self.SAMPLE_RATE)))
            with wave.open(str(output_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(self.SAMPLE_RATE)
                wf.writeframes(b"\x00\x00" * n_frames)
        return output_path

    def _resolve_voice_and_prosody(
        self,
        voice_id: str,
        rate: float,
        pitch_hz: int,
        tag_emotion: str | None,
    ) -> Tuple[str, float, int, str, str, str | None]:
        """Resolve custom VoiceProfile + emotion EQ -> (resolved_voice, eff_rate, eff_pitch, eq_filter, emotion, ref_audio)."""
        resolved_voice = (voice_id or "vi-VN-HoaiMyNeural").strip()
        eff_rate = float(rate)
        eff_pitch = int(pitch_hz)
        eq_filter = ""
        ref_audio: str | None = None
        eff_emotion = tag_emotion or "warm"

        self._load_profiles()
        with self._lock:
            custom = self._custom_profiles.get(resolved_voice)
        if custom is not None:
            resolved_voice = custom.base_voice_id
            eff_rate *= custom.rate
            eff_pitch += custom.pitch_hz
            ref_audio = custom.reference_audio_path
            if not tag_emotion:
                eff_emotion = custom.emotion_style
            if custom.warmth_eq > 0.05:
                gain = round(min(5.0, custom.warmth_eq * 6.5), 1)
                eq_filter = f"equalizer=f=195:t=q:w=1.1:g={gain}"

        if eff_emotion in self.EMOTION_PRESETS:
            preset = self.EMOTION_PRESETS[eff_emotion]
            eff_rate *= float(preset["rate_mult"])
            eff_pitch += int(preset["pitch_offset"])
            preset_eq = str(preset["eq"])
            eq_filter = f"{eq_filter},{preset_eq}" if eq_filter else preset_eq

        eff_rate = max(0.6, min(1.8, eff_rate))
        eff_pitch = max(-35, min(35, eff_pitch))
        return resolved_voice, eff_rate, eff_pitch, eq_filter, eff_emotion, ref_audio

    def synthesize(
        self,
        text: str,
        output_path: Path,
        voice_id: str = "vi-VN-HoaiMyNeural",
        rate: float = 1.0,
        pitch_hz: int = 0,
    ) -> Path:
        raw_clean = text.strip()
        if not raw_clean:
            raise ValueError("Voiceover text must not be empty.")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        tag_emotion, leading_pause_sec, clauses = self._parse_clauses_and_pauses(raw_clean)
        resolved_voice, eff_rate, eff_pitch, eq_filter, eff_emotion, ref_audio = self._resolve_voice_and_prosody(
            voice_id=voice_id,
            rate=rate,
            pitch_hz=pitch_hz,
            tag_emotion=tag_emotion,
        )

        uid = uuid.uuid4().hex[:8]

        if len(clauses) == 1:
            clause_text, tail_pause_sec = clauses[0]
            raw_wav = output_path.with_name(f".raw_{output_path.stem}_{uid}.wav")
            try:
                self._synthesize_utterance_raw(
                    utterance_text=clause_text,
                    raw_wav=raw_wav,
                    resolved_voice=resolved_voice,
                    eff_rate=eff_rate,
                    eff_pitch=eff_pitch,
                    uid=uid,
                    emotion=eff_emotion,
                    ref_audio=ref_audio,
                )
                return self._finalize_utterance_wav(
                    raw_wav=raw_wav,
                    target_wav=output_path,
                    eq_filter="" if clause_text in ("__BREATH__", "__SIGH__") else eq_filter,
                    lead_pause_sec=leading_pause_sec,
                    tail_pause_sec=tail_pause_sec,
                )
            finally:
                raw_wav.unlink(missing_ok=True)

        # Multi-clause splicing for mid-sentence [pause 600ms] & [breath]/[sigh] dramatic beats
        sub_wavs: List[Path] = []
        concat_file = output_path.with_name(f".concat_{output_path.stem}_{uid}.txt")
        try:
            for part_idx, (clause_text, sub_pause_sec) in enumerate(clauses):
                part_uid = f"{uid}_p{part_idx}"
                part_raw = output_path.with_name(f".raw_{output_path.stem}_{part_uid}.wav")
                part_final = output_path.with_name(f".sub_{output_path.stem}_{part_uid}.wav")
                is_breath_cue = clause_text in ("__BREATH__", "__SIGH__")
                try:
                    self._synthesize_utterance_raw(
                        utterance_text=clause_text,
                        raw_wav=part_raw,
                        resolved_voice=resolved_voice,
                        eff_rate=eff_rate,
                        eff_pitch=eff_pitch,
                        uid=part_uid,
                        emotion=eff_emotion,
                        ref_audio=ref_audio,
                    )
                    self._finalize_utterance_wav(
                        raw_wav=part_raw,
                        target_wav=part_final,
                        eq_filter="" if is_breath_cue else eq_filter,
                        lead_pause_sec=leading_pause_sec if part_idx == 0 else 0.0,
                        tail_pause_sec=sub_pause_sec,
                    )
                finally:
                    part_raw.unlink(missing_ok=True)
                sub_wavs.append(part_final)

            lines = [f"file '{p.resolve().as_posix()}'" for p in sub_wavs]
            concat_file.write_text("\n".join(lines), encoding="utf-8")
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_file),
                    "-ar",
                    str(self.SAMPLE_RATE),
                    "-ac",
                    "1",
                    "-acodec",
                    "pcm_s16le",
                    str(output_path),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        finally:
            concat_file.unlink(missing_ok=True)
            for sw in sub_wavs:
                sw.unlink(missing_ok=True)

        return output_path

    # ==========================================================
    # CONTINUOUS PARAGRAPH STREAMING PODCAST ENGINE
    # ==========================================================

    @staticmethod
    def _wav_duration(wav_path: Path) -> float:
        try:
            with wave.open(str(wav_path), "rb") as wf:
                rate = wf.getframerate()
                frames = wf.getnframes()
                if rate > 0:
                    return max(0.15, float(frames) / float(rate))
        except Exception:
            pass
        return 2.0

    @staticmethod
    def _split_long_boundary_cue(text: str, max_words: int = 22) -> List[str]:
        """Split any SentenceBoundary cue exceeding max_words into clean clause-aligned subtitle cues."""
        words = text.split()
        if len(words) <= max_words:
            return [text.strip()] if text.strip() else []

        clauses = [c.strip() for c in re.split(r"(?<=[,;:–—])\s+", text.strip()) if c.strip()]
        if len(clauses) >= 2:
            out: List[str] = []
            buf = ""
            for cl in clauses:
                cand = f"{buf} {cl}".strip() if buf else cl
                if len(cand.split()) <= max_words:
                    buf = cand
                else:
                    if buf:
                        out.append(buf)
                    if len(cl.split()) > max_words:
                        cw = cl.split()
                        mid = max(1, len(cw) // 2)
                        out.append(" ".join(cw[:mid]))
                        buf = " ".join(cw[mid:])
                    else:
                        buf = cl
            if buf:
                out.append(buf)
            return out

        mid = max(1, len(words) // 2)
        return [" ".join(words[:mid]), " ".join(words[mid:])]

    def _synthesize_paragraph_beat(
        self,
        group_specs: List[Dict[str, Any]],
        para_wav: Path,
        genre: str,
    ) -> Tuple[float, List[Dict[str, Any]]]:
        """Synthesize an entire multi-sentence paragraph in ONE continuous neural stream and map exact subtitle cues."""
        first = group_specs[0]
        last = group_specs[-1]
        tail_pause_sec = max(0.25, float(last["pause_ms"]) / 1000.0)

        clean_parts: List[str] = []
        for sp in group_specs:
            cleaned, _, _ = self.parse_expressive_tags(sp["raw_text"])
            if cleaned:
                clean_parts.append(cleaned)
        full_para_text = re.sub(r"\s+", " ", " ".join(clean_parts)).strip()

        resolved_voice, eff_rate, eff_pitch, eq_filter, eff_emotion, ref_audio = self._resolve_voice_and_prosody(
            voice_id=first["voice_id"],
            rate=first["rate"],
            pitch_hz=first["pitch_hz"],
            tag_emotion=first["emotion"],
        )

        uid = uuid.uuid4().hex[:8]
        raw_wav = para_wav.with_name(f".raw_para_{para_wav.stem}_{uid}.wav")
        try:
            boundaries = self._synthesize_utterance_raw(
                utterance_text=full_para_text,
                raw_wav=raw_wav,
                resolved_voice=resolved_voice,
                eff_rate=eff_rate,
                eff_pitch=eff_pitch,
                uid=uid,
                emotion=eff_emotion,
                ref_audio=ref_audio,
            )
            self._finalize_utterance_wav(
                raw_wav=raw_wav,
                target_wav=para_wav,
                eq_filter=eq_filter,
                lead_pause_sec=0.0,
                tail_pause_sec=tail_pause_sec,
            )
        finally:
            raw_wav.unlink(missing_ok=True)

        total_dur = self._wav_duration(para_wav)
        spoken_dur = max(0.25, total_dur - tail_pause_sec)
        rel_segments: List[Dict[str, Any]] = []

        # Path A: Hardware-accurate SentenceBoundary events from Edge Neural Stream
        sent_bounds = [b for b in boundaries if b.get("type") == "SentenceBoundary" and b.get("text")]
        if sent_bounds:
            raw_cues: List[Tuple[float, float, str]] = []
            for b in sent_bounds:
                b_st = max(0.0, float(b["offset_sec"]))
                b_en = max(b_st + 0.18, b_st + float(b["duration_sec"]))
                sub_texts = self._split_long_boundary_cue(str(b["text"]), max_words=22)
                if len(sub_texts) == 1:
                    raw_cues.append((b_st, b_en, sub_texts[0]))
                else:
                    total_w = max(1, sum(len(st.split()) for st in sub_texts))
                    cur_t = b_st
                    span_t = b_en - b_st
                    for s_i, st_txt in enumerate(sub_texts):
                        frac = len(st_txt.split()) / float(total_w)
                        nxt_t = b_en if s_i == len(sub_texts) - 1 else (cur_t + span_t * frac)
                        raw_cues.append((cur_t, max(cur_t + 0.15, nxt_t), st_txt))
                        cur_t = nxt_t

            # Enforce strictly monotonic, non-overlapping cue boundaries clamped within total_dur
            prev_end = 0.0
            for c_idx, (c_st, c_en, c_txt) in enumerate(raw_cues):
                st_clamped = min(max(prev_end, c_st), max(0.0, total_dur - 0.18))
                if c_idx + 1 < len(raw_cues):
                    next_st = raw_cues[c_idx + 1][0]
                    en_clamped = min(c_en, max(st_clamped + 0.16, next_st))
                else:
                    en_clamped = min(total_dur, max(c_en, spoken_dur))
                en_clamped = min(total_dur, max(st_clamped + 0.15, en_clamped))
                prev_end = en_clamped

                speaker = first["speaker"]
                seg_text = f"{speaker}: {c_txt}" if genre == "podcast_dialogue" else c_txt
                rel_segments.append(
                    {
                        "turn_id": f"{first['turn_id']}_s{c_idx + 1}" if len(raw_cues) > len(group_specs) else group_specs[min(c_idx, len(group_specs) - 1)]["turn_id"],
                        "speaker_name": speaker,
                        "voice_id": first["voice_id"],
                        "emotion": first["emotion"],
                        "chapter_index": first["chapter_index"],
                        "chapter_title": first["chapter_title"],
                        "rel_start": st_clamped,
                        "rel_end": en_clamped,
                        "text": seg_text,
                    }
                )
            if rel_segments:
                rel_segments[-1]["rel_end"] = total_dur
            return total_dur, rel_segments

        # Path B: Proportional word-weighted alignment across group_specs (VieNeu / Gemini / ElevenLabs / SAPI)
        weights = [
            max(1, len((sp["explicit_caption"] or sp["raw_text"]).split()))
            for sp in group_specs
        ]
        w_sum = float(sum(weights))
        rel_cur = 0.0
        for s_idx, (sp, w) in enumerate(zip(group_specs, weights)):
            span = spoken_dur * (float(w) / w_sum)
            rel_end = total_dur if s_idx == len(group_specs) - 1 else min(spoken_dur, rel_cur + span)
            if sp["explicit_caption"]:
                seg_text = sp["explicit_caption"]
            else:
                clean_cap, _, _ = self.parse_expressive_tags(sp["raw_text"])
                seg_text = f"{sp['speaker']}: {clean_cap}" if genre == "podcast_dialogue" else clean_cap

            rel_segments.append(
                {
                    "turn_id": sp["turn_id"],
                    "speaker_name": sp["speaker"],
                    "voice_id": sp["voice_id"],
                    "emotion": sp["emotion"],
                    "chapter_index": sp["chapter_index"],
                    "chapter_title": sp["chapter_title"],
                    "rel_start": rel_cur,
                    "rel_end": max(rel_cur + 0.15, rel_end),
                    "text": seg_text,
                }
            )
            rel_cur = max(rel_cur + 0.15, rel_end)

        return total_dur, rel_segments

    def synthesize_podcast_script(
        self,
        turns: List[Dict[str, Any]],
        output_path: Path,
        genre: str = "podcast_dialogue",
    ) -> Tuple[Path, List[Dict[str, Any]]]:
        """Synthesize continuous Paragraph Beats (or individual dialogue turns), stitch pauses/lead-ins, and return (wav_path, timed_segments)."""
        if not turns:
            raise ValueError("Podcast turns must not be empty.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        turns_dir = output_path.parent / "podcast_turns"
        turns_dir.mkdir(parents=True, exist_ok=True)

        prepared_specs: List[Dict[str, Any]] = []
        for idx, turn in enumerate(turns, start=1):
            raw_text = str(turn.get("text") or turn.get("spoken_text") or "").strip()
            if not raw_text:
                continue
            speaker = str(turn.get("speaker_name") or "Host")
            voice_id = str(turn.get("voice_id") or "vi-VN-HoaiMyNeural")
            emotion = str(turn.get("emotion") or "warm").strip().lower()
            turn_rate = float(turn.get("rate") if turn.get("rate") is not None else 1.0)
            turn_pitch = int(turn.get("pitch_hz") if turn.get("pitch_hz") is not None else 0)
            pause_ms = max(120, int(turn.get("pause_after_ms") if turn.get("pause_after_ms") is not None else 350))
            chapter_index = int(turn.get("chapter_index") if turn.get("chapter_index") is not None else 0)
            chapter_title = str(turn.get("chapter_title") or "")
            lead_in_sec = max(0.0, float(turn.get("lead_in_sec") if turn.get("lead_in_sec") is not None else 0.0))
            turn_id = str(turn.get("turn_id") or f"turn_{idx:02d}")
            explicit_caption = str(turn.get("caption_text") or "").strip()
            para_group_id = str(turn.get("paragraph_group_id") or "").strip()

            has_emotion_tag = bool(self._EMOTION_TAG_RE.search(raw_text))
            has_trailing_pause = bool(re.search(r"\[pause[^\]]*\]\s*$", raw_text, flags=re.IGNORECASE))
            prefix = "" if has_emotion_tag else f"[emotion:{emotion}] "
            suffix = "" if has_trailing_pause else f" [pause {pause_ms}ms]"
            tagged_text = f"{prefix}{raw_text}{suffix}".strip()

            prepared_specs.append(
                {
                    "idx": idx,
                    "turn_id": turn_id,
                    "speaker": speaker,
                    "voice_id": voice_id,
                    "emotion": emotion,
                    "rate": turn_rate,
                    "pitch_hz": turn_pitch,
                    "pause_ms": pause_ms,
                    "chapter_index": chapter_index,
                    "chapter_title": chapter_title,
                    "lead_in_sec": lead_in_sec,
                    "raw_text": raw_text,
                    "explicit_caption": explicit_caption,
                    "tagged_text": tagged_text,
                    "paragraph_group_id": para_group_id,
                    "has_inline_pause": bool(self._PAUSE_TAG_RE.search(raw_text)),
                }
            )

        if not prepared_specs:
            raise ValueError("No valid spoken turns produced for podcast.")

        # Group consecutive turns sharing paragraph_group_id + voice_id (without mid-paragraph explicit [pause] or lead-in)
        units: List[Dict[str, Any]] = []
        current_group: List[Dict[str, Any]] = []

        def _flush_group() -> None:
            if not current_group:
                return
            u_idx = len(units) + 1
            first_sp = current_group[0]
            lead_wav = (turns_dir / f"lead_in_{u_idx:03d}.wav") if first_sp["lead_in_sec"] > 0.05 else None
            unit_wav = turns_dir / f"unit_{u_idx:03d}.wav"
            units.append(
                {
                    "unit_idx": u_idx,
                    "is_paragraph": len(current_group) > 1 and bool(first_sp["paragraph_group_id"]),
                    "specs": list(current_group),
                    "lead_in_sec": first_sp["lead_in_sec"],
                    "lead_wav": lead_wav,
                    "unit_wav": unit_wav,
                }
            )
            current_group.clear()

        for sp in prepared_specs:
            if not current_group:
                current_group.append(sp)
                if sp["has_inline_pause"] or not sp["paragraph_group_id"]:
                    _flush_group()
                continue

            prev = current_group[-1]
            can_merge = (
                bool(sp["paragraph_group_id"])
                and sp["paragraph_group_id"] == prev["paragraph_group_id"]
                and sp["voice_id"] == prev["voice_id"]
                and sp["lead_in_sec"] <= 0.05
                and not sp["has_inline_pause"]
            )
            if can_merge:
                current_group.append(sp)
            else:
                _flush_group()
                current_group.append(sp)
                if sp["has_inline_pause"] or not sp["paragraph_group_id"]:
                    _flush_group()

        _flush_group()

        def _synth_unit(unit: Dict[str, Any]) -> Tuple[float, List[Dict[str, Any]]]:
            if unit["lead_wav"] is not None:
                self._generate_silence_wav(unit["lead_wav"], unit["lead_in_sec"])

            if unit["is_paragraph"]:
                return self._synthesize_paragraph_beat(unit["specs"], unit["unit_wav"], genre=genre)

            sp = unit["specs"][0]
            self.synthesize(
                text=sp["tagged_text"],
                output_path=unit["unit_wav"],
                voice_id=sp["voice_id"],
                rate=sp["rate"],
                pitch_hz=sp["pitch_hz"],
            )
            dur = self._wav_duration(unit["unit_wav"])
            if sp["explicit_caption"]:
                seg_text = sp["explicit_caption"]
            else:
                clean_cap, _, _ = self.parse_expressive_tags(sp["raw_text"])
                seg_text = f"{sp['speaker']}: {clean_cap}" if genre == "podcast_dialogue" else clean_cap

            return dur, [
                {
                    "turn_id": sp["turn_id"],
                    "speaker_name": sp["speaker"],
                    "voice_id": sp["voice_id"],
                    "emotion": sp["emotion"],
                    "chapter_index": sp["chapter_index"],
                    "chapter_title": sp["chapter_title"],
                    "rel_start": 0.0,
                    "rel_end": dur,
                    "text": seg_text,
                }
            ]

        # VieNeu ONNX is CPU-threaded internally; cap worker concurrency to 1 when using local ONNX
        uses_local_onnx = any(
            str(u["specs"][0]["voice_id"]).startswith("vieneu-") for u in units
        )
        max_workers = 1 if uses_local_onnx else min(4, len(units))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_synth_unit, u) for u in units]
            unit_results = [fut.result() for fut in futures]

        wav_files: List[Path] = []
        timed_segments: List[Dict[str, Any]] = []
        cursor = 0.0

        for unit, (u_dur, rel_segs) in zip(units, unit_results):
            if unit["lead_in_sec"] > 0.05 and unit["lead_wav"] is not None:
                wav_files.append(unit["lead_wav"])
                cursor += unit["lead_in_sec"]

            for rs in rel_segs:
                timed_segments.append(
                    {
                        "turn_id": rs["turn_id"],
                        "speaker_name": rs["speaker_name"],
                        "voice_id": rs["voice_id"],
                        "emotion": rs["emotion"],
                        "chapter_index": rs["chapter_index"],
                        "chapter_title": rs["chapter_title"],
                        "start_time": round(cursor + float(rs["rel_start"]), 3),
                        "end_time": round(cursor + float(rs["rel_end"]), 3),
                        "text": rs["text"],
                    }
                )
            cursor += u_dur
            wav_files.append(unit["unit_wav"])

        if len(wav_files) == 1:
            shutil.copy2(wav_files[0], output_path)
            return output_path, timed_segments

        concat_list = turns_dir / "concat_turns.txt"
        lines = [f"file '{p.resolve().as_posix()}'" for p in wav_files]
        concat_list.write_text("\n".join(lines), encoding="utf-8")
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_list),
                    "-ar",
                    str(self.SAMPLE_RATE),
                    "-ac",
                    "1",
                    "-acodec",
                    "pcm_s16le",
                    str(output_path),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        finally:
            if concat_list.exists():
                concat_list.unlink()

        return output_path, timed_segments
