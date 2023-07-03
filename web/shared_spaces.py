"""Page: Shared / List Shared Spaces."""

from docq.config import FeatureType
from docq.domain import FeatureKey
from st_pages import add_page_title
from utils.layout import auth_required, feature_enabled, list_spaces_ui
from utils.sessions import get_authenticated_user_id

auth_required()

feature_enabled(FeatureType.ASK_SHARED)

add_page_title()

feature = FeatureKey(FeatureType.ASK_SHARED, get_authenticated_user_id())

list_spaces_ui()
