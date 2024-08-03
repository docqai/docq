"""Page: Admin / Manage Documents."""
from utils.layout import admin_docs_ui, create_space_ui, tracer

PARAM_NAME = "sid"

@tracer.start_as_current_span("admin_spaces_page")
def admin_spaces_page() -> None:
    """Page: Admin / Manage Spaces."""
    create_space_ui()
    admin_docs_ui(PARAM_NAME)
