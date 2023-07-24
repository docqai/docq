"""Cache user sessions."""
from secrets import token_hex
from typing import Any, Callable

from cachetools import TTLCache
from streamlit_javascript import st_javascript

cached_sessions = TTLCache(maxsize=100, ttl=60 * 60 * 24)


def js_script(script: Callable) -> Any:  # noqa: ANN401
    """Run javascript in the frontend and return the value."""

    def wrapper(*args: tuple, **kwargs: dict) -> Any:  # noqa: ANN401
        """JS script wrapper."""
        return st_javascript(script(*args, **kwargs))

    return wrapper

@js_script
def _get_session_id() -> str:
    """Get the session id."""
    return "sessionStorage.getItem('sessionId')"


@js_script
def _set_session_id(id_: str) -> str:
    """Set the session id."""
    return f"sessionStorage.setItem('sessionId', '{id_}')"

def generate_session_id(length: int = 32) -> str:
    """Generate a secure and unique session_id."""
    return token_hex(length // 2)

def cache_auth(auth: Callable) -> Callable:
    """Cache the auth session value to remember credentials on page reload."""

    def wrapper(*args: tuple, **kwargs: dict) -> dict:  # noqa: ANN401
        """Auth wrapper."""
        session_id = _get_session_id()
        print(f"\x1b[32mDEBUG\x1b[0m Session ID: {session_id}")
        if not isinstance(session_id, str) or len(session_id) < 16:
            session_id = generate_session_id() # TODO: Add more encryption if necessary
            _set_session_id(session_id)
        if session_id not in cached_sessions:
            _auth = auth(*args, **kwargs)
            if _auth is None:
                return _auth
            cached_sessions[session_id] = _auth
        return cached_sessions[session_id]

    return wrapper

def auth_result() -> Any: # noqa: ANN401
    """Get cached auth result."""
    session_id = _get_session_id()
    if session_id in cached_sessions:
        return cached_sessions[session_id]

    return None
