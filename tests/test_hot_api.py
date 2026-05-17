"""Tests for astk.signals.hot_api — get_hot_stocks."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from astk.signals.hot_api import get_hot_stocks


MOCK_HOT_RESPONSE = {
    "errocode": 0,
    "errormsg": "",
    "data": [
        {
            "name": "乐鑫科技", "code": "688017", "reason": "AI芯片",
            "close": "234.50", "zhangdie": "3.50", "zhangfu": "1.52",
            "huanshou": "0.87", "chengjiaoe": "100234", "chengjiaoliang": "456",
            "ddejingliang": "12.3", "market": "sh",
        }
    ],
}


class TestGetHotStocks:
    @patch("astk.signals.hot_api.http_get")
    def test_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_HOT_RESPONSE
        mock_get.return_value = mock_resp

        df = get_hot_stocks("2025-01-15")
        assert isinstance(df, pd.DataFrame)
        assert "名称" in df.columns
        assert "代码" in df.columns
        assert df.iloc[0]["名称"] == "乐鑫科技"

    @patch("astk.signals.hot_api.http_get")
    def test_empty(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"errocode": 0, "data": []}
        mock_get.return_value = mock_resp

        df = get_hot_stocks("2025-01-15")
        assert df.empty

    @patch("astk.signals.hot_api.http_get")
    def test_api_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"errocode": 1, "errormsg": "forbidden"}
        mock_get.return_value = mock_resp

        with pytest.raises(RuntimeError, match="同花顺热点错误"):
            get_hot_stocks("2025-01-15")

    @patch("astk.signals.hot_api.http_get")
    def test_default_date_uses_today(self, mock_get):
        from datetime import date
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"errocode": 0, "data": []}
        mock_get.return_value = mock_resp

        get_hot_stocks()
        today_str = date.today().strftime("%Y-%m-%d")
        call_url = mock_get.call_args[0][0]
        assert today_str in call_url
