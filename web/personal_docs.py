"""Page: Personal / Manage Your Documents."""
from docq.config import FeatureType, SpaceType
from docq.domain import SpaceKey
from st_pages import add_page_title
from utils.layout import auth_required, documents_ui, feature_enabled, run_page_scripts, setup_page_scripts
from utils.sessions import get_authenticated_user_id, get_selected_org_id

setup_page_scripts()
auth_required()

feature_enabled(FeatureType.ASK_PERSONAL)

add_page_title()

space = SpaceKey(SpaceType.PERSONAL, get_authenticated_user_id(), get_selected_org_id())

documents_ui(space)

run_page_scripts()
