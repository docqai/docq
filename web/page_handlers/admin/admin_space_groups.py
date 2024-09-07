"""Page: Admin / Manage Space Groups."""

from utils.layout import create_space_group_ui, list_space_groups_ui, tracer


@tracer.start_as_current_span("admin_space_groups_page")
def admin_space_groups_page() -> None:
    """Page: Admin / Manage Space Groups."""
    create_space_group_ui()
    list_space_groups_ui()
