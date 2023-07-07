"""Page: Admin / Manage Spaces."""

from st_pages import add_page_title
from utils.layout import auth_required, create_space_ui, list_spaces_ui

auth_required(requiring_admin=True)

add_page_title()

create_space_ui()
list_spaces_ui(True)
