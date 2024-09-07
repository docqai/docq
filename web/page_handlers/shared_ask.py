"""Page: Shared / Ask Shared Documents."""

from docq.config import OrganisationFeatureType
from docq.domain import FeatureKey
from utils.layout import (
  auth_required,
  chat_ui,
  org_feature_enabled,
  render_page_title_and_favicon,
)
from utils.observability import baggage_as_attributes, tracer
from utils.sessions import get_authenticated_user_id

with tracer().start_as_current_span("ask_shared_page", attributes=baggage_as_attributes()):
    render_page_title_and_favicon()
    auth_required()

    org_feature_enabled(OrganisationFeatureType.ASK_SHARED)
    authenticated_user_id = get_authenticated_user_id()
    if authenticated_user_id is None:
        raise ValueError("User is not authenticated.")

    feature = FeatureKey(OrganisationFeatureType.ASK_SHARED, authenticated_user_id)

    chat_ui(feature)
