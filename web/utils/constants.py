"""Constants used in the web app."""

from enum import Enum

SESSION_KEY_NAME_DOCQ = "_docq"

SESSION_KEY_NAME_ERROR_STATE = "_docq_error_state"

SESSION_KEY_NAME_FORM_VALIDATION_STATE = "_docq_form_validation_state"


class SessionKeySubName(Enum):
    """Second-level names for session keys."""

    CHAT = "chat"
    AUTH = "auth"
    SETTINGS = "settings"


class SessionKeyNameForAuth(Enum):
    """Third-level names for session keys in auth."""

    ID = "id"
    NAME = "name"
    SUPER_ADMIN = "super_admin"
    USERNAME = "username"
    SELECTED_ORG_ID = "selected_org_id"
    SELECTED_ORG_ADMIN = "selected_org_admin"
    PUBLIC_SESSION_ID = "public_session_id"
    PUBLIC_SPACE_GROUP_ID = "public_space_group_id"
    ANONYMOUS = "anonymous"


class SessionKeyNameForSettings(Enum):
    """Third-level names for session keys in settings."""
    ORG = "org"
    SYSTEM = "system"
    USER = "user"


class SessionKeyNameForChat(Enum):
    """Third-level names for session keys in chat."""

    CUTOFF = "cutoff"
    HISTORY = "history"
    THREAD = "thread"


NUMBER_OF_MSGS_TO_LOAD = 10
MAX_NUMBER_OF_UPLOAD_DOCS = 10

ALLOWED_DOC_EXTS = ["txt", "pdf", "docx", "xlsx", "odt", "ods", "rtf", "csv", "tsv"]
