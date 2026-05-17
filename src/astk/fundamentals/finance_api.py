"""mootdx 财务快照: 37字段季报数据."""

from __future__ import annotations

import pandas as pd

from astk.market.mootdx_api import _client


def get_finance_snapshot(symbol: str) -> pd.DataFrame:
    """获取37字段季报快照."""
    client = _client()
    df = client.finance(symbol=symbol)
    if df is None or df.empty:
        return pd.DataFrame()
    # Transpose to key-value format for display
    row = df.iloc[0]
    return pd.DataFrame({"字段": row.index, "值": row.values})
