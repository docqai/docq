"""Page: Shared / List Shared Spaces."""

from docq.config import OrganisationFeatureType
from docq.domain import FeatureKey
from st_pages import add_page_title
from utils.layout import auth_required, list_spaces_ui, org_feature_enabled
from utils.observability import baggage_as_attributes, tracer
from utils.sessions import get_authenticated_user_id

with tracer().start_as_current_span("shared_spaces_page", attributes=baggage_as_attributes()):
    auth_required()

    org_feature_enabled(OrganisationFeatureType.ASK_SHARED)

    add_page_title()

    feature = FeatureKey(OrganisationFeatureType.ASK_SHARED, get_authenticated_user_id())

    list_spaces_ui()
