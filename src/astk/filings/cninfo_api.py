"""公告层: 巨潮cninfo公告."""

from __future__ import annotations

import pandas as pd
import akshare as ak


def get_filings(symbol: str, market: str = "沪市") -> pd.DataFrame:
    """获取巨潮公告列表.

    market: "沪市" / "深市" / "北交所"
    """
    df = ak.stock_zh_a_disclosure_report_cninfo(symbol=symbol, market=market)
    return df
