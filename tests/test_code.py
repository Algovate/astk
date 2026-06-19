"""Tests for astk.utils.code — stock code normalization and validation."""

from __future__ import annotations

import pytest

from astk.utils.code import (
    get_cninfo_market,
    get_mootdx_market,
    get_prefix,
    normalize_code,
    validate_code,
    validate_date,
)
from astk.utils.errors import InvalidStockCodeError


# ── normalize_code ───────────────────────────────────────────


class TestNormalizeCode:
    def test_sh_prefix(self):
        assert normalize_code("SH688017") == "688017"

    def test_sz_prefix_lowercase(self):
        assert normalize_code("sz000001") == "000001"

    def test_bj_prefix(self):
        assert normalize_code("BJ832000") == "832000"

    def test_sh_suffix(self):
        assert normalize_code("688017.SH") == "688017"

    def test_sz_suffix(self):
        assert normalize_code("000001.SZ") == "000001"

    def test_bj_suffix(self):
        assert normalize_code("832000.BJ") == "832000"

    def test_already_pure(self):
        assert normalize_code("688017") == "688017"

    def test_whitespace(self):
        assert normalize_code(" 688017 ") == "688017"

    def test_suffix_lowercase(self):
        assert normalize_code("688017.sh") == "688017"


# ── get_prefix ───────────────────────────────────────────────


class TestGetPrefix:
    @pytest.mark.parametrize("code", ["688017", "600519", "900901"])
    def test_shanghai(self, code):
        assert get_prefix(code) == "sh"

    @pytest.mark.parametrize("code", ["000001", "300476", "002463"])
    def test_shenzhen(self, code):
        assert get_prefix(code) == "sz"

    def test_beijing(self):
        assert get_prefix("832000") == "bj"


# ── get_mootdx_market ────────────────────────────────────────


class TestGetMootdxMarket:
    def test_shanghai(self):
        assert get_mootdx_market("688017") == 1

    def test_shanghai_9(self):
        assert get_mootdx_market("900901") == 1

    def test_shenzhen(self):
        assert get_mootdx_market("000001") == 0

    def test_chinext(self):
        assert get_mootdx_market("300476") == 0

    def test_beijing(self):
        assert get_mootdx_market("832000") == 0


# ── get_cninfo_market ────────────────────────────────────────


class TestGetCninfoMarket:
    def test_shanghai(self):
        assert get_cninfo_market("600519") == "沪市"

    def test_shenzhen(self):
        assert get_cninfo_market("000001") == "深市"

    def test_beijing(self):
        assert get_cninfo_market("832000") == "北交所"


# ── validate_code ────────────────────────────────────────────


class TestValidateCode:
    def test_valid_pure(self):
        assert validate_code("688017") == "688017"

    def test_valid_with_prefix(self):
        assert validate_code("SH688017") == "688017"

    def test_valid_with_suffix(self):
        assert validate_code("688017.SH") == "688017"

    def test_invalid_letters(self):
        with pytest.raises(InvalidStockCodeError, match="无效股票代码"):
            validate_code("abc")

    def test_invalid_short(self):
        with pytest.raises(InvalidStockCodeError, match="无效股票代码"):
            validate_code("123")

    def test_invalid_empty(self):
        with pytest.raises(InvalidStockCodeError, match="无效股票代码"):
            validate_code("")

    def test_invalid_too_long(self):
        with pytest.raises(InvalidStockCodeError, match="无效股票代码"):
            validate_code("1234567")

    def test_raises_specific_exception(self):
        # Tightens: must be InvalidStockCodeError, not a bare ValueError
        with pytest.raises(InvalidStockCodeError):
            validate_code("abc")
        assert not issubclass(InvalidStockCodeError, ValueError)


# ── validate_date ────────────────────────────────────────────


class TestValidateDate:
    def test_valid_iso(self):
        assert validate_date("2025-01-15") == "2025-01-15"

    def test_valid_pads(self):
        assert validate_date("2025-12-31") == "2025-12-31"

    def test_invalid_month(self):
        with pytest.raises(ValueError, match="无效日期"):
            validate_date("2025-13-01")

    def test_invalid_day(self):
        with pytest.raises(ValueError, match="无效日期"):
            validate_date("2025-01-32")

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="无效日期"):
            validate_date("20250115")

    def test_invalid_garbage(self):
        with pytest.raises(ValueError, match="无效日期"):
            validate_date("not-a-date")
