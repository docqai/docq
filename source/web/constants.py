from enum import Enum

SESSION_KEY_NAME_DOCQ = '_docq'

NUMBER_OF_MSGS_TO_LOAD = 10
MAX_NUMBER_OF_DOCS = 5
ALLOWED_DOC_EXTS = ['txt', 'pdf', 'docx', 'xlsx']


class SessionKeyName(Enum):
    CUTOFF = 'cutoff'
    HISTORY = 'history'


class SpaceType(Enum):
    PERSONAL = 'personal'
    SHARED = 'shared'
