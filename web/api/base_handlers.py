"""Base request handlers."""
from datetime import datetime
from typing import Any, Literal, Optional, Self

import docq.manage_organisations as m_orgs
import docq.manage_spaces as m_spaces
from docq.config import SpaceType
from docq.domain import FeatureKey, OrganisationFeatureType, SpaceKey
from opentelemetry import trace
from pydantic import ValidationError
from tornado.web import HTTPError, RequestHandler

from web.api.models import SPACE_TYPE, MessageModel, UserModel
from web.utils.handlers import _default_org_id as get_default_org_id

tracer = trace.get_tracer(__name__)


class BaseRequestHandler(RequestHandler):
    """Base request Handler."""

    def check_origin(self: Self, origin: Any) -> bool:
        """Override the origin check if it's causing problems."""
        return True

    def check_xsrf_cookie(self: Self) -> bool:
        """Override the XSRF cookie check."""
        # If `True`, POST, PUT, and DELETE are block unless the `_xsrf` cookie is set.
        # Safe with token based authN
        return False

    __feature: FeatureKey

    @property
    def feature(self: Self) -> FeatureKey:
        """Get the feature key."""
        return self.__feature

    @feature.setter
    def feature(self: Self, mode: Literal["rag", "chat"]) -> None:
        """Set the feature key."""
        if mode not in ["rag", "chat"]:
            raise HTTPError(status_code=404, reason="Not Found")

        self.__feature = (
            FeatureKey(OrganisationFeatureType.CHAT_PRIVATE, self.current_user.uid)
            if mode == "chat"
            else FeatureKey(OrganisationFeatureType.ASK_SHARED, self.current_user.uid)
        )

    def _get_message_object(self: Self, message: tuple[int, str, bool, datetime, int]) -> MessageModel:
        """Format chat message."""
        return MessageModel(
            id=message[0],
            message=message[1],
            human=message[2],
            timestamp=str(message[3]),
            thread_id=message[4],
        )

    @tracer.start_as_current_span("get_current_user")
    def get_current_user(self: Self) -> UserModel:
        """Retrieve user data from token."""
        span = trace.get_current_span()

        auth_header = self.request.headers.get("Authorization")
        if not auth_header:
            error_msg = "Missing Authorization header"
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            span.record_exception(ValueError(error_msg))
            raise HTTPError(401, reason=error_msg, log_message=error_msg)

        scheme, token = auth_header.split(" ")
        if scheme.lower() != "bearer":
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            span.record_exception(ValueError("Authorization scheme must be Bearer"))
            raise HTTPError(401, reason="Authorization scheme must be Bearer")

        try:
            from web.api.utils.auth_utils import decode_jwt

            payload = decode_jwt(token)
            user = UserModel.model_validate(payload.get("data"))
            return user
        except ValidationError as e:
            raise HTTPError(401, reason="Unauthorized: Validation error") from e


class BaseRagRequestHandler(BaseRequestHandler):
    """Base RequestHandler for RAG (Retrieval-Augmented Generation)."""

    __selected_org_id: Optional[int] = None
    __thread_space: Optional[SpaceKey] = None
    __space: Optional[SpaceKey] = None

    def prepare(self: Self) -> None:
        """Prepare the request."""
        self.feature = "rag"

    @property
    def selected_org_id(self: Self) -> int:
        """Get the selected org id."""
        if self.__selected_org_id is None:
            u = self.current_user
            member_orgs = m_orgs.list_organisations(user_id=self.current_user.uid)
            self.__selected_org_id = get_default_org_id(member_orgs, (u.uid, u.fullname, u.super_admin, u.username))
        return self.__selected_org_id

    @property
    def space(self: Self) -> SpaceKey:
        """Get the thread space key."""
        if self.__space is None:
            raise HTTPError(
                401, reason="Thread space not set.", log_message="You must set the thread space before using it."
            )
        return self.__space

    @space.setter
    def space(self: Self, config: tuple[SPACE_TYPE, int]) -> None:
        """Set the space key."""
        if self.selected_org_id is None:
            raise HTTPError(401, "User is not a member of any organisation.")
        space_type, space_id = config

        if space_type not in ["personal", "shared", "public", "thread"]:
            raise HTTPError(400, reason="Bad request", log_message="Invalid space type")

        space_type_ = (
            SpaceType.PERSONAL
            if space_type == "personal"
            else SpaceType.SHARED
            if space_type == "shared"
            else SpaceType.PUBLIC
            if space_type == "public"
            else SpaceType.THREAD
        )

        space = m_spaces.get_space(space_id, self.selected_org_id)
        if space is None:
            raise HTTPError(404, reason="Not Found", log_message="Space not found")

        self.__space = SpaceKey(space_type_, space_id, self.selected_org_id, space[3])

    @property
    def thread_space(self: Self) -> SpaceKey:
        """Get the thread space key."""
        if self.__thread_space is None:
            raise HTTPError(
                401, reason="Thread space not set.", log_message="You must set the thread space before using it."
            )
        return self.__thread_space

    @thread_space.setter
    def thread_space(self: Self, thread_id: int) -> None:
        """Set the thread space key."""
        if self.selected_org_id is None:
            raise HTTPError(401, "User is not a member of any organisation.")

        space = m_spaces.get_thread_space(self.selected_org_id, thread_id)
        if space is None:
            raise HTTPError(404, reason="Not Found", log_message="Thread space not found")

        self.__thread_space = space
