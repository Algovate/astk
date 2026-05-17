"""akshare 机构一致预期EPS."""

from __future__ import annotations

import pandas as pd
import akshare as ak


def get_consensus_eps(symbol: str) -> pd.DataFrame:
    """获取机构一致预期EPS."""
    df = ak.stock_profit_forecast_ths(symbol=symbol, indicator="预测年报每股收益")
    return df
