"""Page: Personal / Manage Your Documents."""
import st_components.page_header as st_header
from docq.config import FeatureType, SpaceType
from docq.domain import SpaceKey
from st_pages import add_page_title
from utils.layout import auth_required, documents_ui, feature_enabled
from utils.sessions import get_authenticated_user_id, get_selected_org_id

st_header._setup_page_script()
auth_required()

feature_enabled(FeatureType.ASK_PERSONAL)

add_page_title()

space = SpaceKey(SpaceType.PERSONAL, get_authenticated_user_id(), get_selected_org_id())

documents_ui(space)

st_header.run_script()
