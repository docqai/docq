"""Page: Admin / Manage Engagements."""

from st_pages import add_page_title
from utils.layout import auth_required, create_engagement_ui, list_engagements_ui

auth_required(requiring_admin=True)

add_page_title()

create_engagement_ui()
list_engagements_ui()
