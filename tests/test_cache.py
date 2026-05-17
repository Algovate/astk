"""Tests for astk.utils.cache — file-based northbound data cache."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from astk.utils.cache import (
    load_northbound_history,
    northbound_cache_path,
    save_northbound_snapshot,
)


@pytest.fixture
def cache_tmp(tmp_path):
    """Provide a temp cache dir, patching cache_dir()."""
    d = tmp_path / ".astk" / "cache"
    d.mkdir(parents=True)
    with patch("astk.utils.cache.cache_dir", return_value=d):
        yield d


class TestCacheDir:
    def test_creates_directory(self, cache_tmp):
        assert cache_tmp.exists()


class TestNorthboundCachePath:
    def test_returns_csv_path(self, cache_tmp):
        path = northbound_cache_path()
        # Since we patched cache_dir, this should use it
        assert path.name == "northbound_daily.csv"
        assert str(cache_tmp) in str(path)


class TestSaveNorthboundSnapshot:
    def test_creates_csv(self, cache_tmp):
        save_northbound_snapshot("2025-01-15", 12.3, 8.1)
        csv_path = cache_tmp / "northbound_daily.csv"
        assert csv_path.exists()
        content = csv_path.read_text()
        assert "date,hgt_yi,sgt_yi" in content
        assert "2025-01-15,12.3,8.1" in content

    def test_upsert_same_date(self, cache_tmp):
        save_northbound_snapshot("2025-01-15", 12.3, 8.1)
        save_northbound_snapshot("2025-01-15", 15.0, 9.0)
        csv_path = cache_tmp / "northbound_daily.csv"
        lines = csv_path.read_text().strip().split("\n")
        assert len(lines) == 2  # header + 1 data row
        assert "2025-01-15,15.0,9.0" in lines[1]

    def test_multiple_dates_sorted(self, cache_tmp):
        save_northbound_snapshot("2025-01-17", 1.0, 2.0)
        save_northbound_snapshot("2025-01-15", 3.0, 4.0)
        save_northbound_snapshot("2025-01-16", 5.0, 6.0)
        lines = (cache_tmp / "northbound_daily.csv").read_text().strip().split("\n")
        assert lines[1].startswith("2025-01-15")
        assert lines[2].startswith("2025-01-16")
        assert lines[3].startswith("2025-01-17")

    def test_no_tmp_file_left(self, cache_tmp):
        save_northbound_snapshot("2025-01-15", 1.0, 2.0)
        assert not list(cache_tmp.glob("*.tmp"))


class TestLoadNorthboundHistory:
    def test_returns_dataframe(self, cache_tmp):
        save_northbound_snapshot("2025-01-15", 12.3, 8.1)
        df = load_northbound_history(10)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.iloc[0]["hgt_yi"] == 12.3

    def test_tail_n(self, cache_tmp):
        for i in range(10):
            save_northbound_snapshot(f"2025-01-{i+10:02d}", float(i), float(i))
        df = load_northbound_history(5)
        assert len(df) == 5
        assert df.iloc[0]["date"] == "2025-01-15"

    def test_missing_file(self, tmp_path):
        empty_cache = tmp_path / "empty"
        empty_cache.mkdir()
        with patch("astk.utils.cache.cache_dir", return_value=empty_cache):
            df = load_northbound_history(10)
        assert isinstance(df, pd.DataFrame)
        assert df.empty
