"""Page: Personal / Ask Your Documents."""
import st_components.page_header as st_header
from docq.config import FeatureType
from docq.domain import FeatureKey
from st_pages import add_page_title
from utils.layout import auth_required, chat_ui, feature_enabled, header_ui
from utils.sessions import get_authenticated_user_id

st_header._setup_page_script()
auth_required()

feature_enabled(FeatureType.ASK_PERSONAL)

add_page_title()

feature = FeatureKey(FeatureType.ASK_PERSONAL, get_authenticated_user_id())

chat_ui(feature)

st_header.run_script()
