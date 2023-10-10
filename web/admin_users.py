"""Page: Admin / Manage Users."""
from st_pages import add_page_title
from utils.layout import auth_required, create_user_ui, list_users_ui, run_page_scripts, setup_page_scripts

setup_page_scripts()
auth_required(requiring_admin=True)

add_page_title()

create_user_ui()
list_users_ui()

run_page_scripts()
