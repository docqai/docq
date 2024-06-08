"""Base request handlers."""
from typing import Any, Optional, Self

import docq.manage_organisations as m_orgs
from opentelemetry import trace
from tornado.web import RequestHandler

from web.api.models import UserModel
from web.utils.handlers import _default_org_id as get_default_org_id

tracer = trace.get_tracer(__name__)


class BaseRequestHandler(RequestHandler):
    """Base request Handler."""

    __selected_org_id: Optional[int] = None
    _current_user = None

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

    @property
    def get_current_user(self: Self) -> UserModel | None:
        """(Override) Validate Retrieve and return user data from token."""
        print("get_current_user() called")
        return self._current_user

        # auth_header = self.request.headers.get("Authorization")
        # if not auth_header:
        #     error_msg = "Missing Authorization header"
        #     span.set_status(trace.Status(trace.StatusCode.ERROR))
        #     span.record_exception(ValueError(error_msg))
        #     raise HTTPError(401, reason=error_msg, log_message=error_msg)

        # scheme, token = auth_header.split(" ")
        # if scheme.lower() != "bearer":
        #     span.set_status(trace.Status(trace.StatusCode.ERROR))
        #     span.record_exception(ValueError("Authorization scheme must be Bearer"))
        #     raise HTTPError(401, reason="Authorization scheme must be Bearer")

        # try:
        #     from web.api.utils.auth_utils import decode_jwt

        #     payload = decode_jwt(token)  # validate JWT token
        #     self._current_user = UserModel.model_validate(payload.get("data"))
        #     self._authentication_method = AuthenticationMethod.JWT
        #     # authenticated - JWT decode was successful. And payload json is a valid UserModel.
        #     return self._current_user
        # except Exception as e:
        #     span.set_status(trace.Status(trace.StatusCode.ERROR), "JWT validation error.")
        #     span.record_exception(e)
        #     raise HTTPError(401, reason="Unauthorized: Validation error") from e
