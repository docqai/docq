"""Page: Personal / General Chat."""

from docq.config import FeatureType
from docq.domain import FeatureKey
from st_components.page_header import create_menu_items
from st_pages import add_page_title
from utils.layout import auth_required, chat_ui, feature_enabled, run_header_script
from utils.sessions import get_authenticated_user_id

auth_required()

feature_enabled(FeatureType.CHAT_PRIVATE)

add_page_title()

feature = FeatureKey(FeatureType.CHAT_PRIVATE, get_authenticated_user_id())

chat_ui(feature)

run_header_script()
create_menu_items()
