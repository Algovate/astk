"""限售解禁日历."""

from __future__ import annotations

import logging

import akshare as ak

logger = logging.getLogger(__name__)


def get_lockup_expiry(code: str, trade_date: str, forward_days: int = 90) -> dict:
    """限售解禁日历.

    trade_date: YYYY-MM-DD
    返回: {history: [...], upcoming: [...]}
    """
    # 1. 历史解禁
    history: list[dict] = []
    try:
        df = ak.stock_restricted_release_queue_em(symbol=code)
        if not df.empty:
            for _, row in df.head(15).iterrows():
                history.append({
                    "date": str(row.get("解禁时间", "")),
                    "type": row.get("限售股类型", ""),
                    "shares": row.get("解禁数量", 0),
                    "ratio": row.get("实际解禁市值占总市值比例", 0),
                })
    except Exception as e:
        logger.warning("历史解禁数据获取失败: %s", e)

    # 2. 未来待解禁
    upcoming: list[dict] = []
    today_str = trade_date.replace("-", "")
    try:
        df = ak.stock_restricted_release_detail_em(date=today_str)
        if not df.empty:
            df_stock = df[df["股票代码"] == code]
            for _, row in df_stock.iterrows():
                upcoming.append({
                    "date": str(row.get("解禁日期", "")),
                    "type": row.get("限售股类型", ""),
                    "shares": row.get("解禁数量", 0),
                    "float_ratio": row.get("占流通股比例", 0),
                })
    except Exception as e:
        logger.warning("待解禁数据获取失败: %s", e)

    return {"history": history, "upcoming": upcoming}
