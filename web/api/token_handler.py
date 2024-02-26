"""Token handler endpoint for the API. /api/token handler."""

from typing import Literal, Optional, Self

import docq.manage_users as m_users
from pydantic import BaseModel, ValidationError
from tornado.web import HTTPError

from web.api.base_handlers import BaseRequestHandler
from web.api.models import UserModel
from web.api.utils.auth_utils import decode_jwt, encode_jwt
from web.utils.streamlit_application import st_app


def _get_user_dict(result: tuple) -> dict:
    return {"uid": result[0], "fullname": result[1], "super_admin": result[2], "username": result[3]}


class TokenRequestModel(BaseModel):
    """Token request model."""

    grant_type: Literal["authorization_code", "refresh_token"] = "authorization_code"
    code: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: str
    refresh_token: Optional[str] = None


class TokenResponseModel(BaseModel):
    """Token response model."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


@st_app.api_route("/api/v1/token")
class TokenHandler(BaseRequestHandler):
    """Token handler endpoint for the API. /api/token handler."""

    def post(self: Self) -> None:
        """Handle POST requests."""
        try:
            data = TokenRequestModel.model_validate_json(self.request.body)
        except ValidationError as e:
            raise HTTPError(400, reason="Bad request", log_message=str(e)) from e

        if data.grant_type == "authorization_code":
            username = self.get_argument("username", None)
            password = self.get_argument("password", None)

            if not username or not password:
                raise HTTPError(400, reason="Bad request", log_message="Username and password are required")

            result = m_users.authenticate(username, password)
            if not result:
                raise HTTPError(401, reason="Unauthorized", log_message="Invalid username or password")

            user = UserModel(**_get_user_dict(result))
            token = encode_jwt(user)
            if not token:
                raise HTTPError(500, reason="Internal server error", log_message="Failed to generate token")

            # TODO: Setup refresh token
            response = TokenResponseModel(access_token=token, expires_in=3600, refresh_token=token).model_dump_json()
            self.write(response)

        elif data.grant_type == "refresh_token":
            if not data.refresh_token:
                raise HTTPError(400, reason="Bad request", log_message="Refresh token is required")

            user = decode_jwt(data.refresh_token, check_expired=False)
            if not user:
                raise HTTPError(401, reason="Unauthorized", log_message="Invalid refresh token")

            token = encode_jwt(UserModel.model_validate(user.get("data")))
            if not token:
                raise HTTPError(500, reason="Internal server error", log_message="Failed to generate token")

            response = TokenResponseModel(access_token=token, expires_in=3600, refresh_token=token).json()
            self.write(response)

        else:
            raise HTTPError(400, reason="Bad request", log_message="Invalid grant type")
