"""Page: Admin / Manage Space Groups."""

from st_pages import add_page_title
from utils.layout import auth_required, create_space_group_ui, list_space_groups_ui
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("admin_space_groups_page", attributes=baggage_as_attributes()):
  auth_required(requiring_selected_org_admin=True)

  add_page_title()

  create_space_group_ui()
  list_space_groups_ui()
