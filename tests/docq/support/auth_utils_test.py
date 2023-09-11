"""Test auth utils."""
import unittest
from secrets import token_hex
from typing import Self
from unittest.mock import Mock, patch

from docq.config import FeatureType
from docq.support import auth_utils
from docq.support.auth_utils import (
    _auto_login_enabled,
    _clear_cookie,
    _create_hmac,
    _decrypt_auth,
    _encrypt_auth,
    _get_cookies,
    _get_session_id,
    _set_cookie,
    _set_session_id,
    _verify_hmac,
    auth_result,
    cache_auth,
    cached_sessions,
    generate_session_id,
    session_data,
    session_logout,
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
        _clear_cookie()
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
        id_ = generate_session_id()
        assert isinstance(id_, str)
        assert len(id_) == 64

    @patch("docq.support.auth_utils._set_cookie")
    def test_set_session_id(self: Self, mock_set_cookie: Mock) -> None:
        """Test set session id."""
        session_id = "test"
        _set_session_id(session_id)
        mock_set_cookie.assert_called_once_with(session_id)

    @patch("docq.support.auth_utils._get_cookies")
    def test_get_session_id(self: Self, mock_get_cookies: Mock) -> None:
        """Test get session id."""
        session_id = generate_session_id()
        cached_sessions[session_id] = _encrypt_auth(("9999", "user", 1))
        mock_get_cookies.return_value = {"docqai/_docq": session_id}
        result = _get_session_id()
        assert result == session_id

    def test_encrypt_decrypt_auth(self: Self) -> None:
        """Test encrypt decrypt auth."""
        auth = ("9999", "user", 1)
        encrypted_auth = _encrypt_auth(auth)
        decrypted_auth = _decrypt_auth(encrypted_auth)
        assert auth == decrypted_auth

    @patch("docq.support.auth_utils._get_session_id")
    @patch("docq.support.auth_utils._auto_login_enabled")
    def test_cache_auth(
        self: Self,
        mock_auto_login_enabled: Mock,
        mock_get_session_id: Mock
        ) -> None:
        """Test cache auth."""
        mock_func = Mock(return_value=("9999", "user", 1))
        session_id = generate_session_id()
        mock_get_session_id.return_value = session_id
        mock_auto_login_enabled.return_value = True
        cache_auth(mock_func)()
        assert session_id in cached_sessions
        assert mock_func.call_count == 1

    @patch("docq.support.auth_utils._auto_login_enabled")
    @patch("docq.support.auth_utils._get_session_id")
    def test_auth_result(self: Self, mock_get_session_id: Mock, mock_auto_login_enabled: Mock) -> None:
        """Test auth result."""
        mock_func = Mock(return_value=("9999", "user", 1))
        session_id = generate_session_id()
        mock_get_session_id.return_value = session_id
        mock_auto_login_enabled.return_value = True
        cache_auth(mock_func)()
        result = auth_result()
        assert result == ("9999", "user", 1)

    @patch("docq.support.auth_utils._get_session_id")
    def test_session_logout(self: Self, mock_get_session_id: Mock) -> None:
        """Test session logout."""
        session_id = generate_session_id()
        cached_sessions[session_id] = _encrypt_auth(("9999", "user", 1))
        session_data[session_id] = session_id
        mock_get_session_id.return_value = session_id
        session_logout()
        assert session_id not in cached_sessions
        assert session_id not in session_data

    @patch("docq.support.auth_utils.get_system_settings")
    def test_auto_login_enabled(self: Self, mock_get_system_settings: Mock) -> None:
        """Test auto login enabled."""
        mock_get_system_settings.return_value = [FeatureType.AUTO_LOGIN.name]
        result = _auto_login_enabled()
        assert mock_get_system_settings.call_count == 1
        assert result, "Auto login should be enabled"
