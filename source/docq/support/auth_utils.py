"""Cache user sessions."""
import hashlib
import hmac
import json
import logging as log
import os
from datetime import datetime, timedelta
from secrets import token_hex
from typing import Dict, Optional

from cachetools import TTLCache
from cryptography.fernet import Fernet
from streamlit.components.v1 import html
from streamlit.web.server.websocket_headers import _get_websocket_headers

from ..config import COOKIE_NAME, ENV_VAR_COOKIE_SECRET_KEY

EXPIRY_HOURS = 4
CACHE_CONFIG = (1024 * 1, 60 * 60 * EXPIRY_HOURS)
AUTH_KEY = Fernet.generate_key()
AUTH_SESSION_SECRET_KEY: str = os.environ.get(ENV_VAR_COOKIE_SECRET_KEY)

# Chase of session data keyed by session id
cached_sessions: TTLCache[str, bytes] = TTLCache(*CACHE_CONFIG)

# Cache of session id's keyed by hmac hash
session_data: TTLCache[str, str] = TTLCache(*CACHE_CONFIG)


# TODO: the code that handles the cookie should move to the web side. session state tracking is in the backend but not a public API as it's just cross cutting.


def init_session_cache() -> None:
    """Initialize session cache."""
    if AUTH_SESSION_SECRET_KEY is None:
        log.fatal("Failed to initialize session cache: COOKIE_SECRET_KEY not set")
        raise ValueError("COOKIE_SECRET_KEY must be set")
    if len(AUTH_SESSION_SECRET_KEY) < 32:
        log.fatal("Failed to initialize session cache: COOKIE_SECRET_KEY must be 32 or more characters")
        raise ValueError("COOKIE_SECRET_KEY must be 32 or more characters")


def _set_cookie(cookie: str) -> None:
    """Set client cookie for authentication."""
    try:
        expiry = datetime.now() + timedelta(hours=EXPIRY_HOURS)
        html(
            f"""
        <script>
            const secure = location.protocol === "https:" ? " secure;" : "";
            document.cookie = "{COOKIE_NAME}={cookie}; expires={expiry.strftime('%a, %d %b %Y %H:%M:%S GMT')}; path=/; SameSite=Secure;" + secure;
        </script>
        """,
            width=0,
            height=0,
        )
    except Exception as e:
        log.error("Failed to set cookie: %s", e)


def _clear_cookie(cookie_name: str) -> None:
    """Clear client cookie."""
    html(
        f"""
    <script>
        document.cookie = "{cookie_name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/;";
    </script>
    """,
        width=0,
        height=0,
    )
    log.debug("Clear client cookie: %s", cookie_name)


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


def _create_hmac(msg: str) -> str:
    """Create a HMAC hash."""
    return hmac.new(AUTH_SESSION_SECRET_KEY.encode(), msg.encode(), hashlib.sha256).hexdigest()


def _verify_hmac(msg: str, digest: str) -> bool:
    """Verify credibility of HMAC hash."""
    return hmac.compare_digest(_create_hmac(msg), digest)


