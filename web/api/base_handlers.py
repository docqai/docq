"""Base request handlers."""
from typing import Any, Optional, Self

import docq.manage_organisations as m_orgs
import docq.manage_spaces as m_spaces
from docq.domain import FeatureKey, OrganisationFeatureType, SpaceKey
from opentelemetry import trace
from pydantic import ValidationError
from tornado.web import HTTPError, RequestHandler

from web.api.models import UserModel
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

    def _get_message_object(self: Self,result: tuple) -> dict:
        return {
            'id': result[0],
            'message': result[1],
            'human': result[2],
            'timestamp': str(result[3]),
            'thread_id': result[4]
        }

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

    @property
    def selected_org_id(self: Self) -> int:
        """Get the selected org id."""
        if self.__selected_org_id is None:
            u = self.current_user
            member_orgs = m_orgs.list_organisations(user_id=self.current_user.uid)
            self.__selected_org_id = get_default_org_id(member_orgs, (u.uid, u.fullname, u.super_admin, u.username))
        return self.__selected_org_id

    @property
    def feature(self: Self) -> FeatureKey:
        """Get the feature key."""
        return FeatureKey(OrganisationFeatureType.ASK_SHARED, self.current_user.uid)

    @property
    def space(self: Self) -> SpaceKey:
        """Get the space key."""
        if self.selected_org_id is None:
            raise HTTPError(401, "User is not a member of any organisation.")
        thread_id = self.get_body_argument("thread_id", None)
        if thread_id is None:
            thread_id = self.get_argument("thread_id")
        space = m_spaces.get_thread_space(self.selected_org_id, int(thread_id))
        if space is None:
            raise HTTPError(404, reason="Space Not found")
        return space
