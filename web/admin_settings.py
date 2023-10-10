"""Page: Admin / Manage Settings."""

from st_pages import add_page_title
from utils.layout import auth_required, run_page_scripts, setup_page_scripts, system_settings_ui

setup_page_scripts()

auth_required(requiring_admin=True)

add_page_title()

system_settings_ui()

run_page_scripts()
