"""Cache user sessions."""
import hashlib
import hmac
import json
import logging as log
from datetime import datetime, timedelta
from secrets import token_hex
from typing import Callable, Dict, Optional

import streamlit as st
from cachetools import TTLCache
from cryptography.fernet import Fernet
from streamlit.components.v1 import html
from streamlit.web.server.websocket_headers import _get_websocket_headers

from ..config import COOKIE_NAME, ENV_VAR_COOKIE_SECRET_KEY

CACHE_CONFIG = (1024 * 1, 60 * 60 * 24)
AUTH_KEY = Fernet.generate_key()
COOKIE_SECRET = st.secrets.get(ENV_VAR_COOKIE_SECRET_KEY, "secret_key")

"""Session Cache"""
cached_sessions:TTLCache[str, bytes] = TTLCache(*CACHE_CONFIG)
session_data:TTLCache[str, str]= TTLCache(*CACHE_CONFIG)

def _set_cookie(cookie: str) -> None:
    """Set client cookie for authentication."""
    try:
        expiry = datetime.now() + timedelta(hours=4)
        html(f"""
        <script>
            document.cookie = "{COOKIE_NAME}={cookie}; expires={expiry.strftime('%a, %d %b %Y %H:%M:%S GMT')}; path=/;";
        </script>
        """)
    except Exception as e:
        log.error("Failed to set cookie: %s", e)

def _clear_cookie() -> None:
    """Clear client cookie."""
    html(f"""
    <script>
        document.cookie = "{COOKIE_NAME}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/;";
    </script>
    """)

def _get_cookies() -> Optional[Dict[str, str]]:
    """Return client cookies."""
    try:
        headers = _get_websocket_headers()
        if headers is None:
            return None
        cookie_str = str(headers.get("Cookie"))
        cookies: Dict[str, str] = {}
        for cookie in cookie_str.split(";"):
            key, val = cookie.split("=")
            cookies[key.strip()] = val.strip()
        return cookies
    except Exception as e:
        log.error("Failed to get cookies: %s", e)
        return None

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

def _get_session_id() -> Optional[str]:
    """Return the session_id from the cookie."""
    try:
        cookies = _get_cookies()
        if cookies is not None:
            cookie = cookies.get(COOKIE_NAME)
            if cookie is None:
                return None
            if cookie not in cached_sessions:
                return None
            if not _verify_hmac(session_data[cookie], cookie):
                log.warning("Session ID not verified: %s", cookie)
                return None
            return cookie
    except Exception as e:
        log.error("Failed to get session id: %s", e)
        return None

def _encrypt_auth(auth: tuple) -> bytes:
    """Encrypt the auth data."""
    try:
        data = json.dumps(auth).encode()
        cipher = Fernet(AUTH_KEY)
        return cipher.encrypt(data)
    except Exception as e:
        log.error("Failed to encrypt auth data: %s", e)
        return None

def _decrypt_auth(auth: bytes) -> tuple:
    """Decrypt the auth data."""
    try:
        cipher = Fernet(AUTH_KEY)
        data = cipher.decrypt(auth)
        return tuple(json.loads(data))
    except Exception as e:
        log.error("Failed to decrypt auth data: %s", e)
        return None

def cache_auth(auth: Callable) -> Callable:
    """Cache the auth session value to remember credentials on page reload."""

    def wrapper(*args: tuple, **kwargs: dict) -> tuple:  # noqa: ANN401
        """Auth wrapper."""
        try:
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
        except Exception as e:
            log.error("Failed in auth wrapper: %s", e)
            return None

    return wrapper

def auth_result() -> Optional[tuple]:
    """Get cached auth result."""
    try:
        session_id = _get_session_id()
        if session_id:
            auth_ = cached_sessions[session_id]
            return _decrypt_auth(auth_)
        else:
            return None
    except Exception as e:
        log.error("Failed to get auth result: %s", e)
        return None

def session_logout() -> None:
    """Clear all the data used to remember user session."""
    try:
        session_id = _get_session_id()
        if session_id:
            # Remove user data from server on logout
            del cached_sessions[session_id]
            del session_data[session_id]
        _clear_cookie()
    except Exception as e:
        log.error("Failed to logout: %s", e)
