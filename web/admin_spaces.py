"""Page: Admin / Manage Documents."""
import st_components.page_header as st_header
from st_pages import add_page_title
from utils.layout import admin_docs_ui, auth_required, create_space_ui

st_header._setup_page_script()
auth_required(requiring_admin=True)

add_page_title()

PARAM_NAME = "sid"

## Create Space UI
create_space_ui()

admin_docs_ui(PARAM_NAME)

st_header.run_script()
