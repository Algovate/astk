"""Tests for astk.signals.baidu_api — concept blocks and fund flow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from astk.signals.baidu_api import get_concept_blocks, get_fund_flow_history, get_fund_flow_realtime


CONCEPT_RESPONSE = {
    "ResultCode": 0,
    "Result": [
        {"type": "行业板块", "list": [{"name": "半导体", "increase": "2.5", "desc": "芯片"}]},
        {"type": "概念板块", "list": [{"name": "AI芯片", "increase": "3.1", "desc": "人工智能"}]},
        {"type": "地域板块", "list": [{"name": "上海", "increase": "0.5", "desc": ""}]},
    ],
}


class TestGetConceptBlocks:
    @patch("astk.signals.baidu_api.http_get")
    def test_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = CONCEPT_RESPONSE
        mock_get.return_value = mock_resp

        result = get_concept_blocks("688017")
        assert len(result["industry"]) == 1
        assert result["industry"][0]["name"] == "半导体"
        assert len(result["concept"]) == 1
        assert "AI芯片" in result["concept_tags"]
        assert len(result["region"]) == 1

    @patch("astk.signals.baidu_api.http_get")
    def test_api_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ResultCode": -1}
        mock_get.return_value = mock_resp

        with pytest.raises(RuntimeError, match="百度PAE错误"):
            get_concept_blocks("688017")


class TestGetFundFlowRealtime:
    @patch("astk.signals.baidu_api.http_get")
    def test_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "ResultCode": 0,
            "Result": {"update_data": "09:30,1234,100,200,300,400,,,,15.5;09:31,1235,110,210,310,410,,,,15.6"},
        }
        mock_get.return_value = mock_resp

        rows = get_fund_flow_realtime("688017", "20250115")
        assert len(rows) == 2
        assert rows[0]["time"] == "09:30"
        assert rows[0]["mainForce"] == 100.0

    @patch("astk.signals.baidu_api.http_get")
    def test_empty(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ResultCode": 0, "Result": {"update_data": ""}}
        mock_get.return_value = mock_resp

        assert get_fund_flow_realtime("688017", "20250115") == []

    @patch("astk.signals.baidu_api.http_get")
    def test_error_returns_empty(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ResultCode": -1}
        mock_get.return_value = mock_resp

        assert get_fund_flow_realtime("688017", "20250115") == []


class TestGetFundFlowHistory:
    @patch("astk.signals.baidu_api.http_get")
    def test_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "ResultCode": 0,
            "Result": {
                "list": [
                    {"showtime": "2025-01-15", "closepx": "100", "ratio": "2.5", "superNetIn": "500", "largeNetIn": "300", "mediumNetIn": "200", "littleNetIn": "100", "extMainIn": "800"},
                ]
            },
        }
        mock_get.return_value = mock_resp

        rows = get_fund_flow_history("688017", days=5)
        assert len(rows) == 1
        assert rows[0]["date"] == "2025-01-15"
        assert rows[0]["close"] == "100"

    @patch("astk.signals.baidu_api.http_get")
    def test_empty(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"ResultCode": 0, "Result": {}}
        mock_get.return_value = mock_resp

        assert get_fund_flow_history("688017") == []
