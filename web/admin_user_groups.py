"""Page: Admin / Manage User Groups."""

from st_pages import add_page_title
from utils.layout import auth_required, create_user_group_ui, list_user_groups_ui
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("admin_user_groups_page", attributes=baggage_as_attributes()):
  auth_required(requiring_selected_org_admin=True)

  add_page_title()

  create_user_group_ui()
  list_user_groups_ui()
