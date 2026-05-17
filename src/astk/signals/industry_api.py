"""行业横向对比: 同花顺90行业涨跌排名."""

from __future__ import annotations

import os

import akshare as ak


def get_industry_comparison(top_n: int = 20) -> dict:
    """全行业涨跌幅排名（同花顺~90个行业）."""
    prev = os.environ.get("TQDM_DISABLE", "")
    os.environ["TQDM_DISABLE"] = "1"
    try:
        df = ak.stock_board_industry_summary_ths()
    finally:
        if prev:
            os.environ["TQDM_DISABLE"] = prev
        else:
            os.environ.pop("TQDM_DISABLE", None)

    if df.empty:
        return {"top": [], "bottom": [], "total": 0}

    rows: list[dict] = []
    for i, row in df.iterrows():
        rows.append({
            "rank": i + 1,
            "name": row.get("板块", ""),
            "change_pct": row.get("涨跌幅", 0),
            "turnover_yi": row.get("总成交额", 0),
            "net_inflow_yi": row.get("净流入", 0) if "净流入" in df.columns else None,
            "up_count": row.get("上涨家数", 0),
            "down_count": row.get("下跌家数", 0),
            "leader": row.get("领涨股", ""),
        })

    return {
        "top": rows[:top_n],
        "bottom": rows[-top_n:],
        "total": len(rows),
    }
