"""Page: Admin / Manage Orgs."""

from utils.layout import (
    create_org_ui,
    list_orgs_ui,
    render_page_title_and_favicon,
)
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("admin_orgs_page", attributes=baggage_as_attributes()):
    # render_page_title_and_favicon()

    create_org_ui()
    list_orgs_ui()
