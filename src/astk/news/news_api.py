"""新闻层: 个股新闻 + 财联社快讯 + 全球资讯."""

from __future__ import annotations

import pandas as pd
import akshare as ak


def get_stock_news(symbol: str) -> pd.DataFrame:
    """个股新闻 (东财)."""
    df = ak.stock_news_em(symbol=symbol)
    return df


def get_cls_flash() -> pd.DataFrame:
    """财联社快讯."""
    df = ak.stock_info_global_cls()
    return df


def get_global_news() -> pd.DataFrame:
    """东财全球资讯."""
    df = ak.stock_info_global_em()
    return df
