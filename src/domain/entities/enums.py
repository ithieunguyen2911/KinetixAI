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
    COMPLETED = "completed"
    FAILED = "failed"
