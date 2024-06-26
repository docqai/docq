"""Token handler endpoint for the API. /api/token handler."""

from typing import Literal, Optional, Self

import docq.manage_users as m_users
from opentelemetry import trace
from pydantic import BaseModel, ValidationError
from tornado.web import HTTPError

from web.api.base_handlers import BaseRequestHandler
from web.api.models import UserModel
from web.api.utils.auth_utils import decode_jwt, encode_jwt
from web.utils.streamlit_application import st_app

tracer = trace.get_tracer(__name__)


def _get_user_dict(result: tuple) -> dict:
    return {"uid": result[0], "fullname": result[1], "super_admin": result[2], "username": result[3]}


class TokenRequestModel(BaseModel):
    """Token request model."""

    grant_type: Literal["authorization_code", "refresh_token"] = "authorization_code"
    code: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None
    refresh_token: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class TokenValidationRequestModel(BaseModel):
    """Token validation request model."""

    token: str


class TokenResponseModel(BaseModel):
    """Token response model."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


@tracer.start_as_current_span(name="TokenHandler")
@st_app.api_route("/api/v1/token")
class TokenHandler(BaseRequestHandler):
    """Token handler endpoint for the API. /api/token handler. verify the username and password then return a token."""

    def post(self: Self) -> None:
        """Handle POST requests."""
        try:
            request = TokenRequestModel.model_validate_json(self.request.body)
        except ValidationError as e:
            raise HTTPError(400, reason="Bad request", log_message=str(e)) from e

        if request.grant_type == "authorization_code":

            if not request.username or not request.password:
                raise HTTPError(400, reason="Bad request", log_message="Username and password are required")

            result = m_users.authenticate(request.username, request.password)
            if not result:
                raise HTTPError(401, reason="Unauthorized", log_message="Invalid username or password")

            user = UserModel(**_get_user_dict(result))
            token = encode_jwt(user)
            if not token:
                raise HTTPError(500, reason="Internal server error", log_message="Failed to generate token")

            # FIXME: refresh token should be a separate token with a longer expiration.
            response = TokenResponseModel(access_token=token, expires_in=3600, refresh_token=token).model_dump_json()
            self.write(response)

        elif request.grant_type == "refresh_token":
            if not request.refresh_token:
                raise HTTPError(400, reason="Bad request", log_message="Refresh token is required")

            user = decode_jwt(request.refresh_token, check_expired=False) # FIXME: this refresh token should also have a expiration
            if not user:
                raise HTTPError(401, reason="Unauthorized", log_message="Invalid refresh token")

            token = encode_jwt(UserModel.model_validate(user.get("data")))
            if not token:
                raise HTTPError(500, reason="Internal server error", log_message="Failed to generate token")

            response = TokenResponseModel(access_token=token, expires_in=3600, refresh_token=token).json()
            self.write(response)

        else:
            raise HTTPError(400, reason="Bad request", log_message="Invalid grant type")

@tracer.start_as_current_span(name="TokenValidationHandler")
@st_app.api_route("/api/v1/token/validate")
class TokenValidationHandler(BaseRequestHandler):
    """Token validation handler endpoint for the API. /api/token/validate handler. Check if the token sent is valid + unexpired."""

    def post(self: Self) -> None:
        """Handle GET requests."""
        try:
            request = TokenValidationRequestModel.model_validate_json(self.request.body)
            user = decode_jwt(request.token, check_expired=True)
            if not user:
                raise HTTPError(401, reason="Unauthorized", log_message="Invalid token")

            self.write("OK")
        except ValidationError as e:
            raise HTTPError(400, reason="Bad request") from e

@tracer.start_as_current_span(name="TokenRefreshHandler")
@st_app.api_route("/api/v1/token/refresh")
class TokenRefreshHandler(BaseRequestHandler):
    """Token refresh handler endpoint for the API. /api/token/refresh handler. Given a valid unexpired token, return a new token.

    TODO: implement separate refresh token functionality. check the token was originally issued to the same user requesting the refresh.
    """

    def post(self: Self) -> None:
        """Handle POST requests."""
        try:
            request = TokenValidationRequestModel.model_validate_json(self.request.body)
            user = decode_jwt(request.token, check_expired=True)
            if not user:
                raise HTTPError(401, reason="Unauthorized", log_message="Invalid token")

            token = encode_jwt(UserModel.model_validate(user.get("data")))
            if not token:
                raise HTTPError(500, reason="Internal server error", log_message="Failed to generate token")

            response = TokenResponseModel(access_token=token, expires_in=3600, refresh_token=token).model_dump_json()
            self.write(response)
        except ValidationError as e:
            raise HTTPError(400, reason="Bad request") from e
