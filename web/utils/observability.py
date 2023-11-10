"""Observability utilities."""
import docq
from opentelemetry import baggage, trace


def tracer() -> trace.Tracer:
    """Get the tracer."""
    return trace.get_tracer(__name__, docq.__version_str__)


def baggage_as_attributes() -> dict[str, str]:
    """Get the baggage."""
    return {
        "auth.selected_org_id": str(baggage.get_baggage("current_user_id")),
        "auth.selected_org_admin": str(baggage.get_baggage("selected_org_id")),
        "auth.user_id": str(baggage.get_baggage("selected_org_admin")),
        "auth.username": str(baggage.get_baggage("username")),
    }
