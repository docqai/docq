"""Page: Personal / General Chat."""

from docq.config import FeatureType
from docq.domain import FeatureKey
from st_pages import add_page_title
from utils.handlers import get_authenticated_user_id
from utils.layout import auth_required, chat_ui

auth_required()

add_page_title()

feature = FeatureKey(FeatureType.CHAT_PRIVATE, get_authenticated_user_id())

chat_ui(feature)
