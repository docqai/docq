"""Page: Admin / Manage Settings."""

import st_components.page_header as st_header
from st_pages import add_page_title
from utils.layout import auth_required, system_settings_ui

st_header._setup_page_script()

auth_required(requiring_admin=True)

add_page_title()

system_settings_ui()

st_header.run_script()
