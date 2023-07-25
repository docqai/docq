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
    PUBLIC_SPACE = "Public Space"


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


"""A dictionary of experiment names mapped to their enabled state and description."""
# NOTE: global for now. Later we can adjust to use a different backend to set per user.
EXPERIMENTS = {
    "INCLUDE_EXTRACTED_METADATA": {
        "enabled": False,
        "description": "Include extracts, using LlamaIndex extract modules, in the document index metadata.",
    },
}
