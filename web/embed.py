"""Docq widget embed page."""
from docq.config import FeatureType
from docq.domain import FeatureKey
from utils.layout import chat_ui, public_session_setup, public_space_enabled
from utils.sessions import get_public_session_id

public_session_setup()

public_space_enabled(FeatureType.ASK_PUBLIC)

feature = FeatureKey(FeatureType.ASK_PUBLIC, get_public_session_id())

chat_ui(feature)
