"""Page: Personal / General Chat."""

from docq.config import FeatureType
from docq.domain import FeatureKey
from st_pages import add_page_title
from utils.layout import auth_required, chat_ui
from utils.sessions import get_authenticated_user_id

auth_required()

add_page_title()

feature = FeatureKey(FeatureType.CHAT_PRIVATE, get_authenticated_user_id())

chat_ui(feature)