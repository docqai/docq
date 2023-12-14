"""Page: Admin / Manage User Groups."""

from utils.layout import create_user_group_ui, list_user_groups_ui, tracer


@tracer.start_as_current_span("admin_user_groups_page")
def admin_user_groups_page() -> None:
    """Page: Admin / Manage User Groups."""
    create_user_group_ui()
    list_user_groups_ui()
