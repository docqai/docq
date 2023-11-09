"""Page: Admin / Manage Documents."""
from st_pages import add_page_title
from utils.layout import admin_docs_ui, auth_required, create_space_ui
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("admin_spaces_page", attributes=baggage_as_attributes()):
  auth_required(requiring_selected_org_admin=True)

  add_page_title()

  PARAM_NAME = "sid"

  ## Create Space UI
  create_space_ui()

  admin_docs_ui(PARAM_NAME)
