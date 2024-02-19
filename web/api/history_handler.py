"""Handle /api/chat/history requests."""
from datetime import datetime
from typing import Literal, Self

import docq.run_queries as rq
from docq.domain import FeatureKey, OrganisationFeatureType
from pydantic import ValidationError
from tornado.web import HTTPError

from web.api.base import BaseRequestHandler
from web.api.models import ChatHistoryModel, MessageModel
from web.api.utils import authenticated
from web.utils.streamlit_application import st_app


def _format_chat_message(message: tuple[int, str, bool, datetime, int]) -> MessageModel:
    """Format chat message."""
    return MessageModel(
        id=message[0],
        message=message[1],
        human=message[2],
        timestamp=str(message[3]),
        thread_id=message[4],
    )

@st_app.api_route(r"/api/([^/]+)/history/([^/]+)?")
class ChatHistoryHandler(BaseRequestHandler):
    """Handle /api/<chat|rag>/history<id> requests."""

    __feature: FeatureKey

    @property
    def feature(self: Self) -> FeatureKey:
        """Get the feature key."""
        return self.__feature

    @feature.setter
    def feature(self: Self, mode: Literal["rag", "chat"]) -> None:
        """Set the feature key."""
        if mode not in ["rag", "chat"]:
            raise HTTPError(status_code=400, reason="Invalid mode")

        self.__feature = FeatureKey(OrganisationFeatureType.CHAT_PRIVATE, self.current_user.uid) if mode == "chat" else FeatureKey(OrganisationFeatureType.ASK_SHARED, self.current_user.uid)

    @authenticated
    def get(self: Self, mode: Literal["rag", "chat"], id_: str) -> None:
        """Handle GET request."""
        self.feature = mode

        size = self.get_argument("size", "10")
        try:
            chat_history = rq._retrieve_messages(datetime.now(), int(size), self.feature, int(id_))
            messages = list(map(_format_chat_message, chat_history))
            self.write(ChatHistoryModel(response=messages).model_dump())

        except ValidationError as e:
            raise HTTPError(400, "Invalid page or limit") from e
