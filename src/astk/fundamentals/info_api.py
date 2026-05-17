"""akshare 个股基本面."""

from __future__ import annotations

import pandas as pd
import akshare as ak


def get_stock_info(symbol: str) -> pd.DataFrame:
    """获取个股基本面信息."""
    df = ak.stock_individual_info_em(symbol=symbol)
    return df
