"""Docq widget embed page."""
from docq.config import FeatureType
from docq.domain import FeatureKey
from utils.layout import auth_required, chat_ui, public_space_enabled
from utils.sessions import get_authenticated_user_id

public_space_enabled(FeatureType.ASK_SHARED)

auth_required(show_login_form=False, show_logout_button=False)

feature = FeatureKey(FeatureType.ASK_SHARED, get_authenticated_user_id())

chat_ui(feature)
