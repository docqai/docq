"""Handle /api/auth requests."""
from typing import Self

import docq.manage_users as m_users
from pydantic import ValidationError
from tornado.web import HTTPError

from web.api.models import UserModel
from web.api.templates import LOGIN_ERROR_TEMPLATE, LOGIN_PAGE_TEMPLATE, LOGIN_SUCCESS_PAGE_TEMPLATE
from web.api.utils import BaseRequestHandler, decode_jwt, encode_jwt
from web.utils.streamlit_application import st_app


def _get_user_dict(result: tuple) -> dict:
    return {
        'uid': result[0],
        'fullname': result[1],
        'super_admin': result[2],
        'username': result[3]
    }


@st_app.api_route("/api/auth/login")
class AuthLoginHandler(BaseRequestHandler):
    """Handle /api/auth/login requests."""

    def login_error(self: Self, reason: str, status: int = 401) -> None:
        """Handle login error."""
        self.set_status(status)
        self.write(LOGIN_ERROR_TEMPLATE.format(reason=reason))
        self.finish()

    def get(self: Self) -> None:
        """Handle GET requests."""
        self.write(LOGIN_PAGE_TEMPLATE)

    def post(self: Self) -> None:
        """Handle POST requests."""
        username = self.get_argument("username", None)
        password = self.get_argument("password", None)

        if not username or not password:
            self.login_error("Username and password are required", 400)

        else:
            try:
                result = m_users.authenticate(username, password)
                if result:
                    try:
                        data = UserModel(**_get_user_dict(result))
                    except ValidationError:
                        self.login_error("Invalid username or password")

                    token = encode_jwt(data)
                    if token:
                        self.set_header("Authorization", f"Bearer {token}")
                        self.write(LOGIN_SUCCESS_PAGE_TEMPLATE)
                else:
                    self.login_error("Invalid username or password")

            except Exception:
                self.login_error("Invalid username or password")


@st_app.api_route('/api/auth/refresh')
class AuthRefreshHandler(BaseRequestHandler):
    """Refresh auth token."""

    def post(self: Self) -> None:
        """Handle POST requests."""
        try:
            token = self.get_argument("token")
        except Exception as e:
            raise HTTPError(400, reason="Token is required") from e

        try:
            data = decode_jwt(token, check_expired=False)
        except Exception as e:
            raise HTTPError(401, reason="Unauthorized: Token is invalid") from e

        token = encode_jwt(UserModel.model_validate(data.get("data")))
        if token:
            self.set_header("Authorization", f"Bearer {token}")
        else:
            raise HTTPError(401, reason="Unauthorized: Token is invalid")
