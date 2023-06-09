"""Configurations for Docq."""

from enum import Enum

ENV_VAR_DOCQ_DATA = "DOCQ_DATA"
ENV_VAR_DOCQ_DEMO = "DOCQ_DEMO"
ENV_VAR_OPENAI_API_KEY = "OPENAI_API_KEY"


class SpaceType(Enum):
    """Space types."""

    PERSONAL = "personal"
    SHARED = "shared"


class FeatureType(Enum):
    """Feature types."""

    ASK_PERSONAL = "Ask Your Documents"
    ASK_SHARED = "Ask Shared Documents"
    CHAT_PRIVATE = "General Chat"


class LogType(Enum):
    """Log types."""

    SYSTEM = "System"
    ACTIVITY = "Activity"


class SystemSettingsKey(Enum):
    """System settings keys."""

    ENABLED_FEATURES = "Enabled Features"
    MODEL_VENDOR = "Model Vendor"


class UserSettingsKey(Enum):
    """User settings keys."""
