"""Page: Admin / Manage Settings."""


from utils.layout import __not_authorised, organisation_settings_ui, system_settings_ui, tracer

from ...utils.sessions import is_current_user_super_admin


@tracer.start_as_current_span("admin_settings_page")
def admin_settings_page() -> None:
    """Page: Admin / Manage Settings."""
    organisation_settings_ui()
    # if is_super_admin():
    if is_current_user_super_admin():
        system_settings_ui()
    else:
        __not_authorised()
