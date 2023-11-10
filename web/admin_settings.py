"""Page: Admin / Manage Settings."""


from st_pages import add_page_title
from utils.layout import auth_required, is_super_admin, organisation_settings_ui, system_settings_ui
from utils.observability import baggage_as_attributes, tracer

with tracer().start_as_current_span("admin_settings_page", attributes=baggage_as_attributes()):
    auth_required(requiring_selected_org_admin=True)

    add_page_title()

    organisation_settings_ui()

    is_super_admin()

    system_settings_ui()
