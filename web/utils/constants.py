"""Constants used in the web app."""

from enum import Enum

SESSION_KEY_NAME_DOCQ = "_docq"


class SessionKeySubName(Enum):
    """Second-level names for session keys."""

    CHAT = "chat"
    AUTH = "auth"
    SETTINGS = "settings"


class SessionKeyNameForAuth(Enum):
    """Third-level names for session keys in auth."""

    ID = "id"
    NAME = "name"
    ADMIN = "admin"
    USERNAME = "username"
    ORG_ID = "org_id"


class SessionKeyNameForSettings(Enum):
    """Third-level names for session keys in settings."""

    SYSTEM = "system"
    USER = "user"


class SessionKeyNameForChat(Enum):
    """Third-level names for session keys in chat."""

    CUTOFF = "cutoff"
    HISTORY = "history"
    THREAD = "thread"


NUMBER_OF_MSGS_TO_LOAD = 10
MAX_NUMBER_OF_PERSONAL_DOCS = 10

ALLOWED_DOC_EXTS = ["txt", "pdf", "docx", "xlsx", "odt", "ods", "rtf", "csv", "tsv"]
