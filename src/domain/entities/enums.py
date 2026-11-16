"""Domain Enumerations for KinetixAI."""

from enum import Enum


class RenderEngineType(str, Enum):
    """Supported visual composition render engines."""

    REMOTION = "remotion"
    HYPERFRAMES = "hyperframes"


class JobStatus(str, Enum):
    """Lifecycle states of an automated video production pipeline job."""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    EXTRACTING_AUDIO = "extracting_audio"
    TRANSCRIBING = "transcribing"
    RENDERING_VISUALS = "rendering_visuals"
    MERGING = "merging"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AspectRatioPreset(str, Enum):
    """Supported output aspect ratio presets for NLE reframing."""

    LANDSCAPE_16_9 = "16:9"
    VERTICAL_9_16 = "9:16"
    SQUARE_1_1 = "1:1"


class ColorLookPreset(str, Enum):
    """Broadcast & cinematic LUT / color grading presets."""

    NATURAL = "natural"
    TEAL_ORANGE = "teal_orange"
    WARM_VINTAGE = "warm_vintage"
    NOIR_BW = "noir_bw"
    STUDIO_CRISP = "studio_crisp"


class TemplatePreset(str, Enum):
    """Supported Remotion & HyperFrames motion graphics templates."""

    CAPTION_TEMPLATE = "CaptionTemplate"
    KINETIC_TITLE = "KineticTitleCard"
    SOCIAL_POP = "SocialPopCaptions"
    TECH_CALLOUT = "TechCalloutHUD"


class TransitionPreset(str, Enum):
    """Supported non-linear video transition presets."""

    NONE = "none"
    FADE_BLACK = "fade_black"
    CROSS_DISSOLVE = "cross_dissolve"
    WIPE_LEFT = "wipe_left"
    SLIDE_UP = "slide_up"
    GLITCH_FLASH = "glitch_flash"


class AnimationPreset(str, Enum):
    """Supported camera & motion graphic animation presets."""

    SPRING_POP = "spring_pop"
    KEN_BURNS_ZOOM = "ken_burns_zoom"
    TYPEWRITER = "typewriter_reveal"
    NEON_PULSE = "neon_glow_pulse"
    SLIDE_BOUNCE = "slide_up_bounce"
    CAMERA_SHAKE = "camera_shake_impact"


class StorytellingGenre(str, Enum):
    """Supported multi-voice Podcast & Storytelling narration genres (VoiceStudio-inspired)."""

    PODCAST_DIALOGUE = "podcast_dialogue"
    LATE_NIGHT_STORY = "late_night_story"
    THRILLER_MYSTERY = "thriller_mystery"
    AUDIOBOOK_NARRATION = "audiobook_narration"
    TECH_EXPLAINER = "tech_explainer"
    MOTIVATIONAL_EPIC = "motivational_epic"
