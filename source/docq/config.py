"""Configurations for Docq."""

from enum import Enum

ENV_VAR_DOCQ_DATA = "DOCQ_DATA"
ENV_VAR_DOCQ_DEMO = "DOCQ_DEMO"
ENV_VAR_OPENAI_API_KEY = "DOCQ_OPENAI_API_KEY"
ENV_VAR_DOCQ_COOKIE_HMAC_SECRET_KEY = "DOCQ_COOKIE_HMAC_SECRET_KEY"
SESSION_COOKIE_NAME = "docqai/_docq"


class SpaceType(Enum):
    """Space types."""

    PERSONAL = "personal"
    SHARED = "shared"
    PUBLIC = "public"


class FeatureType(Enum):
    """Feature types."""

    ASK_PERSONAL = "Ask Your Documents"
    ASK_SHARED = "Ask Shared Documents"
    ASK_PUBLIC = "Ask Public Documents"
    CHAT_PRIVATE = "General Chat"


class LogType(Enum):
    """Log types."""

    SYSTEM = "System"
    ACTIVITY = "Activity"


class SystemSettingsKey(Enum):
    """System settings keys."""

    # TODO: rename to OrgSettingsKey
    ENABLED_FEATURES = "Enabled Features"
    MODEL_COLLECTION = "Model Collection"


class UserSettingsKey(Enum):
    """User settings keys."""


class ConfigKeyHandlers(Enum):
    """Config key handlers."""
    GET_GDRIVE_CREDENTIAL = "get_gdrive_credential"


class ConfigKeyOptions(Enum):
    """Config key options."""
    GET_GDRIVE_OPTIONS = "get_gdrive_options"


"""A dictionary of experiment names mapped to their enabled state and description."""
# NOTE: global for now. Later we can adjust to use a different backend to set per user.
EXPERIMENTS = {
    "INCLUDE_EXTRACTED_METADATA": {
        "enabled": False,
        "description": "Include extracts, using LlamaIndex extract modules, in the document index metadata.",
    },
    "ASYNC_NODE_PARSER": {
        "enabled": False,
        "description": "Use an async node parser to speed up document parsing.",
    },
}
