"""Page: Admin / Manage User Groups."""

from utils.layout import (
  auth_required,
  create_user_group_ui,
  list_user_groups_ui,
  render_page_title_and_favicon,
)
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("admin_user_groups_page", attributes=baggage_as_attributes()):
  # render_page_title_and_favicon()

  create_user_group_ui()
  list_user_groups_ui()
