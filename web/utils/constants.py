"""Constants used in the web app."""

from enum import Enum

SESSION_KEY_NAME_DOCQ = "_docq"


class SessionKeySubName(Enum):
    """Second-level names for session keys."""

    CHAT = "chat"
    AUTH = "auth"
    SETTINGS = "settings"
    PUBLIC = "public"


class SessionKeyNameForAuth(Enum):
    """Third-level names for session keys in auth."""

    ID = "id"
    NAME = "name"
    SUPER_ADMIN = "super_admin"
    USERNAME = "username"
    SELECTED_ORG_ID = "selected_org_id"
    SELECTED_ORG_ADMIN = "selected_org_admin"


class SessionKeyNameForSettings(Enum):
    """Third-level names for session keys in settings."""

    SYSTEM = "system"
    USER = "user"


class SessionKeyNameForChat(Enum):
    """Third-level names for session keys in chat."""

    CUTOFF = "cutoff"
    HISTORY = "history"
    THREAD = "thread"


class SessionKeyNameForPublic(Enum):
    """Third-level names for session keys in public."""

    SESSION = "session"
    SPACE_GROUP_ID = "space_group_id"


NUMBER_OF_MSGS_TO_LOAD = 10
MAX_NUMBER_OF_PERSONAL_DOCS = 10

ALLOWED_DOC_EXTS = ["txt", "pdf", "docx", "xlsx", "odt", "ods", "rtf", "csv", "tsv"]
