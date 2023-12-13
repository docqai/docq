"""Page: Shared / List Shared Spaces."""

from docq.config import OrganisationFeatureType
from docq.domain import FeatureKey
from utils.layout import (
    auth_required,
    list_spaces_ui,
    org_feature_enabled,
    render_page_title_and_favicon,
)
from utils.observability import baggage_as_attributes, tracer
from utils.sessions import get_authenticated_user_id

with tracer().start_as_current_span("shared_spaces_page", attributes=baggage_as_attributes()):
    render_page_title_and_favicon()
    auth_required()

    org_feature_enabled(OrganisationFeatureType.ASK_SHARED)

    feature = FeatureKey(OrganisationFeatureType.ASK_SHARED, get_authenticated_user_id()) # type: ignore

    list_spaces_ui()
