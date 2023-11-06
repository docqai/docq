"""Page: Admin / Manage Space Groups."""

from st_pages import add_page_title
from utils.layout import (
    auth_required,
    create_space_group_ui,
    list_space_groups_ui,
    run_page_scripts,
    setup_page_scripts,
)

setup_page_scripts()
auth_required(requiring_admin=True)

add_page_title()

create_space_group_ui()
list_space_groups_ui()

run_page_scripts()
