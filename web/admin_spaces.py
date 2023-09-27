"""Page: Admin / Manage Documents."""
from st_pages import add_page_title
from utils.layout import admin_docs_ui, auth_required, create_space_ui

auth_required(requiring_admin=True)

add_page_title()

PARAM_NAME = "sid"

## Create Space UI
create_space_ui()

admin_docs_ui(PARAM_NAME)
