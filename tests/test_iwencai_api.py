"""Tests for astk.research.iwencai_api — dedup_articles and iwencai_search."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from astk.research.iwencai_api import dedup_articles, iwencai_search


# ── dedup_articles (pure) ────────────────────────────────────


class TestDedupArticles:
    def test_keeps_highest_score(self):
        articles = [
            {"uid": "a1", "title": "A", "publish_date": "2025-01-15", "score": 0.8},
            {"uid": "a1", "title": "A v2", "publish_date": "2025-01-15", "score": 0.95},
        ]
        result = dedup_articles(articles)
        assert len(result) == 1
        assert result[0]["score"] == 0.95

    def test_sorted_by_date_desc(self):
        articles = [
            {"uid": "a1", "title": "A", "publish_date": "2025-01-14", "score": 0.9},
            {"uid": "a2", "title": "B", "publish_date": "2025-01-15", "score": 0.8},
        ]
        result = dedup_articles(articles)
        assert result[0]["publish_date"] == "2025-01-15"

    def test_empty_list(self):
        assert dedup_articles([]) == []

    def test_fallback_uid(self):
        articles = [
            {"title": "Report A", "publish_date": "2025-01-15", "score": 0.9},
            {"title": "Report A", "publish_date": "2025-01-15", "score": 0.7},
        ]
        result = dedup_articles(articles)
        assert len(result) == 1
        assert result[0]["score"] == 0.9


# ── iwencai_search (mocked HTTP) ─────────────────────────────


class TestIwencaiSearch:
    @patch("astk.research.iwencai_api.http_post")
    def test_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status_code": 0,
            "data": [{"uid": "a1", "title": "Test"}],
        }
        mock_post.return_value = mock_resp
        result = iwencai_search("AI芯片")
        assert len(result) == 1

    @patch("astk.research.iwencai_api.http_post")
    def test_http_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = "Server Error"
        mock_post.return_value = mock_resp
        with pytest.raises(RuntimeError, match="iwencai HTTP 500"):
            iwencai_search("test")

    @patch("astk.research.iwencai_api.http_post")
    def test_api_error(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status_code": 1, "status_msg": "rate limited"}
        mock_post.return_value = mock_resp
        with pytest.raises(RuntimeError, match="rate limited"):
            iwencai_search("test")

    @patch("astk.research.iwencai_api.http_post")
    def test_empty_data(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status_code": 0, "data": None}
        mock_post.return_value = mock_resp
        result = iwencai_search("test")
        assert result == []
