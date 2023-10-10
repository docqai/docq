"""Docq widget embed page."""
from docq.config import FeatureType
from docq.domain import FeatureKey
from utils.layout import chat_ui, public_session_setup, public_space_enabled, setup_page_scripts
from utils.sessions import get_public_session_id

setup_page_scripts()
public_session_setup()

public_space_enabled(FeatureType.ASK_PUBLIC)

feature = FeatureKey(FeatureType.ASK_PUBLIC, get_public_session_id())

chat_ui(feature)
