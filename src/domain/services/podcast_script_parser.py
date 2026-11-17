"""PodcastScriptParser - Pure Domain Parser for Structured Broadcast Podcast Scripts & Stage Directions."""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List


@dataclass
class PodcastSfxCue:
    """Diegetic or atmospheric SFX cue extracted from script stage directions."""

    sfx_id: str
    chapter_index: int = 0
    offset_sec: float = 0.0
    volume: float = 0.72
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sfx_id": self.sfx_id,
            "chapter_index": self.chapter_index,
            "offset_sec": round(self.offset_sec, 3),
            "volume": round(self.volume, 2),
            "description": self.description,
        }


@dataclass
class PodcastChapterSpec:
    """Chapter metadata extracted from timestamped podcast headers."""

    chapter_index: int
    title: str
    mood: str = "melancholic"  # melancholic | hopeful | neutral
    bgm_preset: str = "bgm_piano_melancholic"
    lead_in_sec: float = 0.0
    start_time: float = 0.0
    end_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter_index": self.chapter_index,
            "title": self.title,
            "mood": self.mood,
            "bgm_preset": self.bgm_preset,
            "lead_in_sec": round(self.lead_in_sec, 3),
            "start_time": round(self.start_time, 3),
            "end_time": round(self.end_time, 3),
        }


@dataclass
class ParsedTurnSpec:
    """Single spoken turn bound to a chapter, voice, rate, emotion, and pause."""

    turn_id: str
    chapter_index: int
    chapter_title: str
    speaker_name: str
    voice_id: str
    emotion: str
    rate: float
    spoken_text: str
    caption_text: str
    pause_after_ms: int = 420
    lead_in_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "chapter_index": self.chapter_index,
            "chapter_title": self.chapter_title,
            "speaker_name": self.speaker_name,
            "voice_id": self.voice_id,
            "emotion": self.emotion,
            "rate": round(self.rate, 3),
            "text": self.spoken_text,
            "caption_text": self.caption_text,
            "pause_after_ms": self.pause_after_ms,
            "lead_in_sec": round(self.lead_in_sec, 3),
        }


@dataclass
class ParsedPodcastScript:
    """Complete structured representation of a parsed podcast script."""

    episode_title: str
    is_structured_narrative: bool
    recommended_voice_id: str
    primary_bgm: str = "bgm_piano_melancholic"
    secondary_bgm: str = "bgm_inspiring_acoustic"
    bgm_transition_chapter_index: int | None = None
    chapters: List[PodcastChapterSpec] = field(default_factory=list)
    turns: List[ParsedTurnSpec] = field(default_factory=list)
    sfx_cues: List[PodcastSfxCue] = field(default_factory=list)


