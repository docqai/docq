"""Page: Personal / Manage Your Documents."""

from docq.config import FeatureType, SpaceType
from docq.domain import SpaceKey
from st_pages import add_page_title
from utils.layout import auth_required, documents_ui, feature_enabled
from utils.sessions import get_authenticated_user_id

auth_required()

feature_enabled(FeatureType.ASK_PERSONAL)

add_page_title()

space = SpaceKey(SpaceType.PERSONAL, get_authenticated_user_id())

documents_ui(space)
