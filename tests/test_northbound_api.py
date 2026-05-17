"""Tests for astk.signals.northbound_api — get_northbound_realtime."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from astk.signals.northbound_api import get_northbound_realtime


class TestGetNorthboundRealtime:
    @patch("astk.signals.northbound_api.http_get")
    def test_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "time": ["09:30", "09:31", "09:32"],
            "hgt": [12.3, 13.5, 14.1],
            "sgt": [8.1, 7.9, 8.5],
        }
        mock_get.return_value = mock_resp

        df = get_northbound_realtime()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ["time", "hgt_yi", "sgt_yi"]

    @patch("astk.signals.northbound_api.http_get")
    def test_pads_shorter_hgt(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "time": ["09:30", "09:31", "09:32"],
            "hgt": [12.3],
            "sgt": [8.1, 7.9, 8.5],
        }
        mock_get.return_value = mock_resp

        df = get_northbound_realtime()
        assert len(df) == 3
        import math
        assert math.isnan(df.iloc[1]["hgt_yi"])

    @patch("astk.signals.northbound_api.http_get")
    def test_empty(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"time": [], "hgt": [], "sgt": []}
        mock_get.return_value = mock_resp

        df = get_northbound_realtime()
        assert len(df) == 0
