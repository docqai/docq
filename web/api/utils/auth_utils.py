"""API Auth related utilities."""
import functools
import logging as log
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Literal, Optional

import jwt.exceptions as jwt_exceptions
from cryptography.hazmat.backends import default_backend as crypto_default_backend
from cryptography.hazmat.primitives import serialization as crypto_serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from docq.config import ENV_VAR_DOCQ_API_SECRET
from jwt import JWT, jwk_from_pem
from jwt.utils import get_int_from_datetime
from opentelemetry import trace
from tornado.web import HTTPError

from web.api.base_handlers import BaseRequestHandler
from web.api.models import UserModel

INSTANCE = JWT()
KEY_ERROR = (jwt_exceptions.UnsupportedKeyTypeError, jwt_exceptions.InvalidKeyTypeError)

tracer = trace.get_tracer(__name__)


@tracer.start_as_current_span("authenticated")
def authenticated(method: Callable[..., Any]) -> Callable[..., Any]:
    """Decorate RequestHandler methods with this to require a valid token."""

    @functools.wraps(method)
    def wrapper(self: BaseRequestHandler, *args: Any, **kwargs: Any) -> Any:
        span = trace.get_current_span()
        try:
            api_key = self.request.headers.get("X-API-Key", "")

            if not validate_api_key(api_key):
                span.set_status(trace.Status(trace.StatusCode.ERROR))
                span.record_exception(ValueError("Invalid token"))
                raise HTTPError(401, reason="API key missing")

            if self.current_user is not None:
                return method(self, *args, **kwargs)

        except ValueError as e:
            span.set_status(trace.Status(trace.StatusCode.ERROR))
            span.record_exception(e)
            raise HTTPError(401, reason="Invalid Authorization header") from e

    return wrapper


def encode_jwt(data: UserModel) -> Optional[str]:
    """Encode a JWT."""
    docq_host_address = os.environ.get("DOCQ_SERVER_ADDRESS", "http://localhost")
    try:
        payload = {
            "iss": docq_host_address,
            "sub": "auth",
            "exp": get_int_from_datetime(datetime.now(tz=timezone.utc) + timedelta(hours=23)),
            "nbf": get_int_from_datetime(datetime.now(tz=timezone.utc)),
            "iat": get_int_from_datetime(datetime.now(tz=timezone.utc)),
            "data": data.model_dump(),
        }
        key = jwk_from_pem(get_key("private"))
        return INSTANCE.encode(payload, key, alg="RS256")

    except (*KEY_ERROR, jwt_exceptions.JWTEncodeError) as e:
        log.error("Error encoding token: %s", e)
        raise HTTPError(500, "Error encoding token") from e


def decode_jwt(token: str, check_expired: bool = True) -> dict:
    """Decode a JWT."""
    try:
        key = jwk_from_pem(get_key("public"))
    except KEY_ERROR as e:
        log.error("Error loading key: %s", e)
        raise HTTPError(500, "Error loading key") from e

    try:
        return INSTANCE.decode(token, key, algorithms={"RS256"}, do_time_check=check_expired)
    except (jwt_exceptions.JWSDecodeError, jwt_exceptions.JWTDecodeError) as e:
        log.error("Error decoding token: %s", e)
        raise HTTPError(401, reason="Unauthorized") from e


def validate_api_key(key: str) -> bool:
    """Validate the token. This is just a placeholder, replace with your own validation logic."""
    is_valid = False
    secret = os.environ.get(ENV_VAR_DOCQ_API_SECRET, None)
    if secret is not None or secret != "":
        is_valid = key == secret

    return is_valid


def _generate_rsa_key() -> tuple[str, str]:
    """Generate a RSA key pair and return the private key as PEM."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=crypto_default_backend(),
    )
    private_pem = private_key.private_bytes(
        crypto_serialization.Encoding.PEM,
        crypto_serialization.PrivateFormat.TraditionalOpenSSL,
        crypto_serialization.NoEncryption(),
    )
    public_key = private_key.public_key().public_bytes(
        crypto_serialization.Encoding.PEM, crypto_serialization.PublicFormat.PKCS1
    )
    return private_pem.decode("utf-8"), public_key.decode("utf-8")


def _get_key_dir_path() -> str:
    """Get the key directory path."""
    key_dir_path = "./.streamlit/.keys"
    if not os.path.exists(key_dir_path):
        os.makedirs(key_dir_path)
    return key_dir_path


def get_key(type_: Literal["public", "private"] = "public") -> bytes:
    """Get the public or private key."""
    key_dir_path = _get_key_dir_path()

    keys = {
        "public": os.path.join(key_dir_path, "public.pem"),
        "private": os.path.join(key_dir_path, "private.pem"),
    }

    if not os.path.exists(keys[type_]):
        priv_key, pub_key = _generate_rsa_key()
        with open(keys["public"], "w") as f:
            f.write(pub_key)
        with open(keys["private"], "w") as f:
            f.write(priv_key)

    with open(keys[type_], "rb") as f:
        return f.read()
