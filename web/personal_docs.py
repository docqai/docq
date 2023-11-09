"""Page: Personal / Manage Your Documents."""

from docq.config import OrganisationFeatureType, SpaceType
from docq.domain import SpaceKey
from st_pages import add_page_title
from utils.layout import auth_required, documents_ui, org_feature_enabled
from utils.observability import baggage_as_attributes, tracer
from utils.sessions import get_authenticated_user_id, get_selected_org_id

with tracer().start_as_current_span("personal_docs_page", attributes=baggage_as_attributes()):
  auth_required()

  org_feature_enabled(OrganisationFeatureType.ASK_PERSONAL)

  add_page_title()

  space = SpaceKey(SpaceType.PERSONAL, get_authenticated_user_id(), get_selected_org_id())

  documents_ui(space)
