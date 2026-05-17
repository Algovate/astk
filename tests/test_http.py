"""Tests for astk.utils.http — shared HTTP session."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from astk.utils.constants import DEFAULT_UA
from astk.utils.http import get_session, http_get, http_post


@pytest.fixture(autouse=True)
def _clear_cache():
    get_session.cache_clear()
    yield
    get_session.cache_clear()


class TestGetSession:
    def test_returns_session(self):
        s = get_session()
        assert isinstance(s, requests.Session)

    def test_has_user_agent(self):
        s = get_session()
        assert s.headers.get("User-Agent") == DEFAULT_UA

    def test_cached_singleton(self):
        s1 = get_session()
        s2 = get_session()
        assert s1 is s2

    def test_cache_clear_creates_new(self):
        s1 = get_session()
        get_session.cache_clear()
        s2 = get_session()
        assert s1 is not s2


class TestHttpGet:
    @patch.object(get_session.__wrapped__ if hasattr(get_session, '__wrapped__') else get_session, '__call__', create=True)
    def test_delegates_to_session(self, mock_response):
        with patch("astk.utils.http.get_session") as mock_gs:
            session = MagicMock()
            mock_gs.return_value = session
            session.get.return_value = MagicMock(status_code=200)
            result = http_get("http://example.com", params={"a": "b"}, timeout=5)
            session.get.assert_called_once_with(
                "http://example.com", headers=None, params={"a": "b"}, timeout=5
            )


class TestHttpPost:
    def test_delegates_to_session(self):
        with patch("astk.utils.http.get_session") as mock_gs:
            session = MagicMock()
            mock_gs.return_value = session
            session.post.return_value = MagicMock(status_code=200)
            http_post("http://example.com", json={"q": "test"}, headers={"X": "1"}, timeout=10)
            session.post.assert_called_once_with(
                "http://example.com", headers={"X": "1"}, json={"q": "test"}, timeout=10
            )
