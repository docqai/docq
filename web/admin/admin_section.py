"""Admin Section."""

from utils.layout import admin_section_ui, auth_required, render_page_title_and_favicon
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("admin_section", attributes=baggage_as_attributes()):
    # render_page_title_and_favicon()

    admin_section_ui()
