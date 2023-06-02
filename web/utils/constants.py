"""Constants used in the web app."""

from enum import Enum

SESSION_KEY_NAME_DOCQ = "_docq"


class SessionKeySubName(Enum):
    """Second-level names for session keys."""

    AUTH = "auth"


class SessionKeyNameForAuth(Enum):
    """Third-level names for session keys in auth."""

    ID = "id"
    NAME = "name"
    ADMIN = "admin"


class SessionKeyNameForChat(Enum):
    """Third-level names for session keys in chat."""

    CUTOFF = "cutoff"
    HISTORY = "history"


NUMBER_OF_MSGS_TO_LOAD = 10
MAX_NUMBER_OF_PERSONAL_DOCS = 10

ALLOWED_DOC_EXTS = ["txt", "pdf", "docx", "xlsx", "odt", "ods", "rtf", "csv", "tsv"]
