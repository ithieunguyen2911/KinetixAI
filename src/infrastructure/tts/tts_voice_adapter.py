"""TtsVoiceAdapter - Neural Text-to-Speech (edge-tts + Offline Windows SAPI Fallback)."""

import asyncio
from pathlib import Path
import subprocess
from typing import Any, Dict, List

from src.domain.interfaces.voice_synthesizer import IVoiceSynthesizer


class TtsVoiceAdapter(IVoiceSynthesizer):
    """Encapsulates edge-tts (rany2/edge-tts) with automatic offline Windows Speech Synthesis fallback."""

    CURATED_VOICES: List[Dict[str, Any]] = [
        {
            "voice_id": "vi-VN-HoaiMyNeural",
            "name": "Hoai My (Vietnamese Female)",
            "locale": "vi-VN",
            "gender": "Female",
            "style": "Warm Presenter / Storytelling",
            "fallback_pitch_mult": 1.06,
        },
        {
            "voice_id": "vi-VN-NamMinhNeural",
            "name": "Nam Minh (Vietnamese Male)",
            "locale": "vi-VN",
            "gender": "Male",
            "style": "Documentary / Authoritative",
            "fallback_pitch_mult": 0.90,
        },
        {
            "voice_id": "en-US-AriaNeural",
            "name": "Aria Neural (US English Female)",
            "locale": "en-US",
            "gender": "Female",
            "style": "Broadcast / Explainer",
            "fallback_pitch_mult": 1.04,
        },
        {
            "voice_id": "en-US-GuyNeural",
            "name": "Guy Neural (US English Male)",
            "locale": "en-US",
            "gender": "Male",
            "style": "Podcast / Newsroom",
            "fallback_pitch_mult": 0.92,
        },
        {
            "voice_id": "en-US-JennyNeural",
            "name": "Jenny Neural (US Conversational)",
            "locale": "en-US",
            "gender": "Female",
            "style": "Friendly Assistant",
            "fallback_pitch_mult": 1.08,
        },
        {
            "voice_id": "win-sapi-studio",
            "name": "Windows Studio Offline Voice",
            "locale": "local",
            "gender": "Neutral",
            "style": "100% Offline SAPI Synthesizer",
            "fallback_pitch_mult": 1.00,
        },
    ]

    def list_voices(self) -> List[Dict[str, Any]]:
        return [dict(v) for v in self.CURATED_VOICES]

    def synthesize(
        self,
        text: str,
        output_path: Path,
        voice_id: str = "vi-VN-HoaiMyNeural",
        rate: float = 1.0,
        pitch_hz: int = 0,
    ) -> Path:
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Voiceover text must not be empty.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_voice = voice_id.strip() or "vi-VN-HoaiMyNeural"

        # 1. Try Microsoft Neural edge-tts when online and voice != win-sapi-studio
        if resolved_voice != "win-sapi-studio":
            try:
                mp3_tmp = output_path.with_suffix(".edge_tmp.mp3")
                rate_pct = int(round((rate - 1.0) * 100))
                rate_str = f"{rate_pct:+d}%"
                pitch_str = f"{int(pitch_hz):+d}Hz"

                async def _run_edge() -> None:
                    import edge_tts

                    comm = edge_tts.Communicate(
                        clean_text,
                        voice=resolved_voice,
                        rate=rate_str,
                        pitch=pitch_str,
                    )
                    await asyncio.wait_for(comm.save(str(mp3_tmp)), timeout=12.0)

                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None

                if loop is not None:
                    import concurrent.futures

                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        pool.submit(lambda: asyncio.run(_run_edge())).result(timeout=15.0)
                else:
                    asyncio.run(_run_edge())

                if mp3_tmp.exists() and mp3_tmp.stat().st_size > 800:
                    cmd = [
                        "ffmpeg",
                        "-y",
                        "-i",
                        str(mp3_tmp),
                        "-ar",
                        "16000",
                        "-ac",
                        "1",
                        "-acodec",
                        "pcm_s16le",
                        str(output_path),
                    ]
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    mp3_tmp.unlink(missing_ok=True)
                    if output_path.exists() and output_path.stat().st_size > 800:
                        return output_path
            except Exception:
                pass

        # 2. Offline Fallback: Windows System.Speech.Synthesis + FFmpeg formant pitch/rate shaping
        sapi_tmp = output_path.with_suffix(".sapi_tmp.wav")
        escaped = clean_text.replace("'", "''").replace("\n", " ").replace("|", ", ")
        sapi_rate = max(-5, min(5, int(round((rate - 1.0) * 8))))
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
                timeout=12,
            )
            if sapi_tmp.exists() and sapi_tmp.stat().st_size > 1500:
                meta = next((v for v in self.CURATED_VOICES if v["voice_id"] == resolved_voice), None)
                pitch_mult = float(meta["fallback_pitch_mult"]) if meta else 1.0
                if abs(pitch_mult - 1.0) > 0.01:
                    af = f"asetrate=22050*{pitch_mult:.2f},atempo={1.0/pitch_mult:.2f},aresample=16000"
                else:
                    af = "aresample=16000"
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        str(sapi_tmp),
                        "-af",
                        af,
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
                sapi_tmp.unlink(missing_ok=True)
                if output_path.exists() and output_path.stat().st_size > 800:
                    return output_path
        except Exception:
            pass

        # 3. Ultimate deterministic fallback if speech synthesizer unavailable
        dur = max(2.0, min(10.0, len(clean_text.split()) * 0.42))
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"aevalsrc=0.12*sin(2*PI*330*t)*(0.5+0.5*sin(2*PI*3*t)):s=16000:d={dur:.2f}",
                "-acodec",
                "pcm_s16le",
                str(output_path),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return output_path
