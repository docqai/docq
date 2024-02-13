"""Handle /api/chat/history requests."""
from datetime import datetime
from typing import Self

import docq.domain as domain
import docq.run_queries as rq
from pydantic import ValidationError
from tornado.web import HTTPError

from web.api.models import ChatHistoryModel, MessageModel
from web.api.utils import BaseRequestHandler, authenticated
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

@st_app.api_route(r"/api/chat/history/([^/]+)?")
class ChatHistoryHandler(BaseRequestHandler):
    """Handle /api/<chat|rag>/history<id> requests."""


    @property
    def feature(self: Self) -> domain.FeatureKey:
        """Get the feature key."""
        return domain.FeatureKey(domain.OrganisationFeatureType.CHAT_PRIVATE, self.current_user.uid)

    @authenticated
    def get(self: Self, id_: str) -> None:
        """Handle GET request."""
        size = self.get_argument("size", "10")
        try:
            chat_history = rq._retrieve_messages(datetime.now(), int(size), self.feature, int(id_))
            messages = list(map(_format_chat_message, chat_history))
            self.write(ChatHistoryModel(response=messages).model_dump())

        except ValidationError as e:
            raise HTTPError(400, "Invalid page or limit") from e
