"""估值流程: 单票完整估值 + 批量对比."""

from __future__ import annotations

import math

import akshare as ak

from astk.market.tencent_api import tencent_quote
from astk.utils.errors import DataSourceError


def full_valuation(code: str) -> dict:
    """单票完整估值分析."""
    # 1. 腾讯实时行情
    quotes = tencent_quote([code])
    if code not in quotes:
        raise DataSourceError(f"腾讯行情数据未返回: {code}")
    q = quotes[code]
    price = q["price"]
    mcap = q["mcap_yi"]
    pe_ttm = q["pe_ttm"]
    pb = q["pb"]
    name = q["name"]

    # 2. 机构一致预期
    df = ak.stock_profit_forecast_ths(symbol=code, indicator="预测年报每股收益")
    eps_cur = eps_next = None
    analyst_count = 0
    years_sorted = sorted(df["年度"].unique())
    for _, row in df.iterrows():
        y = str(row["年度"])
        if len(years_sorted) > 0 and y == str(years_sorted[0]):
            eps_cur = float(row["均值"])
            analyst_count = int(row["预测机构数"])
        elif len(years_sorted) > 1 and y == str(years_sorted[1]):
            eps_next = float(row["均值"])

    # 3. 估值指标
    pe_fwd = price / eps_cur if eps_cur and eps_cur > 0 else float("inf")
    cagr = (eps_next / eps_cur - 1) if (eps_cur and eps_cur > 0 and eps_next) else 0
    peg = pe_fwd / (cagr * 100) if cagr > 0 else float("inf")
    digest = (
        math.log(pe_fwd / 30) / math.log(1 + cagr)
        if pe_fwd > 30 and cagr > 0 else 0
    )

    return {
        "name": name,
        "code": code,
        "price": price,
        "mcap_yi": mcap,
        "pe_ttm": pe_ttm,
        "pb": pb,
        "eps_cur": eps_cur,
        "eps_next": eps_next,
        "pe_fwd": round(pe_fwd, 1) if eps_cur else None,
        "cagr_pct": round(cagr * 100, 0) if cagr else None,
        "peg": round(peg, 2) if peg != float("inf") else None,
        "digest_years": round(digest, 1),
        "analyst_count": analyst_count,
    }
