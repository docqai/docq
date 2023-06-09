"""Page: Admin / Manage Settings."""

from st_pages import add_page_title
from utils.layout import auth_required, system_settings_ui

auth_required(requiring_admin=True)

add_page_title()

system_settings_ui()
