"""Base request handlers."""
from typing import Any, Optional, Self

import docq.manage_organisations as m_orgs
from opentelemetry import trace
from pydantic import ValidationError
from tornado.web import HTTPError, RequestHandler

from web.api.models import UserModel
from web.utils.handlers import _default_org_id as get_default_org_id

tracer = trace.get_tracer(__name__)


class BaseRequestHandler(RequestHandler):
    """Base request Handler."""

    __selected_org_id: Optional[int] = None

    def check_origin(self: Self, origin: Any) -> bool:
        """Override the origin check if it's causing problems."""
        return True

    def check_xsrf_cookie(self: Self) -> bool:
        """Override the XSRF cookie check."""
        # If `True`, POST, PUT, and DELETE are block unless the `_xsrf` cookie is set.
        # Safe with token based authN
        return False

    @property
    def selected_org_id(self: Self) -> int:
        """Get the selected org id."""
        if self.__selected_org_id is None:
            u = self.current_user
            member_orgs = m_orgs.list_organisations(user_id=u.uid)
            self.__selected_org_id = get_default_org_id(member_orgs, (u.uid, u.fullname, u.super_admin, u.username))
        return self.__selected_org_id

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