class PodcastScriptParser:
    """Transforms raw dialogue or full production podcast scripts into structured turns, chapters, SFX & BGM."""

    _EPISODE_RE = re.compile(
        r"^(?:TẬP|TAP|EPISODE|PHẦN)\s*\d+\s*[:\-–—]\s*(.+)$",
        flags=re.IGNORECASE,
    )
    _CHAPTER_TIME_RE = re.compile(
        r"^\s*(\d{1,2}:\d{2})\s*[\-–—~]+\s*(\d{1,2}:\d{2})\s*\|\s*(.+)$"
    )
    _NOTES_HEADER_RE = re.compile(
        r"^\s*(?:GỢI Ý THU ÂM|HƯỚNG DẪN THU ÂM|GHI CHÚ SẢN XUẤT|PRODUCTION NOTES|DIRECTOR NOTES)\b",
        flags=re.IGNORECASE,
    )
    _NOTES_BULLET_RE = re.compile(
        r"^\s*(?:Nhịp điệu\s*\(Pacing\)|Chất giọng|Nhạc nền\s*\(BGM\))\s*:",
        flags=re.IGNORECASE,
    )
    _INLINE_VOICESTUDIO_TAG_RE = re.compile(
        r"^(?:pause(?:\s+\d+(?:\.\d+)?(?:ms|s))?|emotion:[a-zA-Z_]+|laughter|sigh|breath)$",
        flags=re.IGNORECASE,
    )

    @classmethod
    def parse(
        cls,
        raw_content: str,
        genre: str = "podcast_dialogue",
        host_voice_id: str = "vi-VN-HoaiMyNeural",
        guest_voice_id: str = "vi-VN-NamMinhNeural",
    ) -> ParsedPodcastScript:
        text = (raw_content or "").strip()
        if not text:
            raise ValueError("Podcast content must not be empty.")

        lines = [ln.strip() for ln in text.splitlines()]
        lower_full = text.lower()

        # Detect structured narrative / production script
        has_chapters = any(cls._CHAPTER_TIME_RE.match(ln) for ln in lines if ln)
        has_episode_header = any(cls._EPISODE_RE.match(ln) for ln in lines if ln)
        has_stage_brackets = bool(
            re.search(r"\[\s*(?:âm thanh|nhạc nền|sfx|music|bgm)\b", lower_full, flags=re.IGNORECASE)
        )
        is_structured = has_chapters or has_episode_header or has_stage_brackets

        # Pre-scan recording notes for voice / BGM recommendations
        notes_voice = host_voice_id
        if is_structured:
            if any(
                kw in lower_full
                for kw in (
                    "tông giọng trầm",
                    "giọng trầm",
                    "chàng trai",
                    "thủ thỉ",
                    "nửa đêm",
                    "nam minh",
                )
            ):
                notes_voice = "vi-VN-NamMinhNeural"
        elif genre.strip().lower() in ("late_night_story", "thriller_mystery", "motivational_epic"):
            if host_voice_id == "vi-VN-HoaiMyNeural" and "nam" in lower_full:
                notes_voice = "vi-VN-NamMinhNeural"

        primary_bgm = "bgm_piano_melancholic" if is_structured else "bgm_lofi_chill"
        secondary_bgm = "bgm_inspiring_acoustic"

        episode_title = "KINETIX PODCAST STUDIO"
        chapters: List[PodcastChapterSpec] = []
        sfx_cues: List[PodcastSfxCue] = []
        raw_chapter_blocks: List[tuple[int, List[str]]] = []

        current_chapter_idx = -1
        in_notes_section = False

        for ln in lines:
            if not ln:
                continue

            if cls._NOTES_HEADER_RE.match(ln) or cls._NOTES_BULLET_RE.match(ln):
                in_notes_section = True
                continue
            if in_notes_section:
                continue

            ep_match = cls._EPISODE_RE.match(ln)
            if ep_match and current_chapter_idx == -1:
                episode_title = ln.strip()
                continue

            chap_match = cls._CHAPTER_TIME_RE.match(ln)
            if chap_match:
                chap_title = chap_match.group(3).strip()
                current_chapter_idx = len(chapters)
                is_hopeful = any(
                    k in chap_title.lower()
                    for k in ("bước ngoặt", "kết thúc", "hy vọng", "bắt đầu lại", "ánh sáng", "outro")
                )
                chapters.append(
                    PodcastChapterSpec(
                        chapter_index=current_chapter_idx,
                        title=chap_title,
                        mood="hopeful" if is_hopeful else "melancholic",
                        bgm_preset=secondary_bgm if is_hopeful else primary_bgm,
                        lead_in_sec=0.0,
                    )
                )
                raw_chapter_blocks.append((current_chapter_idx, []))
                continue

            # Extract bracketed stage cues (e.g. [Âm thanh: ...], [Nhạc nền ...])
            remaining_line = cls._extract_stage_brackets(
                ln,
                chapter_index=max(0, current_chapter_idx),
                chapters=chapters,
                sfx_cues=sfx_cues,
            )
            if not remaining_line:
                continue

            if current_chapter_idx == -1:
                current_chapter_idx = 0
                default_mood = "melancholic" if is_structured else "neutral"
                chapters.append(
                    PodcastChapterSpec(
                        chapter_index=0,
                        title="PHẦN MỞ ĐẦU" if is_structured else "PODCAST EPISODE",
                        mood=default_mood,
                        bgm_preset=primary_bgm,
                    )
                )
                raw_chapter_blocks.append((0, []))

            raw_chapter_blocks[current_chapter_idx][1].append(remaining_line)

        # Determine BGM transition point (first hopeful chapter > 0)
        bgm_transition_idx: int | None = None
        for ch in chapters:
            if ch.chapter_index > 0 and ch.mood == "hopeful":
                bgm_transition_idx = ch.chapter_index
                break

        # Build spoken turns per chapter
        turns: List[ParsedTurnSpec] = []
        genre_key = genre.strip().lower()
        two_speakers = (not is_structured) and genre_key in ("podcast_dialogue", "tech_explainer")
        turn_counter = 0

        for chap_idx, paragraphs in raw_chapter_blocks:
            chap = chapters[chap_idx]
            is_hook = "hook" in chap.title.lower() or (is_structured and chap_idx == 0 and len(chapters) > 1)
            chap_lead_consumed = False

            for para in paragraphs:
                # Strip outer smart/ASCII quotes around monologue blocks
                cleaned_para = para.strip().strip('"').strip("“").strip("”").strip()
                if not cleaned_para:
                    continue

                # If explicit dialogue `Host: ... | Guest: ...` (only when NOT structured monologue)
                sub_lines = [p.strip() for p in cleaned_para.split("|") if p.strip()] if not is_structured else [cleaned_para]

                for sub_ln in sub_lines:
                    spk_name = "Narrator" if is_structured else "Host"
                    voice_for_line = notes_voice
                    body_text = sub_ln

                    if not is_structured and ":" in sub_ln:
                        prefix, rest = sub_ln.split(":", 1)
                        if 1 <= len(prefix.strip()) <= 22 and not prefix.strip().isdigit():
                            spk_name = prefix.strip()
                            body_text = rest.strip()
                            if spk_name.lower() in ("guest", "khách", "co-host", "bạn"):
                                voice_for_line = guest_voice_id
                            elif two_speakers and (turn_counter % 2 == 1):
                                voice_for_line = guest_voice_id
                    elif two_speakers and (turn_counter % 2 == 1):
                        spk_name = "Guest"
                        voice_for_line = guest_voice_id

                    phrases = cls._chunk_into_caption_phrases(body_text, max_words=21 if is_hook else 23)
                    for p_idx, phrase in enumerate(phrases):
                        turn_counter += 1
                        lead_sec = chap.lead_in_sec if (not chap_lead_consumed) else 0.0
                        chap_lead_consumed = True

                        spoken = phrase
                        if is_hook:
                            spoken = cls._inject_hook_pauses(spoken)
                            emotion = "late_night"
                            rate = 0.90
                            pause_ms = 620
                        elif chap.mood == "hopeful":
                            emotion = "warm"
                            rate = 0.95
                            pause_ms = 460 if p_idx == len(phrases) - 1 else 340
                        elif is_structured:
                            emotion = "late_night"
                            rate = 0.94
                            pause_ms = 500 if p_idx == len(phrases) - 1 else 360
                        else:
                            emotion = "warm"
                            rate = 1.0
                            pause_ms = 350

                        caption_clean = re.sub(
                            r"\[(pause[^\]]*|emotion:[^\]]*|laughter|sigh|breath)\]",
                            "",
                            phrase,
                            flags=re.IGNORECASE,
                        )
                        caption_clean = re.sub(r"\s+", " ", caption_clean).strip()
                        if two_speakers and spk_name:
                            caption_clean = f"{spk_name}: {caption_clean}"

                        turns.append(
                            ParsedTurnSpec(
                                turn_id=f"turn_{turn_counter:03d}",
                                chapter_index=chap_idx,
                                chapter_title=chap.title,
                                speaker_name=spk_name,
                                voice_id=voice_for_line,
                                emotion=emotion,
                                rate=rate,
                                spoken_text=spoken,
                                caption_text=caption_clean,
                                pause_after_ms=pause_ms,
                                lead_in_sec=lead_sec,
                            )
                        )

        return ParsedPodcastScript(
            episode_title=episode_title,
            is_structured_narrative=is_structured,
            recommended_voice_id=notes_voice,
            primary_bgm=primary_bgm,
            secondary_bgm=secondary_bgm,
            bgm_transition_chapter_index=bgm_transition_idx,
            chapters=chapters,
            turns=turns,
            sfx_cues=sfx_cues,
        )

    @classmethod
    def _extract_stage_brackets(
        cls,
        line: str,
        chapter_index: int,
        chapters: List[PodcastChapterSpec],
        sfx_cues: List[PodcastSfxCue],
    ) -> str:
        """Strip non-spoken [Âm thanh: ...] / [Nhạc nền ...] cues while preserving VoiceStudio inline tags."""

        def _replacer(match: re.Match[str]) -> str:
            inner = match.group(1).strip()
            if cls._INLINE_VOICESTUDIO_TAG_RE.match(inner):
                return match.group(0)

            low = inner.lower()
            # Map diegetic SFX cues
            if any(k in low for k in ("quạt tản nhiệt", "quạt máy", "cooling fan", "tắt lịm", "tắt ngấm")):
                sfx_cues.append(
                    PodcastSfxCue(
                        sfx_id="sfx_fan_shutdown",
                        chapter_index=chapter_index,
                        offset_sec=0.0,
                        volume=0.78,
                        description=inner,
                    )
                )
                if 0 <= chapter_index < len(chapters):
                    chapters[chapter_index].lead_in_sec = max(chapters[chapter_index].lead_in_sec, 2.5)

            if any(k in low for k in ("tin nhắn", "điện thoại rung", "rung liên hồi", "phone vibrat", "notification")):
                sfx_cues.append(
                    PodcastSfxCue(
                        sfx_id="sfx_phone_vibrate",
                        chapter_index=chapter_index,
                        offset_sec=1.25,
                        volume=0.75,
                        description=inner,
                    )
                )
                if 0 <= chapter_index < len(chapters):
                    chapters[chapter_index].lead_in_sec = max(chapters[chapter_index].lead_in_sec, 2.6)

            # Map BGM mood shifts inside brackets
            if 0 <= chapter_index < len(chapters):
                if any(k in low for k in ("nâng tông", "ấm áp", "hy vọng", "inspiring", "acoustic")):
                    chapters[chapter_index].mood = "hopeful"
                    chapters[chapter_index].bgm_preset = "bgm_inspiring_acoustic"
                elif any(k in low for k in ("piano trầm", "buồn", "melancholic", "chậm rãi")):
                    chapters[chapter_index].mood = "melancholic"
                    chapters[chapter_index].bgm_preset = "bgm_piano_melancholic"

            return " "

        cleaned = re.sub(r"\[([^\]]+)\]", _replacer, line)
        return re.sub(r"\s+", " ", cleaned).strip()

    @staticmethod
    def _inject_hook_pauses(text: str) -> str:
        """Add psychological pauses after anchor words ('30 tuổi', 'tắt ngấm', 'con số âm') per recording direction."""
        out = text
        out = re.sub(
            r"(30\s*tuổi\s*[.,!?;]?)(?!\s*\[pause)",
            r"\1 [pause 650ms]",
            out,
            flags=re.IGNORECASE,
        )
        out = re.sub(
            r"(tắt\s*ngấm\s*[,.;]?)(?!\s*\[pause)",
            r"\1 [pause 600ms]",
            out,
            flags=re.IGNORECASE,
        )
        out = re.sub(
            r"(con\s*số\s*âm\s*[.,!?;]?)(?!\s*\[pause)",
            r"\1 [pause 750ms]",
            out,
            flags=re.IGNORECASE,
        )
        return re.sub(r"\s+", " ", out).strip()

    @staticmethod
    def _chunk_into_caption_phrases(paragraph: str, max_words: int = 22) -> List[str]:
        """Split a paragraph into readable spoken caption phrases (12–24 words) without breaking Vietnamese syntax."""
        sentences = [
            s.strip()
            for s in re.split(r"(?<=[.!?…;])\s+", paragraph.strip())
            if s.strip()
        ]
        if not sentences:
            return []

        chunks: List[str] = []
        buffer = ""

        for sent in sentences:
            words = sent.split()
            if len(words) > max_words + 4:
                # Flush current buffer first
                if buffer:
                    chunks.append(buffer)
                    buffer = ""
                # Split long sentence along commas / dashes
                clauses = [c.strip() for c in re.split(r"(?<=[,–—:])\s+", sent) if c.strip()]
                clause_buf = ""
                for cl in clauses:
                    cand = f"{clause_buf} {cl}".strip() if clause_buf else cl
                    if len(cand.split()) <= max_words + 3:
                        clause_buf = cand
                    else:
                        if clause_buf:
                            chunks.append(clause_buf)
                        # If single clause is still huge, slice cleanly every max_words words
                        cl_words = cl.split()
                        if len(cl_words) > max_words + 5:
                            for idx in range(0, len(cl_words), max_words):
                                chunks.append(" ".join(cl_words[idx : idx + max_words]))
                            clause_buf = ""
                        else:
                            clause_buf = cl
                if clause_buf:
                    chunks.append(clause_buf)
            else:
                # Merge ultra-short sentences (e.g. "30 tuổi.") only if total <= 14 words AND not ending with Hook anchor
                cand = f"{buffer} {sent}".strip() if buffer else sent
                is_dramatic_short = len( buffer.split() ) <= 4 and "30 tuổi" in buffer.lower()
                if buffer and (len(cand.split()) <= 15) and not is_dramatic_short:
                    buffer = cand
                else:
                    if buffer:
                        chunks.append(buffer)
                    buffer = sent

        if buffer:
            chunks.append(buffer)

        return chunks
