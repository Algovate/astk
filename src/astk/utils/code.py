"""Stock code normalization and validation."""

import re
from datetime import datetime

from astk.utils.errors import InvalidStockCodeError


def normalize_code(raw: str) -> str:
    """Normalize stock code to pure 6 digits.

    Supports: 688017, SH688017, sh688017, 688017.SH, 688017.sh, SZ000001, BJ832000
    """
    s = raw.strip().upper()
    # Strip exchange suffix: 688017.SH -> 688017
    s = re.sub(r"\.(SH|SZ|BJ)$", "", s)
    # Strip exchange prefix: SH688017 -> 688017
    s = re.sub(r"^(SH|SZ|BJ)", "", s)
    return s


def get_prefix(code: str) -> str:
    """6-digit code -> market prefix for Tencent/mootdx HTTP APIs."""
    if code.startswith(("6", "9")):
        return "sh"
    elif code.startswith("8"):
        return "bj"
    else:
        return "sz"


def get_mootdx_market(code: str) -> int:
    """6-digit code -> mootdx market number (0=深圳, 1=上海)."""
    if code.startswith(("6", "9")):
        return 1
    return 0


def get_cninfo_market(code: str) -> str:
    """6-digit code -> cninfo market name."""
    if code.startswith("6"):
        return "沪市"
    elif code.startswith("8"):
        return "北交所"
    else:
        return "深市"


def validate_code(raw: str) -> str:
    """Normalize and validate stock code. Raises InvalidStockCodeError on failure."""
    code = normalize_code(raw)
    if not re.match(r"^\d{6}$", code):
        raise InvalidStockCodeError(f"无效股票代码: {raw!r} (需要6位数字，如 688017)")
    return code


def validate_date(raw: str, fmt: str = "%Y-%m-%d") -> str:
    """Validate a date string format. Raises ValueError on failure.

    Returns the input string unchanged on success.
    """
    try:
        datetime.strptime(raw, fmt)
    except (ValueError, TypeError) as e:
        hint = fmt.replace("%Y", "YYYY").replace("%m", "MM").replace("%d", "DD")
        raise ValueError(f"无效日期: {raw!r} (需要 {hint} 格式，如 2025-01-15)") from e
    return raw
