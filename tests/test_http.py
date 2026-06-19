"""Tests for astk.utils.http — shared HTTP session."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import requests

from astk.utils.constants import DEFAULT_UA
from astk.utils.errors import DataSourceError
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


def _patched_session(status_code=200):
    """Patch get_session with a MagicMock session and return (session, patcher)."""
    patcher = patch("astk.utils.http.get_session")
    mock_gs = patcher.start()
    session = MagicMock()
    mock_gs.return_value = session
    session.get.return_value = MagicMock(status_code=status_code)
    session.post.return_value = MagicMock(status_code=status_code)
    return session, patcher


class TestHttpGet:
    def test_delegates_to_session(self):
        session, patcher = _patched_session()
        try:
            http_get("http://example.com", params={"a": "b"}, timeout=5)
            session.get.assert_called_once_with(
                "http://example.com", headers=None, params={"a": "b"}, timeout=5
            )
        finally:
            patcher.stop()

    def test_non_2xx_raises_data_source_error(self):
        session, patcher = _patched_session(status_code=503)
        # Make raise_for_status actually raise
        session.get.return_value.raise_for_status.side_effect = requests.HTTPError("503")
        session.get.return_value.status_code = 503
        try:
            with pytest.raises(DataSourceError, match="HTTP 503"):
                http_get("http://example.com")
        finally:
            patcher.stop()

    def test_2xx_passes_through(self):
        session, patcher = _patched_session(status_code=200)
        # raise_for_status returns None (no raise) on the MagicMock by default
        try:
            resp = http_get("http://example.com")
            assert resp.status_code == 200
        finally:
            patcher.stop()


class TestHttpPost:
    def test_delegates_to_session(self):
        session, patcher = _patched_session()
        try:
            http_post("http://example.com", json={"q": "test"}, headers={"X": "1"}, timeout=10)
            session.post.assert_called_once_with(
                "http://example.com", headers={"X": "1"}, json={"q": "test"}, timeout=10
            )
        finally:
            patcher.stop()

    def test_non_2xx_raises_data_source_error(self):
        session, patcher = _patched_session(status_code=401)
        session.post.return_value.raise_for_status.side_effect = requests.HTTPError("401")
        session.post.return_value.status_code = 401
        try:
            with pytest.raises(DataSourceError, match="HTTP 401"):
                http_post("http://example.com")
        finally:
            patcher.stop()
