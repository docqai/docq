"""Page: Personal / Manage Your Documents."""

from docq.config import SpaceType
from docq.domain import SpaceKey
from st_pages import add_page_title
from utils.handlers import get_authenticated_user_id
from utils.layout import auth_required, documents_ui

auth_required()

add_page_title()

space = SpaceKey(SpaceType.PERSONAL, get_authenticated_user_id())

documents_ui(space)
