"""PodcastScriptParser - Pure Domain Parser for Soulful Paragraph Beats, Visual Storyboards & Stage Directions."""

from dataclasses import dataclass, field
import re
from typing import Any, Dict, List, Tuple


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
    """Single readable caption turn bound to a chapter, paragraph beat, voice, rate, pitch, emotion & pause."""

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
    paragraph_group_id: str = ""
    pitch_hz: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "chapter_index": self.chapter_index,
            "chapter_title": self.chapter_title,
            "speaker_name": self.speaker_name,
            "voice_id": self.voice_id,
            "emotion": self.emotion,
            "rate": round(self.rate, 3),
            "pitch_hz": self.pitch_hz,
            "text": self.spoken_text,
            "caption_text": self.caption_text,
            "pause_after_ms": self.pause_after_ms,
            "lead_in_sec": round(self.lead_in_sec, 3),
            "paragraph_group_id": self.paragraph_group_id,
        }


@dataclass
class ParsedPodcastScript:
    """Complete structured representation of a parsed podcast script with paragraph beats & visual scenes."""

    episode_title: str
    is_structured_narrative: bool
    recommended_voice_id: str
    primary_bgm: str = "bgm_piano_melancholic"
    secondary_bgm: str = "bgm_inspiring_acoustic"
    bgm_transition_chapter_index: int | None = None
    chapters: List[PodcastChapterSpec] = field(default_factory=list)
    turns: List[ParsedTurnSpec] = field(default_factory=list)
    sfx_cues: List[PodcastSfxCue] = field(default_factory=list)
    paragraph_beats: List[Dict[str, Any]] = field(default_factory=list)
    visual_scenes: List[Dict[str, Any]] = field(default_factory=list)


