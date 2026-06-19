"""Tests for astk.flows.valuation — full_valuation math and edge cases."""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest

from astk.flows.valuation import full_valuation
from astk.utils.errors import DataSourceError


_QUOTE = {
    "688017": {
        "name": "乐鑫科技",
        "price": 100.0,
        "mcap_yi": 200.0,
        "pe_ttm": 25.0,
        "pb": 3.0,
    }
}


def _forecast(df):
    """Patch helper: returns a patcher for astk.flows.valuation.ak."""
    patcher = patch("astk.flows.valuation.ak")
    mock_ak = patcher.start()
    mock_ak.stock_profit_forecast_ths.return_value = df
    return patcher


class TestFullValuation:
    @patch("astk.flows.valuation.tencent_quote", return_value=_QUOTE)
    def test_math_success(self, _mock_q):
        df = pd.DataFrame({
            "年度": [2025, 2026],
            "均值": [4.0, 5.0],
            "预测机构数": [10, 12],
        })
        patcher = _forecast(df)
        try:
            r = full_valuation("688017")
        finally:
            patcher.stop()

        assert r["name"] == "乐鑫科技"
        assert r["eps_cur"] == 4.0
        assert r["eps_next"] == 5.0
        assert r["pe_fwd"] == 25.0       # 100 / 4.0
        assert r["cagr_pct"] == 25.0     # (5/4 - 1) * 100
        assert r["peg"] == 1.0           # 25 / (0.25 * 100)
        assert r["digest_years"] == 0.0  # pe_fwd not > 30
        assert r["analyst_count"] == 10

    @patch("astk.flows.valuation.tencent_quote", return_value=_QUOTE)
    def test_empty_forecast_no_crash(self, _mock_q):
        # Stock with no analyst coverage — previously raised KeyError
        patcher = _forecast(pd.DataFrame())
        try:
            r = full_valuation("688017")
        finally:
            patcher.stop()

        assert r["eps_cur"] is None
        assert r["eps_next"] is None
        assert r["pe_fwd"] is None
        assert r["peg"] is None
        assert r["analyst_count"] == 0

    @patch("astk.flows.valuation.tencent_quote", return_value=_QUOTE)
    def test_forecast_missing_column_no_crash(self, _mock_q):
        # akshare schema drift — column renamed/absent
        patcher = _forecast(pd.DataFrame({"foo": [1]}))
        try:
            r = full_valuation("688017")
        finally:
            patcher.stop()

        assert r["eps_cur"] is None
        assert r["analyst_count"] == 0

    @patch("astk.flows.valuation.tencent_quote", return_value=_QUOTE)
    def test_single_year_forecast(self, _mock_q):
        df = pd.DataFrame({"年度": [2025], "均值": [4.0], "预测机构数": [10]})
        patcher = _forecast(df)
        try:
            r = full_valuation("688017")
        finally:
            patcher.stop()

        assert r["eps_cur"] == 4.0
        assert r["eps_next"] is None
        assert r["pe_fwd"] == 25.0
        assert r["peg"] is None  # no growth rate without eps_next

    @patch("astk.flows.valuation.tencent_quote", return_value={})
    def test_missing_quote_raises(self, _mock_q):
        patcher = _forecast(pd.DataFrame())
        try:
            with pytest.raises(DataSourceError, match="腾讯行情数据未返回"):
                full_valuation("688017")
        finally:
            patcher.stop()

    @patch("astk.flows.valuation.tencent_quote", return_value=_QUOTE)
    def test_akshare_forecast_failure_no_crash(self, _mock_q):
        # akshare network/parse error is logged, not raised
        patcher = patch("astk.flows.valuation.ak")
        mock_ak = patcher.start()
        mock_ak.stock_profit_forecast_ths.side_effect = RuntimeError("upstream")
        try:
            r = full_valuation("688017")
        finally:
            patcher.stop()

        assert r["eps_cur"] is None
        assert r["name"] == "乐鑫科技"  # quote still returned
