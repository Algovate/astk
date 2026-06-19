"""mootdx TCP行情: K线 + 五档盘口 + 逐笔成交."""

from __future__ import annotations

import functools

import pandas as pd
from mootdx.quotes import Quotes

from astk.utils.code import get_mootdx_market


@functools.lru_cache(maxsize=1)
def get_client() -> Quotes:
    """Return a shared mootdx Quotes client (cached singleton)."""
    return Quotes.factory(market="std")


def get_kline(symbol: str, category: int = 4, offset: int = 50) -> pd.DataFrame:
    """K线数据.

    category: 4=日线 5=周线 6=月线 7=1分钟 8=5分钟 9=15分钟 10=30分钟 11=60分钟
    """
    client = get_client()
    df = client.bars(symbol=symbol, category=category, offset=offset)
    if df is None or df.empty:
        return pd.DataFrame()
    return df.reset_index()


def get_quotes(symbols: list[str]) -> pd.DataFrame:
    """实时报价 (五档盘口 + 价格)."""
    client = get_client()
    df = client.quotes(symbol=symbols)
    if df is None or df.empty:
        return pd.DataFrame()
    return df.reset_index()


def get_ticks(symbol: str, date: str | None = None) -> pd.DataFrame:
    """逐笔成交. date: YYYYMMDD 格式."""
    client = get_client()
    df = client.transaction(symbol=symbol, date=date) if date else client.transaction(symbol=symbol)
    if df is None or df.empty:
        return pd.DataFrame()
    return df.reset_index()
