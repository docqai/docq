"""Page: Admin / Manage Orgs."""

from utils.layout import create_org_ui, list_orgs_ui, tracer


@tracer.start_as_current_span("admin_orgs_page")
def admin_orgs_page() -> None:
    """Page: Admin / Manage Orgs."""
    create_org_ui()
    list_orgs_ui()
