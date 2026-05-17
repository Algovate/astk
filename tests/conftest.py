"""Shared fixtures for astk test suite."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_response():
    """Factory to build a fake requests.Response."""
    def _factory(*, status_code=200, json_data=None, text="", content=b""):
        resp = MagicMock()
        resp.status_code = status_code
        resp.ok = status_code < 400
        if json_data is not None:
            resp.json.return_value = json_data
        resp.text = text
        resp.content = content
        return resp
    return _factory


@pytest.fixture
def mock_http_get(mock_response):
    """Patch astk.utils.http.http_get."""
    with patch("astk.utils.http.http_get") as m:
        m.return_value = mock_response(status_code=200, json_data={})
        yield m


@pytest.fixture
def mock_http_post(mock_response):
    """Patch astk.utils.http.http_post."""
    with patch("astk.utils.http.http_post") as m:
        m.return_value = mock_response(status_code=200, json_data={})
        yield m