class PodcastScriptParser:
    """Transforms raw dialogue or full production podcast scripts into soulful paragraph beats, turns, SFX & visual scenes."""

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
            # Respect explicit specialist voice (e.g. vieneu-*, gemini-*, elevenlabs-*, custom profile)
            if host_voice_id in ("vi-VN-HoaiMyNeural", ""):
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
        raw_chapter_blocks: List[Tuple[int, List[str]]] = []

        current_chapter_idx = -1
        in_notes_section = False
        pending_para_lines: List[str] = []

        def _flush_pending_paragraph() -> None:
            if not pending_para_lines or current_chapter_idx < 0:
                pending_para_lines.clear()
                return
            if is_structured:
                merged = " ".join(pending_para_lines).strip()
                if merged:
                    raw_chapter_blocks[current_chapter_idx][1].append(merged)
            else:
                for item in pending_para_lines:
                    if item.strip():
                        raw_chapter_blocks[current_chapter_idx][1].append(item.strip())
            pending_para_lines.clear()

        for ln in lines:
            if not ln:
                _flush_pending_paragraph()
                continue

            if cls._NOTES_HEADER_RE.match(ln) or cls._NOTES_BULLET_RE.match(ln):
                _flush_pending_paragraph()
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
                _flush_pending_paragraph()
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
                _flush_pending_paragraph()
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

            pending_para_lines.append(remaining_line)

        _flush_pending_paragraph()

        # Determine BGM transition point (first hopeful chapter > 0)
        bgm_transition_idx: int | None = None
        for ch in chapters:
            if ch.chapter_index > 0 and ch.mood == "hopeful":
                bgm_transition_idx = ch.chapter_index
                break

        # Build soulful paragraph beats & readable caption turns
        turns: List[ParsedTurnSpec] = []
        paragraph_beats: List[Dict[str, Any]] = []
        genre_key = genre.strip().lower()
        two_speakers = (not is_structured) and genre_key in ("podcast_dialogue", "tech_explainer")
        turn_counter = 0
        para_counter = 0

        for chap_idx, paragraphs in raw_chapter_blocks:
            chap = chapters[chap_idx]
            is_hook = "hook" in chap.title.lower() or (is_structured and chap_idx == 0 and len(chapters) > 1)
            chap_lead_consumed = False

            for para in paragraphs:
                cleaned_para = para.strip().strip('"').strip("“").strip("”").strip()
                if not cleaned_para:
                    continue

                sub_lines = (
                    [p.strip() for p in cleaned_para.split("|") if p.strip()]
                    if not is_structured
                    else [cleaned_para]
                )

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

                    para_counter += 1
                    para_group_id = f"para_{para_counter:03d}" if is_structured else ""
                    para_lead_sec = chap.lead_in_sec if (not chap_lead_consumed) else 0.0
                    chap_lead_consumed = True

                    emotion, base_rate, base_pitch, para_pause_ms = cls._classify_paragraph_prosody(
                        body_text=body_text,
                        chap_mood=chap.mood,
                        is_hook=is_hook,
                        is_structured=is_structured,
                    )

                    if is_hook:
                        hook_specs = cls._build_hook_anchor_turns(body_text)
                        para_turn_ids: List[str] = []
                        para_spoken_parts: List[str] = []
                        for h_idx, h_spec in enumerate(hook_specs):
                            turn_counter += 1
                            tid = f"turn_{turn_counter:03d}"
                            para_turn_ids.append(tid)
                            para_spoken_parts.append(h_spec["spoken"])
                            turns.append(
                                ParsedTurnSpec(
                                    turn_id=tid,
                                    chapter_index=chap_idx,
                                    chapter_title=chap.title,
                                    speaker_name=spk_name,
                                    voice_id=voice_for_line,
                                    emotion=h_spec["emotion"],
                                    rate=h_spec["rate"],
                                    pitch_hz=h_spec["pitch_hz"],
                                    spoken_text=h_spec["spoken"],
                                    caption_text=h_spec["caption"],
                                    pause_after_ms=h_spec["pause_ms"],
                                    lead_in_sec=para_lead_sec if h_idx == 0 else 0.0,
                                    paragraph_group_id=para_group_id,
                                )
                            )
                        paragraph_beats.append(
                            {
                                "paragraph_id": para_group_id or f"para_{para_counter:03d}",
                                "chapter_index": chap_idx,
                                "chapter_title": chap.title,
                                "speaker_name": spk_name,
                                "voice_id": voice_for_line,
                                "emotion": "late_night",
                                "rate": 0.87,
                                "pitch_hz": -5,
                                "pause_after_ms": 950,
                                "lead_in_sec": round(para_lead_sec, 3),
                                "text": " ".join(para_spoken_parts),
                                "clean_text": cls._clean_caption_text(body_text),
                                "word_count": max(1, len(cls._clean_caption_text(body_text).split())),
                                "turn_ids": para_turn_ids,
                            }
                        )
                        continue

                    phrases = cls._chunk_into_caption_phrases(body_text, max_words=22)
                    para_turn_ids = []
                    for p_idx, phrase in enumerate(phrases):
                        turn_counter += 1
                        tid = f"turn_{turn_counter:03d}"
                        para_turn_ids.append(tid)
                        is_last_in_para = p_idx == len(phrases) - 1
                        turn_pause_ms = para_pause_ms if is_last_in_para else (180 if is_structured else 350)

                        caption_clean = cls._clean_caption_text(phrase)
                        if two_speakers and spk_name:
                            caption_clean = f"{spk_name}: {caption_clean}"

                        turns.append(
                            ParsedTurnSpec(
                                turn_id=tid,
                                chapter_index=chap_idx,
                                chapter_title=chap.title,
                                speaker_name=spk_name,
                                voice_id=voice_for_line,
                                emotion=emotion,
                                rate=base_rate,
                                pitch_hz=base_pitch,
                                spoken_text=phrase,
                                caption_text=caption_clean,
                                pause_after_ms=turn_pause_ms,
                                lead_in_sec=para_lead_sec if p_idx == 0 else 0.0,
                                paragraph_group_id=para_group_id,
                            )
                        )

                    clean_para = cls._clean_caption_text(body_text)
                    paragraph_beats.append(
                        {
                            "paragraph_id": para_group_id or f"para_{para_counter:03d}",
                            "chapter_index": chap_idx,
                            "chapter_title": chap.title,
                            "speaker_name": spk_name,
                            "voice_id": voice_for_line,
                            "emotion": emotion,
                            "rate": round(base_rate, 3),
                            "pitch_hz": base_pitch,
                            "pause_after_ms": para_pause_ms,
                            "lead_in_sec": round(para_lead_sec, 3),
                            "text": body_text,
                            "clean_text": clean_para,
                            "word_count": max(1, len(clean_para.split())),
                            "turn_ids": para_turn_ids,
                        }
                    )

        visual_scenes = cls._build_visual_scenes(
            episode_title=episode_title,
            chapters=chapters,
            paragraph_beats=paragraph_beats,
            is_structured=is_structured,
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
            paragraph_beats=paragraph_beats,
            visual_scenes=visual_scenes,
        )

    @staticmethod
    def _clean_caption_text(text: str) -> str:
        caption_clean = re.sub(
            r"\[(pause[^\]]*|emotion:[^\]]*|laughter|sigh|breath)\]",
            "",
            text,
            flags=re.IGNORECASE,
        )
        return re.sub(r"\s+", " ", caption_clean).strip()

    @staticmethod
    def _classify_paragraph_prosody(
        body_text: str,
        chap_mood: str,
        is_hook: bool,
        is_structured: bool,
    ) -> Tuple[str, float, int, int]:
        """Classify paragraph emotional prosody -> (emotion, rate, pitch_hz, pause_after_ms)."""
        if is_hook:
            return "late_night", 0.87, -5, 950

        # Hopeful Turnaround & Outro paragraphs take precedence once narrative shifts to light
        if chap_mood == "hopeful":
            return "warm", 0.94, -1, 900

        low = body_text.lower()

        # Urgent Collapse / Market Crash paragraphs
        if any(
            k in low
            for k in (
                "thị trường sập",
                "không kiến thức nền tảng",
                "lao dốc",
                "đống sắt vụn",
                "khoản nợ khổng lồ",
            )
        ):
            return "dramatic", 0.98, -4, 740

        # Introspective Multi-Angle Analysis paragraphs
        if any(
            k in low
            for k in (
                "góc độ thứ nhất",
                "góc độ thứ hai",
                "góc độ thứ ba",
                "ba góc độ",
                "mổ xẻ thất bại",
                "thiên kiến kẻ sống sót",
                "cú sốc bản ngã",
            )
        ):
            return "late_night", 0.93, -3, 850

        if is_structured:
            return "late_night", 0.94, -3, 800

        return "warm", 1.0, 0, 350

    @classmethod
    def _build_hook_anchor_turns(cls, body_text: str) -> List[Dict[str, Any]]:
        """Split Hook deliberately at the 3 psychological anchors ('30 tuổi.', 'tắt ngấm,', 'con số âm.') for dramatic pacing."""
        cleaned = re.sub(r"\s+", " ", body_text).strip()
        results: List[Dict[str, Any]] = []
        remainder = cleaned

        # Anchor 1: Opening "30 tuổi."
        m_age = re.match(r"^(30\s*tuổi\s*[.!?…])\s*(.+)$", remainder, flags=re.IGNORECASE)
        if m_age:
            anchor_1 = m_age.group(1).strip()
            remainder = m_age.group(2).strip()
            results.append(
                {
                    "spoken": f"{anchor_1} [pause 750ms]",
                    "caption": cls._clean_caption_text(anchor_1),
                    "emotion": "late_night",
                    "rate": 0.86,
                    "pitch_hz": -5,
                    "pause_ms": 750,
                }
            )

        # Anchor 2: "... đã tắt ngấm,"
        m_rig = re.search(r"^(.*?tắt\s*ngấm\s*[,.;])\s*(.+)$", remainder, flags=re.IGNORECASE)
        if m_rig and len(m_rig.group(1).split()) <= 26:
            anchor_2 = m_rig.group(1).strip()
            remainder = m_rig.group(2).strip()
            results.append(
                {
                    "spoken": f"{anchor_2} [pause 650ms]",
                    "caption": cls._clean_caption_text(anchor_2),
                    "emotion": "late_night",
                    "rate": 0.88,
                    "pitch_hz": -5,
                    "pause_ms": 650,
                }
            )

        # Remaining Hook phrases (ending on Anchor 3 "...con số âm.")
        tail_phrases = cls._chunk_into_caption_phrases(remainder, max_words=21)
        for idx, ph in enumerate(tail_phrases):
            is_last = idx == len(tail_phrases) - 1
            spoken_ph = cls._inject_hook_pauses(ph)
            results.append(
                {
                    "spoken": spoken_ph,
                    "caption": cls._clean_caption_text(ph),
                    "emotion": "late_night",
                    "rate": 0.87 if is_last else 0.89,
                    "pitch_hz": -5 if is_last else -4,
                    "pause_ms": 950 if is_last else 520,
                }
            )

        if not results:
            spoken_fallback = cls._inject_hook_pauses(cleaned)
            results.append(
                {
                    "spoken": spoken_fallback,
                    "caption": cls._clean_caption_text(cleaned)[:120],
                    "emotion": "late_night",
                    "rate": 0.87,
                    "pitch_hz": -5,
                    "pause_ms": 950,
                }
            )

        return results

    @classmethod
    def _build_visual_scenes(
        cls,
        episode_title: str,
        chapters: List[PodcastChapterSpec],
        paragraph_beats: List[Dict[str, Any]],
        is_structured: bool,
    ) -> List[Dict[str, Any]]:
        """Generate rich cinematic 16:9 visual storyboard scene specs (8 scenes for full narrative arcs)."""
        if not chapters or not paragraph_beats:
            return []

        total_words = max(1, sum(int(p.get("word_count", 1)) for p in paragraph_beats))
        lower_ep = (episode_title + " " + " ".join(c.title for c in chapters)).lower()

        # Specialized 8-scene cinematic arc for Episode 1 ("Tuổi 30" / 5-chapter narrative with 3 angles)
        has_three_angles = any("góc độ thứ nhất" in str(p.get("clean_text", "")).lower() for p in paragraph_beats)
        if is_structured and len(chapters) >= 5 and ("tuổi 30" in lower_ep or has_three_angles):
            chap_words: Dict[int, int] = {}
            for c in chapters:
                chap_words[c.chapter_index] = max(
                    1,
                    sum(int(p.get("word_count", 1)) for p in paragraph_beats if p["chapter_index"] == c.chapter_index),
                )

            # Partition chapter ratios cleanly across 8 narrative scenes: 1 + 2 + 3 + 1 + 1 = 8
            raw_defs: List[Tuple[int, float, str, str, str]] = [
                (
                    0,
                    float(chap_words.get(0, 40)),
                    "Hook: Cú Ngã Ở Ngưỡng Cửa Tuổi 30",
                    "melancholic",
                    "Cinematic late-night bedroom in rainy Saigon, a 30-year-old Vietnamese man sitting quietly on the edge of a bed beside powered-down GPU crypto mining rigs with motionless dark cooling fans, glowing smartphone notifications on a wooden desk, moody teal and amber chiaroscuro lighting, shallow depth of field, 35mm anamorphic film grain, no text",
                ),
                (
                    1,
                    float(chap_words.get(1, 100)) * 0.52,
                    "Mở Đầu: Giấc Mơ Đổi Đời & Áp Lực Tuổi Đôi Mươi",
                    "melancholic",
                    "Atmospheric apartment window at night overlooking distant glittering city skyscrapers, young Vietnamese man gazing out reflectively while neon financial candlestick charts softly reflect on rain-streaked glass, melancholic lo-fi cinema lighting, 35mm lens, no text",
                ),
                (
                    1,
                    float(chap_words.get(1, 100)) * 0.48,
                    "Biến Cố: Thị Trường Lao Dốc & Đống Sắt Vụn",
                    "dramatic",
                    "Dramatic close-up of dusty unplugged computer mining hardware racks in a dim apartment room, red downward market glow fading on a dark monitor, stack of utility bills under a single warm tungsten desk lamp, moody rain shadows on concrete wall, photorealistic cinema, no text",
                ),
                (
                    2,
                    float(chap_words.get(2, 180)) * 0.34,
                    "Góc Độ 1: Tâm Lý Học Của Sự Thiếu Thốn",
                    "melancholic",
                    "Conceptual neo-noir night scene of a solitary man walking down a narrow wet street alley under warm sodium streetlights while blurred city traffic rushes past in the background symbolizing impatience and fear of falling behind, cinematic 50mm lens, no text",
                ),
                (
                    2,
                    float(chap_words.get(2, 180)) * 0.33,
                    "Góc Độ 2: Thiên Kiến Kẻ Sống Sót",
                    "melancholic",
                    "Artistic chiaroscuro composition of a single spotlighted glass chess king standing on a dark wet table surrounded by nine fallen pieces in deep shadow, rain droplets on dark windowpane behind, contemplative documentary cinematography, slate blue and warm gold palette, no text",
                ),
                (
                    2,
                    float(chap_words.get(2, 180)) * 0.33,
                    "Góc Độ 3: Cú Sốc Bản Ngã & Viết Lại CV Ở Tuổi 30",
                    "melancholic",
                    "Intimate late-night desk scene, a 30-year-old Vietnamese man typing a fresh resume on a laptop beside a steaming ceramic mug of black coffee, warm tungsten desk lamp casting soft shadows across a handwritten notebook, humble introspective mood, 35mm film grain, no text",
                ),
                (
                    3,
                    float(chap_words.get(3, 120)),
                    "Bước Ngoặt: Cởi Bỏ Tự Ái, Xây Lại Nền Móng Thật",
                    "hopeful",
                    "Golden early morning sunrise rays streaming through sheer apartment curtains onto a neat wooden desk with a job application folder and a monthly debt-repayment checklist, calm determined Vietnamese man buttoning a crisp white shirt, warm acoustic morning atmosphere, 35mm cinema lens, no text",
                ),
                (
                    4,
                    float(chap_words.get(4, 80)),
                    "Kết Thúc: Bén Rễ Trong Đất Tối Để Vươn Cao",
                    "hopeful",
                    "Poetic cinematic wide shot of a resilient young green tree with deep roots visible in rich dark soil reaching upward into warm golden sunrise light over a tranquil misty horizon, bokeh morning dew, inspiring hopeful color grade, 35mm film aesthetic, no text",
                ),
            ]

            weight_sum = max(1.0, sum(w for _, w, _, _, _ in raw_defs))
            scenes: List[Dict[str, Any]] = []
            cursor_ratio = 0.0
            for idx, (c_idx, weight, sc_title, sc_mood, prompt) in enumerate(raw_defs, start=1):
                span = weight / weight_sum
                end_r = 1.0 if idx == len(raw_defs) else min(1.0, cursor_ratio + span)
                scenes.append(
                    {
                        "scene_id": f"scene_{idx:02d}",
                        "chapter_index": min(c_idx, len(chapters) - 1),
                        "title": sc_title,
                        "mood": sc_mood,
                        "visual_prompt": prompt,
                        "start_ratio": round(cursor_ratio, 4),
                        "end_ratio": round(end_r, 4),
                    }
                )
                cursor_ratio = end_r
            return scenes

        # Generic dynamic storyboard generator for any multi-chapter or conversational podcast
        scenes = []
        cursor_words = 0
        scene_idx = 0
        for chap in chapters:
            chap_paras = [p for p in paragraph_beats if p["chapter_index"] == chap.chapter_index]
            if not chap_paras:
                continue
            # Split long chapters (>= 3 paragraphs) into 2 visual scenes for dynamic pacing
            groups = (
                [chap_paras[: len(chap_paras) // 2], chap_paras[len(chap_paras) // 2 :]]
                if len(chap_paras) >= 3 and len(chapters) <= 6
                else [chap_paras]
            )
            for g_i, grp in enumerate(groups):
                if not grp:
                    continue
                scene_idx += 1
                grp_words = sum(int(p.get("word_count", 1)) for p in grp)
                st_r = cursor_words / total_words
                cursor_words += grp_words
                en_r = min(1.0, cursor_words / total_words)
                snippet = str(grp[0].get("clean_text", ""))[:110]
                lighting = (
                    "warm golden morning sunlight, hopeful acoustic cinema palette"
                    if chap.mood == "hopeful"
                    else "moody late-night tungsten and slate-blue chiaroscuro lighting, rain reflections"
                )
                suffix = f" (Part {g_i + 1})" if len(groups) > 1 else ""
                scenes.append(
                    {
                        "scene_id": f"scene_{scene_idx:02d}",
                        "chapter_index": chap.chapter_index,
                        "title": f"{chap.title}{suffix}",
                        "mood": chap.mood,
                        "visual_prompt": (
                            f"Cinematic editorial podcast illustration for '{chap.title}', "
                            f"inspired by theme: '{snippet}', {lighting}, shallow depth of field, "
                            "35mm anamorphic film grain, 16:9 widescreen composition, no text"
                        ),
                        "start_ratio": round(st_r, 4),
                        "end_ratio": round(en_r, 4),
                    }
                )
        if scenes:
            scenes[-1]["end_ratio"] = 1.0
        return scenes

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
            r"\1 [pause 750ms]",
            out,
            flags=re.IGNORECASE,
        )
        out = re.sub(
            r"(tắt\s*ngấm\s*[,.;]?)(?!\s*\[pause)",
            r"\1 [pause 650ms]",
            out,
            flags=re.IGNORECASE,
        )
        out = re.sub(
            r"(con\s*số\s*âm\s*[.,!?;]?)(?!\s*\[pause)",
            r"\1 [pause 950ms]",
            out,
            flags=re.IGNORECASE,
        )
        return re.sub(r"\s+", " ", out).strip()

    @staticmethod
    def _chunk_into_caption_phrases(paragraph: str, max_words: int = 22) -> List[str]:
        """Split a paragraph into readable spoken caption phrases (12–25 words) without breaking Vietnamese syntax."""
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
                if buffer:
                    chunks.append(buffer)
                    buffer = ""
                clauses = [c.strip() for c in re.split(r"(?<=[,–—:])\s+", sent) if c.strip()]
                clause_buf = ""
                for cl in clauses:
                    cand = f"{clause_buf} {cl}".strip() if clause_buf else cl
                    if len(cand.split()) <= max_words + 3:
                        clause_buf = cand
                    else:
                        if clause_buf:
                            chunks.append(clause_buf)
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
                cand = f"{buffer} {sent}".strip() if buffer else sent
                is_dramatic_short = len(buffer.split()) <= 4 and "30 tuổi" in buffer.lower()
                if buffer and (len(cand.split()) <= 16) and not is_dramatic_short:
                    buffer = cand
                else:
                    if buffer:
                        chunks.append(buffer)
                    buffer = sent

        if buffer:
            chunks.append(buffer)

        return chunks
