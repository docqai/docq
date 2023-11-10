"""Page: Personal / General Chat."""

from docq.config import OrganisationFeatureType
from docq.domain import FeatureKey
from st_pages import add_page_title
from utils.layout import auth_required, chat_ui, org_feature_enabled
from utils.observability import baggage_as_attributes, tracer
from utils.sessions import get_authenticated_user_id

with tracer().start_as_current_span("personal_chat_page", attributes=baggage_as_attributes()):
  auth_required()

  org_feature_enabled(OrganisationFeatureType.CHAT_PRIVATE)

  add_page_title()

  feature = FeatureKey(OrganisationFeatureType.CHAT_PRIVATE, get_authenticated_user_id())

  chat_ui(feature)
