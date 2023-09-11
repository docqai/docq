"""Docq widget embed page."""
from docq.config import FeatureType
from docq.domain import FeatureKey
from utils.layout import auth_required, chat_ui, public_space_enabled
from utils.sessions import get_public_session_id

auth_required(show_login_form=False, show_logout_button=False)

public_space_enabled(FeatureType.ASK_PUBLIC)

feature = FeatureKey(FeatureType.ASK_PUBLIC, get_public_session_id())

chat_ui(feature)
