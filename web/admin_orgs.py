"""Page: Admin / Manage Orgs."""

from st_pages import add_page_title
from utils.layout import auth_required, create_org_ui, list_orgs_ui

auth_required(requiring_admin=True)

add_page_title()

create_org_ui()
list_orgs_ui()
