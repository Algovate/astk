"""估值流程: 单票完整估值 + 批量对比."""

from __future__ import annotations

import math
import urllib.request

import akshare as ak


def full_valuation(code: str) -> dict:
    """单票完整估值分析."""
    # 1. 腾讯实时行情
    prefix = "sh" if code.startswith(("6", "9")) else ("bj" if code.startswith("8") else "sz")
    url = f"https://qt.gtimg.cn/q={prefix}{code}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode("gbk")
    vals = data.split('"')[1].split("~")
    price = float(vals[3])
    mcap = float(vals[44])
    pe_ttm = float(vals[39]) if vals[39] else 0
    pb = float(vals[46]) if vals[46] else 0

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
    pe_fwd = price / eps_cur if eps_cur else float("inf")
    cagr = (eps_next / eps_cur - 1) if (eps_cur and eps_next) else 0
    peg = pe_fwd / (cagr * 100) if cagr > 0 else float("inf")
    digest = (
        math.log(pe_fwd / 30) / math.log(1 + cagr)
        if pe_fwd > 30 and cagr > 0 else 0
    )

    return {
        "name": vals[1],
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