def generate_hmac_session_id(length: int = 32) -> str:
    """Generate a secure (HMAC) and unique session_id then track in session cache."""
    id_ = token_hex(length // 2)
    hmac_ = _create_hmac(id_)
    session_data[hmac_] = id_
    return hmac_


def _set_cookie_session_id(hmac_session_id: str) -> None:
    """Set the encrypted session_id in the cookie."""
    _set_cookie(hmac_session_id)
    log.debug("Set cookie - hmac session id: %s", hmac_session_id)


def _get_cookie_session_id() -> str | None:
    """Return the Docq encrypted HMAC session_id from the cookie."""
    try:
        hmac_session_id = None
        cookies = _get_cookies()
        if cookies is not None:
            hmac_session_id = cookies.get(COOKIE_NAME)
        return hmac_session_id
    except Exception as e:
        log.error("Failed to get session id: %s", e)
        return None


def verify_cookie_hmac_session_id() -> str | None:
    """Verify the encrypted session_id from the cookie.

    Return:
        str: The hmac_session_id if verified.
        None: If not verified.
    """
    hmac_session_id = None
    hmac_session_id = _get_cookie_session_id()
    if hmac_session_id is None:
        log.debug("No session id in cookie found")
    elif hmac_session_id not in cached_sessions:
        log.debug(
            "verify_cookie_hmac_session_id(): HMAC Session ID not found in cache. Session expired or was explicitly removed: %s",
            hmac_session_id,
        )
        hmac_session_id = None
    elif hmac_session_id not in session_data or not _verify_hmac(session_data[hmac_session_id], hmac_session_id):
        log.warning("verify_cookie_hmac_session_id(): HMAC Session ID failed verification: %s", hmac_session_id)
        hmac_session_id = None
    return hmac_session_id


def _encrypt(payload: dict) -> bytes:
    """Encrypt some data."""
    try:
        data = json.dumps(payload).encode()
        cipher = Fernet(AUTH_KEY)
        return cipher.encrypt(data)
    except Exception as e:
        log.error("Failed to encrypt auth data: %s", e)
        return None


def _decrypt(encrypted_payload: bytes) -> dict:
    """Decrypt some data."""
    try:
        cipher = Fernet(AUTH_KEY)
        data = cipher.decrypt(encrypted_payload)
        result = json.loads(data)
        return result
    except Exception as e:
        log.error("Failed to decrypt auth data: %s", e)
        return None


def _reset_expiry_cache_auth_session(session_id: str) -> None:
    """Update the auth expiry time."""
    try:
        cached_sessions[session_id] = cached_sessions[session_id]
        session_data[session_id] = session_data[session_id]
        # _set_cookie_session_id(session_id)
    except Exception as e:
        log.error("Failed to update auth expiry: %s", e)


def set_cache_auth_session(val: dict) -> None:
    """Caches the session state configs for auth, persisting across connections.

    Args:
        val (dict): The session state for auth.
    """
    try:
        hmac_session_id = _get_cookie_session_id()
        if not hmac_session_id:
            hmac_session_id = generate_hmac_session_id()
        _set_cookie_session_id(hmac_session_id)
        cached_sessions[hmac_session_id] = _encrypt(val)
        _reset_expiry_cache_auth_session(hmac_session_id)
    except Exception as e:
        log.error("Error caching auth session: %s", e)


def get_cache_auth_session() -> dict | None:
    """Verify the session auth token and get the cached session state for the current session. The current session is identified by a session_id wrapped in a auth token in a browser session cookie."""
    try:
        decrypted_auth_session_data = None
        hmac_session_id = _get_cookie_session_id()
        if hmac_session_id in cached_sessions:
            encrypted_auth_session_data = cached_sessions[hmac_session_id]
            decrypted_auth_session_data = _decrypt(encrypted_auth_session_data)
        return decrypted_auth_session_data
    except Exception as e:
        log.error("Failed to get auth session from cache: %s", e)
        return None


def remove_cache_auth_session() -> None:
    """Remove the cached session state for the current session. The current session is identified by a session_id in a particular browsersession cookie."""
    try:
        hmac_session_id = _get_cookie_session_id()
        if hmac_session_id in cached_sessions:
            del cached_sessions[hmac_session_id]
        if hmac_session_id in session_data:
            del session_data[hmac_session_id]
    except Exception as e:
        log.error("Failed to remove auth session from cache: %s", e)


def reset_cache_and_cookie_auth_session() -> None:
    """Clear all the data used to remember user session (auth session cache and session cookie). This must be called at login and cookie."""
    try:
        remove_cache_auth_session()
        _clear_cookie(COOKIE_NAME)
    except Exception as e:
        log.error("Failed to clear session data caches (hmac, session data, and session cookie ): %s", e)
