"""Page: Admin / Manage Settings."""


from utils.layout import (
    auth_required,
    is_super_admin,
    organisation_settings_ui,
    render_page_title_and_favicon,
    system_settings_ui,
)
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("admin_settings_page", attributes=baggage_as_attributes()):
    render_page_title_and_favicon()
    auth_required(requiring_selected_org_admin=True)

    organisation_settings_ui()

    is_super_admin()

    system_settings_ui()
