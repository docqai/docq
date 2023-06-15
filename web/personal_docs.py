"""Page: Personal / Manage Your Documents."""

from docq.config import SpaceType
from docq.domain import SpaceKey
from st_pages import add_page_title
from utils.layout import auth_required, documents_ui
from utils.sessions import get_authenticated_user_id

auth_required()

add_page_title()

space = SpaceKey(SpaceType.PERSONAL, get_authenticated_user_id())

documents_ui(space)
