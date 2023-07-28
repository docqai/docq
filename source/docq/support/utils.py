"""Cache user sessions."""
import hashlib
import hmac
import logging as log
import pickle
from datetime import datetime, timedelta
from secrets import token_hex
from typing import Callable

import streamlit as st
from cachetools import TTLCache
from cryptography.fernet import Fernet
from streamlit.components.v1 import html
from streamlit.web.server.websocket_headers import _get_websocket_headers

CACHE_CONFIG = (1024 * 1, 60 * 60 * 24)
AUTH_KEY = Fernet.generate_key()
COOKIE_SECRET = st.secrets["COOKIE_SECRET_KEY"]

"""Session Cache"""
cached_sessions:TTLCache[str, bytes] = TTLCache(*CACHE_CONFIG)
session_data:TTLCache[str, str]= TTLCache(*CACHE_CONFIG)

def _set_cookie(cookie: str) -> None:
    """Set client cookie for authentication."""
    expiry = datetime.now() + timedelta(hours=4)
    html(f"""
    <script>
        document.cookie = "docqai/_docq={cookie}; expires={expiry.strftime('%a, %d %b %Y %H:%M:%S GMT')}; path=/";
    </script>
    """)

def _clear_cookie() -> None:
    """Clear client cookie."""
    html("""
    <script>
        document.cookie = "docqai/_docq=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/";
    </script>
         """)

def _get_cookies() -> None | dict[str, str]:
    """Return client cookies."""
    headers = _get_websocket_headers()
    if headers is None:
        return None
    cookie_str = str(headers.get("Cookie"))
    cookies: dict[str, str] = {}
    for cookie in cookie_str.split(";"):
        key, val = cookie.split("=")
        cookies[key.strip()] = val.strip()
    return cookies


def _create_hmac( msg: str, key: str = COOKIE_SECRET) -> str:
    """Create a HMAC hash."""
    return hmac.new(
        key.encode(),
        msg.encode(),
        hashlib.sha256
    ).hexdigest()

def _verify_hmac(msg: str, digest: str) -> bool:
    """Verify credibility of HMAC hash."""
    return hmac.compare_digest(
        _create_hmac(msg),
        digest
    )

def generate_session_id(length: int = 32) -> str:
    """Generate a secure and unique session_id."""
    id_ = token_hex(length // 2)
    hmac_ = _create_hmac(id_)
    session_data[hmac_] = id_
    return hmac_

def _set_session_id(session_id: str) -> None:
    """Set the session_id in the cookie."""
    _set_cookie(session_id)

def _get_session_id() -> str | None:
    """Return the session_id from the cookie."""
    cookies = _get_cookies()
    if cookies is not None:
        cookie = cookies.get("docqai/_docq")
        if cookie is None:
            return None
        if cookie not in cached_sessions:
            return None
        if not _verify_hmac(session_data[cookie], cookie):
            log.warning("Session ID not verified: %s", cookie)
            return None

        return cookie

def _encrypt_auth(auth: tuple) -> bytes:
    """Encrypt the auth data."""
    data = pickle.dumps(auth)
    cipher = Fernet(AUTH_KEY)
    return cipher.encrypt(data)

def _decrypt_auth(auth: bytes) -> tuple:
    """Decrypt the auth data."""
    cipher = Fernet(AUTH_KEY)
    data = cipher.decrypt(auth)
    return pickle.loads(data)

def cache_auth(auth: Callable) -> Callable:
    """Cache the auth session value to remember credentials on page reload."""

    def wrapper(*args: tuple, **kwargs: dict) -> tuple:  # noqa: ANN401
        """Auth wrapper."""
        session_id = _get_session_id()
        if not session_id:
            session_id = generate_session_id()
            _set_session_id(session_id)
        if session_id not in cached_sessions:
            _auth = auth(*args, **kwargs)
            if _auth is None:
                return _auth
            cached_sessions[session_id] = _encrypt_auth(_auth)
        return _decrypt_auth(cached_sessions[session_id])

    return wrapper

def auth_result() -> tuple | None:
    """Get cached auth result."""
    session_id = _get_session_id()
    if session_id:
        auth_ = cached_sessions[session_id]
        return _decrypt_auth(auth_)
    else:
        return None

def session_logout() -> None:
    """Clear all the data used to remember user session."""
    session_id = _get_session_id()
    if session_id:
        del cached_sessions[session_id]
        del session_data[session_id]
    _clear_cookie()
