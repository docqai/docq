"""Page: Admin / Manage Groups."""

from st_pages import add_page_title
from utils.layout import auth_required, create_group_ui, list_groups_ui

auth_required(requiring_admin=True)

add_page_title()

create_group_ui()
list_groups_ui()
