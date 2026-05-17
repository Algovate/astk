"""Tests for astk.market.tencent_api — tencent_quote GBK parsing."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from astk.market.tencent_api import tencent_quote


def _build_tencent_line(code: str, market: str, name: str = "测试股", price: float = 100.0) -> str:
    """Build a fake Tencent API response line with ~54 fields."""
    fields = [""] * 54
    fields[0] = "1"          # market
    fields[1] = name         # name
    fields[2] = code         # code
    fields[3] = str(price)   # price
    fields[4] = "98.0"       # last_close
    fields[5] = "99.0"       # open
    fields[31] = "2.0"       # change_amt
    fields[32] = "2.04"      # change_pct
    fields[33] = "102.0"     # high
    fields[34] = "97.0"      # low
    fields[37] = "50000"     # amount_wan
    fields[38] = "1.5"       # turnover_pct
    fields[39] = "25.0"      # pe_ttm
    fields[43] = "5.0"       # amplitude_pct
    fields[44] = "200.0"     # mcap_yi
    fields[45] = "150.0"     # float_mcap_yi
    fields[46] = "3.5"       # pb
    fields[47] = "110.0"     # limit_up
    fields[48] = "90.0"      # limit_down
    fields[49] = "1.2"       # vol_ratio
    fields[52] = "22.0"      # pe_static
    return f"v_{market}{code}=\"{'~'.join(fields)}\";"


class TestTencentQuote:
    @patch("astk.market.tencent_api.http_get")
    def test_single_shanghai(self, mock_get):
        line = _build_tencent_line("688017", "sh", "乐鑫科技", 234.5)
        mock_resp = MagicMock()
        mock_resp.content = line.encode("gbk")
        mock_get.return_value = mock_resp

        result = tencent_quote(["688017"])
        assert "688017" in result
        assert result["688017"]["name"] == "乐鑫科技"
        assert result["688017"]["price"] == 234.5
        assert result["688017"]["pe_ttm"] == 25.0

    @patch("astk.market.tencent_api.http_get")
    def test_multiple_codes(self, mock_get):
        line1 = _build_tencent_line("688017", "sh", "A", 100.0)
        line2 = _build_tencent_line("000001", "sz", "B", 200.0)
        mock_resp = MagicMock()
        mock_resp.content = (line1 + line2).encode("gbk")
        mock_get.return_value = mock_resp

        result = tencent_quote(["688017", "000001"])
        assert len(result) == 2
        assert "688017" in result
        assert "000001" in result

    @patch("astk.market.tencent_api.http_get")
    def test_empty_response(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = b""
        mock_get.return_value = mock_resp

        result = tencent_quote(["688017"])
        assert result == {}

    @patch("astk.market.tencent_api.http_get")
    def test_short_line_skipped(self, mock_get):
        # Line with fewer than 53 tilde fields
        mock_resp = MagicMock()
        mock_resp.content = b'v_sh688017="1~short~data";'
        mock_get.return_value = mock_resp

        result = tencent_quote(["688017"])
        assert result == {}
