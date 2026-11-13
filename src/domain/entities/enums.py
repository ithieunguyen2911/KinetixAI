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
