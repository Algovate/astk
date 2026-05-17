"""Tests for astk.signals.dragon_tiger_api."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from astk.signals.dragon_tiger_api import get_daily_dragon_tiger, get_dragon_tiger


MOCK_DAILY_RESPONSE = {
    "success": True,
    "result": {
        "data": [
            {
                "TRADE_DATE": "2025-01-15 00:00:00",
                "SECURITY_CODE": "688017",
                "SECURITY_NAME_ABBR": "乐鑫科技",
                "EXPLANATION": "涨幅偏离",
                "CLOSE_PRICE": 234.5,
                "CHANGE_RATE": 10.52,
                "BILLBOARD_NET_AMT": 50000000,
                "BILLBOARD_BUY_AMT": 80000000,
                "BILLBOARD_SELL_AMT": 30000000,
                "TURNOVERRATE": 5.23,
            }
        ]
    },
}


class TestGetDailyDragonTiger:
    @patch("astk.signals.dragon_tiger_api.http_get")
    def test_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_DAILY_RESPONSE
        mock_get.return_value = mock_resp

        result = get_daily_dragon_tiger("2025-01-15")
        assert result["date"] == "2025-01-15"
        assert result["total_records"] == 1
        assert result["stocks"][0]["code"] == "688017"
        assert result["stocks"][0]["net_buy_wan"] == 5000.0

    @patch("astk.signals.dragon_tiger_api.http_get")
    def test_no_data(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"success": False}
        mock_get.return_value = mock_resp

        result = get_daily_dragon_tiger("2025-01-15")
        assert result["total_records"] == 0
        assert "note" in result

    @patch("astk.signals.dragon_tiger_api.http_get")
    def test_min_net_buy_filter(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_DAILY_RESPONSE
        mock_get.return_value = mock_resp

        result = get_daily_dragon_tiger("2025-01-15", min_net_buy=6000.0)
        assert result["total_records"] == 0  # 5000 < 6000

    @patch("astk.signals.dragon_tiger_api.http_get")
    def test_min_net_buy_passes(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = MOCK_DAILY_RESPONSE
        mock_get.return_value = mock_resp

        result = get_daily_dragon_tiger("2025-01-15", min_net_buy=4000.0)
        assert result["total_records"] == 1


class TestGetDragonTiger:
    @patch("astk.signals.dragon_tiger_api.ak")
    def test_success(self, mock_ak):
        mock_ak.stock_lhb_detail_em.return_value = pd.DataFrame({
            "代码": ["688017"],
            "日期": ["2025-01-15"],
            "解读": ["涨幅偏离"],
            "龙虎榜净买额": [5000],
            "换手率": [5.2],
        })
        mock_ak.stock_lhb_stock_detail_em.return_value = pd.DataFrame()
        mock_ak.stock_lhb_jgmmtj_em.return_value = pd.DataFrame()

        result = get_dragon_tiger("688017", "2025-01-15")
        assert len(result["records"]) == 1
        assert result["records"][0]["net_buy"] == 5000

    @patch("astk.signals.dragon_tiger_api.ak")
    def test_akshare_failure_graceful(self, mock_ak):
        mock_ak.stock_lhb_detail_em.side_effect = Exception("network error")
        mock_ak.stock_lhb_jgmmtj_em.side_effect = Exception("network error")

        result = get_dragon_tiger("688017", "2025-01-15")
        assert result["records"] == []
        assert result["institution"] == {}
