"""Page: Shared / List Shared Spaces."""

import st_components.page_header as st_header
from docq.config import FeatureType
from docq.domain import FeatureKey
from st_pages import add_page_title
from utils.layout import auth_required, feature_enabled, list_spaces_ui
from utils.sessions import get_authenticated_user_id

st_header._setup_page_script()
auth_required()

feature_enabled(FeatureType.ASK_SHARED)

add_page_title()

feature = FeatureKey(FeatureType.ASK_SHARED, get_authenticated_user_id())

list_spaces_ui()

st_header.run_script()
