"""Tests for astk.research.eastmoney_api — reports and PDF download."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from astk.research.eastmoney_api import download_pdf, eastmoney_reports


REPORT_RECORD = {
    "infoCode": "AN202501151234",
    "publishDate": "2025-01-15",
    "orgSName": "中信证券",
    "title": "乐鑫科技深度报告",
    "emRatingName": "买入",
}


class TestEastmoneyReports:
    @patch("astk.research.eastmoney_api.time.sleep")
    @patch("astk.research.eastmoney_api.http_get")
    def test_single_page(self, mock_get, mock_sleep):
        mock_get.return_value.json.return_value = {
            "data": [REPORT_RECORD],
            "TotalPage": 1,
        }

        result = eastmoney_reports("688017", max_pages=3)
        assert len(result) == 1
        assert result[0]["infoCode"] == "AN202501151234"

    @patch("astk.research.eastmoney_api.time.sleep")
    @patch("astk.research.eastmoney_api.http_get")
    def test_multi_page(self, mock_get, mock_sleep):
        rec2 = {**REPORT_RECORD, "infoCode": "AN202501151235"}
        mock_get.return_value.json.side_effect = [
            {"data": [REPORT_RECORD], "TotalPage": 2},
            {"data": [rec2], "TotalPage": 2},
        ]

        result = eastmoney_reports("688017", max_pages=5)
        assert len(result) == 2

    @patch("astk.research.eastmoney_api.http_get")
    def test_empty(self, mock_get):
        mock_get.return_value.json.return_value = {"data": []}

        result = eastmoney_reports("688017")
        assert result == []


class TestDownloadPdf:
    @patch("astk.research.eastmoney_api.get_session")
    def test_success(self, mock_gs, tmp_path):
        session = MagicMock()
        mock_gs.return_value = session
        session.get.return_value = MagicMock(status_code=200, content=b"x" * 2048)

        path = download_pdf(REPORT_RECORD, target_dir=str(tmp_path))
        assert path is not None
        assert path.endswith(".pdf")

    def test_no_info_code(self, tmp_path):
        result = download_pdf({"title": "no code"}, target_dir=str(tmp_path))
        assert result is None

    @patch("astk.research.eastmoney_api.get_session")
    def test_existing_file(self, mock_gs, tmp_path):
        # Pre-create the file
        from pathlib import Path
        fname = "2025-01-15_中信证券_乐鑫科技深度报告.pdf"
        (tmp_path / fname).write_bytes(b"existing")

        result = download_pdf(REPORT_RECORD, target_dir=str(tmp_path))
        assert result is not None
        session = mock_gs.return_value
        session.get.assert_not_called()

    @patch("astk.research.eastmoney_api.get_session")
    def test_too_small(self, mock_gs, tmp_path):
        session = MagicMock()
        mock_gs.return_value = session
        session.get.return_value = MagicMock(status_code=200, content=b"tiny")

        result = download_pdf(REPORT_RECORD, target_dir=str(tmp_path))
        assert result is None
