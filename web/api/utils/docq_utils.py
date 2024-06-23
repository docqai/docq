""""Utils to interact with Docq backend service."""
from datetime import datetime

import docq.manage_spaces as m_spaces
from docq.config import OrganisationFeatureType, SpaceType
from docq.domain import FeatureKey, SpaceKey
from tornado.web import HTTPError

from web.api.models import FEATURE, MessageModel


def get_feature_key(user_id: int, feature: FEATURE = "rag") -> FeatureKey:
    """Get organisation feature key."""
    return (
        FeatureKey(OrganisationFeatureType.CHAT_PRIVATE, user_id)
        if feature == "chat"
        else FeatureKey(OrganisationFeatureType.ASK_SHARED, user_id)
    )


def get_space(org_id: int, space_id: int) -> SpaceKey:
    """Get space key from space id and space type."""
    space = m_spaces.get_space(space_id, org_id)
    if space is None:
        raise HTTPError(404, reason="Not Found", log_message="Space not found")
    return SpaceKey(SpaceType[space[7]], space_id, org_id, space[3])


def get_thread_space(org_id: int, thread_id: int) -> SpaceKey:
    """Get thread space key from org_id and thread_id."""
    space = m_spaces.get_thread_space(org_id, thread_id)

    if space is None:
        raise HTTPError(404, reason="Not Found", log_message="Space not found")
    return space


def get_message_object(message: tuple[int, str, bool, datetime, int]) -> MessageModel:
    """Format chat message."""
    return MessageModel(
        **{
            "id": message[0],
            "content": message[1],
            "human": message[2],
            "timestamp": str(message[3]),
            "thread_id": message[4],
        }
    )
