"""Configurations for Docq."""

from enum import Enum

ENV_VAR_DOCQ_DATA = "DOCQ_DATA"
ENV_VAR_DOCQ_DEMO = "DOCQ_DEMO"
ENV_VAR_OPENAI_API_KEY = "OPENAI_API_KEY"


class DocumentMetadata(Enum):
    """Document metadata."""

    FILE_PATH = "file_path"
    SPACE_ID = "space_id"
    SPACE_TYPE = "space_type"


class SpaceType(Enum):
    """Space types."""

    PERSONAL = "personal"
    SHARED = "shared"


class FeatureType(Enum):
    """Feature types."""

    ASK_PERSONAL = "ask_personal"
    ASK_SHARED = "ask_shared"
    CHAT_PRIVATE = "chat_private"


class LogType(Enum):
    """Log types."""

    SYSTEM = "system"
    ACTIVITY = "activity"
