"""Token handler endpoint for the API. /api/token handler."""

from typing import Literal, Optional, Self

import docq.manage_users as m_users
from pydantic import BaseModel, ValidationError

from web.api.models import UserModel
from web.api.utils import BaseRequestHandler, decode_jwt, encode_jwt
from web.utils.streamlit_application import st_app


def _get_user_dict(result: tuple) -> dict:
    return {
        'uid': result[0],
        'fullname': result[1],
        'super_admin': result[2],
        'username': result[3]
    }


class TokenRequestModel(BaseModel):
    """Token request model."""
    grant_type: Literal['authorization_code', 'refresh_token'] = 'authorization_code'
    code: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: str
    refresh_token: Optional[str] = None

class TokenResponseModel(BaseModel):
    """Token response model."""
    access_token: str
    token_type: Literal['bearer'] = 'bearer'
    expires_in: int
    refresh_token: Optional[str] = None

class TokenErrorResponseModel(BaseModel):
    """Token error response model."""
    error: str
    error_description: str


@st_app.api_route("/api/token")
class TokenHandler(BaseRequestHandler):
    """Token handler endpoint for the API. /api/token handler."""

    def token_error(self: Self, reason: str, status: int = 400) -> None:
        """Handle token error."""
        self.set_status(status)
        self.write(TokenErrorResponseModel(error='invalid_request', error_description=reason).json())
        self.finish()

    def post(self: Self) -> None:
        """Handle POST requests."""
        try:
            data = TokenRequestModel.model_validate_json(self.request.body)
        except ValidationError as e:
            self.token_error(str(e))
            return

        if data.grant_type == 'authorization_code':
            username = self.get_argument("username", None)
            password = self.get_argument("password", None)

            if not username or not password:
                self.token_error("Username and password are required", 400)
                return

            result = m_users.authenticate(username, password)
            if not result:
                self.token_error("Invalid username or password")
                return

            user = UserModel(**_get_user_dict(result))
            token = encode_jwt(user)
            if not token:
                self.token_error("Failed to generate token")
                return

            # TODO: Setup refresh token
            response = TokenResponseModel(access_token=token, expires_in=3600, refresh_token=token).model_dump_json()
            self.write(response)

        elif data.grant_type == 'refresh_token':
            if not data.refresh_token:
                self.token_error("Refresh token is required", 400)
                return

            user = decode_jwt(data.refresh_token, check_expired=False)
            if not user:
                self.token_error("Invalid refresh token")
                return

            token = encode_jwt(UserModel.model_validate(user.get("data")))
            if not token:
                self.token_error("Failed to generate token")
                return

            response = TokenResponseModel(access_token=token, expires_in=3600, refresh_token=token).json()
            self.write(response)

        else:
            self.token_error("Invalid grant type", 400)
            return
