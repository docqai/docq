"""Page: Admin / Manage Documents."""
from utils.layout import (
  admin_docs_ui,
  auth_required,
  create_space_ui,
  render_page_title_and_favicon,
)
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("admin_spaces_page", attributes=baggage_as_attributes()):
  # render_page_title_and_favicon()

  PARAM_NAME = "sid"

  ## Create Space UI
  create_space_ui()

  admin_docs_ui(PARAM_NAME)
