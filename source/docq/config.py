"""Configurations for Docq."""

from enum import Enum

ENV_VAR_DOCQ_DATA = "DOCQ_DATA"
ENV_VAR_DOCQ_DEMO = "DOCQ_DEMO"
ENV_VAR_OPENAI_API_KEY = "DOCQ_OPENAI_API_KEY"
ENV_VAR_DOCQ_COOKIE_HMAC_SECRET_KEY = "DOCQ_COOKIE_HMAC_SECRET_KEY"
ENV_VAR_DOCQ_API_SECRET = "DOCQ_API_SECRET"
SESSION_COOKIE_NAME = "docqai/_docq"
ENV_VAR_DOCQ_GROQ_API_KEY = "DOCQ_GROQ_API_KEY"

ENV_VAR_DOCQ_SLACK_CLIENT_ID = "DOCQ_SLACK_CLIENT_ID"
ENV_VAR_DOCQ_SLACK_CLIENT_SECRET = "DOCQ_SLACK_CLIENT_SECRET"  # noqa: S105
ENV_VAR_DOCQ_SLACK_SIGNING_SECRET = "DOCQ_SLACK_SIGNING_SECRET"  # noqa: S105


class SpaceType(Enum):
    """Space types. These reflect scope of data access."""

    PERSONAL = "personal"
    SHARED = "shared"
    PUBLIC = "public"
    THREAD = "thread"


class SystemFeatureType(Enum):
    """System level feature types."""

    FREE_USER_SIGNUP = "Free User Signup"


class OrganisationFeatureType(Enum):
    """Organisation level feature types."""

    ASK_SHARED = "Ask Shared Documents"
    ASK_PUBLIC = "Ask Public Documents"
    CHAT_PRIVATE = "General Chat"


class LogType(Enum):
    """Audit log types."""

    SYSTEM = "System"
    ACTIVITY = "Activity"


class SystemSettingsKey(Enum):
    """System level settings keys."""

    ENABLED_FEATURES = "Enabled Features"


class OrganisationSettingsKey(Enum):
    """Organisation level settings keys."""

    ENABLED_FEATURES = "Enabled Features"
    MODEL_COLLECTION = "Model Collection"

class UserSettingsKey(Enum):
    """User settings keys."""


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
