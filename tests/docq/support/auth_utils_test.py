"""Test auth utils."""
import unittest
from secrets import token_hex
from typing import Self
from unittest.mock import Mock, patch

from docq.support import auth_utils
from docq.support.auth_utils import (
    SESSION_COOKIE_NAME,
    _clear_cookie,
    _create_hmac,
    _decrypt,
    _encrypt,
    _get_cookie_session_id,
    _get_cookies,
    _set_cookie,
    _set_cookie_session_id,
    _verify_hmac,
    cached_sessions,
    generate_hmac_session_id,
    get_cache_auth_session,
    reset_cache_and_cookie_auth_session,
    session_data,
    set_cache_auth_session,
)


class TestAuthUtils(unittest.TestCase):
    """Test auth utils."""

    def setUp(self: Self) -> None:
        """Setup module."""
        auth_utils.AUTH_SESSION_SECRET_KEY = token_hex(32)

    @patch("docq.support.auth_utils.html")
    def test_set_cookie(self: Self, mock_html: Mock) -> None:
        """Test set cookie."""
        _set_cookie("cookie")
        mock_html.assert_called_once()

    @patch("docq.support.auth_utils.html")
    def test_clear_cookie(self: Self, mock_html: Mock) -> None:
        """Test clear cookie."""
        _clear_cookie(SESSION_COOKIE_NAME)
        mock_html.assert_called_once()

    @patch("docq.support.auth_utils._get_websocket_headers")
    def test_get_cookies(self: Self, mock_headers: Mock) -> None:
        """Test get cookies."""
        mock_headers.return_value = {"Cookie": "key=value"}
        result = _get_cookies()
        assert result == {"key": "value"}

    def test_create_hmac(self: Self) -> None:
        """Test create hmac."""
        msg = "test"
        digest = _create_hmac(msg)
        assert isinstance(digest, str)

    def test_verify_hmac(self: Self) -> None:
        """Test verify hmac."""
        msg = "test"
        digest = _create_hmac(msg)
        result = _verify_hmac(msg, digest)
        assert result

    def test_generate_session_id(self: Self) -> None:
        """Test generate session id."""
        id_ = generate_hmac_session_id()
        assert isinstance(id_, str)
        assert len(id_) == 64

    @patch("docq.support.auth_utils._set_cookie")
    def test_set_session_id(self: Self, mock_set_cookie: Mock) -> None:
        """Test set session id."""
        session_id = "test"
        _set_cookie_session_id(session_id)
        mock_set_cookie.assert_called_once_with(session_id)

    @patch("docq.support.auth_utils._get_cookies")
    def test_get_cookie_session_id(self: Self, mock_get_cookies: Mock) -> None:
        """Test get session id."""
        session_id = generate_hmac_session_id()
        cached_sessions[session_id] = _encrypt(("9999", "user", 1))
        mock_get_cookies.return_value = {SESSION_COOKIE_NAME: session_id}
        result = _get_cookie_session_id()
        assert result == session_id

    def test_encrypt_decrypt_auth(self: Self) -> None:
        """Test encrypt decrypt auth."""
        payload = {"org_id": "9999", "username": "user name", "user_id": 1}
        encrypted_auth = _encrypt(payload)
        decrypted_auth = _decrypt(encrypted_auth)
        assert payload == decrypted_auth

    @patch("docq.support.auth_utils._get_cookie_session_id")
    def test_cache_auth(self: Self, mock_get_cookie_session_id: Mock) -> None:
        """Test cache auth."""
        payload = {"org_id": "9999", "username": "user name", "user_id": 1}
        session_id = generate_hmac_session_id()
        mock_get_cookie_session_id.return_value = session_id
        set_cache_auth_session(payload)
        assert session_id in cached_sessions

    @patch("docq.support.auth_utils._get_cookie_session_id")
    def test_auth_result(
        self: Self,
        mock_get_cookie_session_id: Mock,
    ) -> None:
        """Test auth result."""
        payload = {"org_id": "9999", "username": "user name", "user_id": 1}
        session_id = generate_hmac_session_id()
        mock_get_cookie_session_id.return_value = session_id
        # mock_auto_login_enabled.return_value = True
        set_cache_auth_session(payload)
        result = get_cache_auth_session()
        assert result == {"org_id": "9999", "username": "user name", "user_id": 1}

    @patch("docq.support.auth_utils._get_cookie_session_id")
    def test_session_logout(self: Self, mock_get_cookie_session_id: Mock) -> None:
        """Test session logout."""
        session_id = generate_hmac_session_id()
        cached_sessions[session_id] = _encrypt(("9999", "user", 1))
        session_data[session_id] = session_id
        mock_get_cookie_session_id.return_value = session_id
        reset_cache_and_cookie_auth_session()
        assert session_id not in cached_sessions, "Cached session should be deleted on logout"
        assert session_id not in session_data, "Session data should be deleted on logout"
