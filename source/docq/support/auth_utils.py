"""Cache user sessions."""
import hashlib
import hmac
import json
import logging as log
import os
from datetime import datetime, timedelta
from secrets import token_hex
from typing import Callable, Dict, Optional

from cachetools import TTLCache
from cryptography.fernet import Fernet
from streamlit.components.v1 import html
from streamlit.web.server.websocket_headers import _get_websocket_headers

from ..config import COOKIE_NAME, ENV_VAR_COOKIE_SECRET_KEY, FeatureType
from ..manage_settings import SystemSettingsKey, get_organisation_settings

EXPIRY_HOURS = 4
CACHE_CONFIG = (1024 * 1, 60 * 60 * EXPIRY_HOURS)
AUTH_KEY = Fernet.generate_key()
AUTH_SESSION_SECRET_KEY: str = os.environ.get(ENV_VAR_COOKIE_SECRET_KEY)

# Session Cache.
cached_sessions:TTLCache[str, bytes] = TTLCache(*CACHE_CONFIG)
session_data:TTLCache[str, str]= TTLCache(*CACHE_CONFIG)

def init_session_cache() -> None:
    """Initialize session cache."""
    if AUTH_SESSION_SECRET_KEY is None:
        log.fatal("Failed to initialize session cache: COOKIE_SECRET_KEY not set")
        raise ValueError("COOKIE_SECRET_KEY must be set")
    if len(AUTH_SESSION_SECRET_KEY) < 16:
        log.fatal("Failed to initialize session cache: COOKIE_SECRET_KEY must be 16 or more characters")
        raise ValueError("COOKIE_SECRET_KEY must be 16 or more characters")


def _set_cookie(cookie: str) -> None:
    """Set client cookie for authentication."""
    try:
        expiry = datetime.now() + timedelta(hours=EXPIRY_HOURS)
        html(f"""
        <script>
            const secure = location.protocol === "https:" ? " secure;" : "";
            document.cookie = "{COOKIE_NAME}={cookie}; expires={expiry.strftime('%a, %d %b %Y %H:%M:%S GMT')}; path=/; SameSite=Secure;" + secure;
        </script>
        """, width=0, height=0)
    except Exception as e:
        log.error("Failed to set cookie: %s", e)


def _clear_cookie() -> None:
    """Clear client cookie."""
    html(f"""
    <script>
        document.cookie = "{COOKIE_NAME}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/;";
    </script>
    """, width=0, height=0)


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


def _create_hmac( msg: str) -> str:
    """Create a HMAC hash."""
    return hmac.new(
        AUTH_SESSION_SECRET_KEY.encode(),
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


def _encrypt_auth(*args: tuple, **kwargs: dict) -> bytes:
    """Encrypt the auth data."""
    try:
        data = json.dumps([args, kwargs]).encode()
        cipher = Fernet(AUTH_KEY)
        return cipher.encrypt(data)
    except Exception as e:
        log.error("Failed to encrypt auth data: %s", e)
        return None


def _decrypt_auth(configs: bytes) -> tuple[tuple, dict]:
    """Decrypt the auth data."""
    try:
        cipher = Fernet(AUTH_KEY)
        data = cipher.decrypt(configs)
        data_ = list(json.loads(data))
        return tuple(data_[0]), data_[1]
    except Exception as e:
        log.error("Failed to decrypt auth data: %s", e)
        return None


def _update_auth_expiry(session_id: str) -> None:
    """Update the auth expiry time."""
    try:
        cached_sessions[session_id] = cached_sessions[session_id]
        session_data[session_id] = session_data[session_id]
        _set_session_id(session_id)
    except Exception as e:
        log.error("Failed to update auth expiry: %s", e)


def _auto_login_enabled(org_id: int) -> bool:
    """Check if auto login feature is enabled."""
    try:
        system_settings = get_organisation_settings(org_id=org_id, key=SystemSettingsKey.ENABLED_FEATURES)
        if system_settings: # Only enable feature when explicitly enabled (dafault to Disabled)
            return FeatureType.AUTO_LOGIN.name in system_settings
        return False
    except Exception as e:
        log.error("Failed to check if auto login is enabled: %s", e)
        return False


def cache_session_state(set_configs: Callable) -> Callable:
    """Cache the auth session value to remember credentials on page reload."""

    def wrapper(*args: tuple, **kwargs: dict) -> tuple:
        """Auth wrapper."""
        try:
            if "anonymous" in kwargs and kwargs["anonymous"]:
                return set_configs(*args, **kwargs)

            session_id = _get_session_id()
            if not session_id:
                session_id = generate_session_id()
                _set_session_id(session_id)
            if session_id:
                set_configs(*args, **kwargs)
                cached_sessions[session_id] = _encrypt_auth(*args, **kwargs)
                _update_auth_expiry(session_id)
        except Exception as e:
            log.error("Error caching auth session state: %s", e)
            return None

    return wrapper


def get_auth_configs() -> Optional[tuple[tuple, dict]]:
    """Get cached session state configs for auth."""
    try:
        session_id = _get_session_id()
        if session_id in cached_sessions:
            configs = cached_sessions[session_id]
            args, kwargs = _decrypt_auth(configs)
            selected_org_id = kwargs.get("selected_org_id") or args[1]
            if not _auto_login_enabled(selected_org_id):
                return None
            return _decrypt_auth(configs)
        else:
            return None
    except Exception as e:
        log.error("Failed to get auth result: %s", e)
        return None


def session_logout() -> None:
    """Clear all the data used to remember user session."""
    try:
        session_id = _get_session_id()
        if session_id in cached_sessions:
            del cached_sessions[session_id]
        if session_id in session_data:
            del session_data[session_id]
        _clear_cookie()
    except Exception as e:
        log.error("Failed to logout: %s", e)
