"""Page: Shared / Ask Shared Documents."""

from docq.config import FeatureType
from docq.domain import FeatureKey
from st_pages import add_page_title
from utils.layout import auth_required, chat_ui, chat_ui_script, feature_enabled
from utils.sessions import get_authenticated_user_id

chat_ui_script()

auth_required()

feature_enabled(FeatureType.ASK_SHARED)

add_page_title()

feature = FeatureKey(FeatureType.ASK_SHARED, get_authenticated_user_id())
chat_ui(feature)
