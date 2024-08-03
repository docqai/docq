"""Docq widget embed page."""
from docq.config import OrganisationFeatureType
from docq.domain import FeatureKey
from utils.layout import chat_ui, public_session_setup, public_space_enabled
from utils.observability import baggage_as_attributes, tracer
from utils.sessions import get_public_session_id

with tracer().start_as_current_span("widget_embed_page", attributes=baggage_as_attributes()):
  public_session_setup()

  public_space_enabled(OrganisationFeatureType.ASK_PUBLIC)

  feature = FeatureKey(OrganisationFeatureType.ASK_PUBLIC, get_public_session_id())

  chat_ui(feature)
