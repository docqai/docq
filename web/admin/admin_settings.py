"""Page: Admin / Manage Settings."""


from utils.layout import is_super_admin, organisation_settings_ui, system_settings_ui, tracer


@tracer.start_as_current_span("admin_settings_page")
def admin_settings_page() -> None:
    """Page: Admin / Manage Settings."""
    organisation_settings_ui()
    is_super_admin()
    system_settings_ui()
