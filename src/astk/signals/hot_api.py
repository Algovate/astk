"""同花顺强势股 + 题材归因 reason tags."""

from __future__ import annotations

from datetime import date as _date

import pandas as pd

from astk.utils.http import http_get

_HOT_HEADERS = {
    "Host": "zx.10jqka.com.cn",
    "Referer": "https://zx.10jqka.com.cn/",
}


def get_hot_stocks(date_str: str | None = None) -> pd.DataFrame:
    """同花顺当日强势股归因.

    date_str: YYYY-MM-DD, None=今天
    """
    if date_str is None:
        date_str = _date.today().strftime("%Y-%m-%d")

    url = (
        f"https://zx.10jqka.com.cn/event/api/getharden/"
        f"date/{date_str}/orderby/date/orderway/desc/charset/GBK/"
    )
    r = http_get(url, headers=_HOT_HEADERS, timeout=10)
    data = r.json()
    if data.get("errocode", 0) != 0:
        raise RuntimeError(f"同花顺热点错误: {data.get('errormsg', '')}")

    rows = data.get("data") or []
    df = pd.DataFrame(rows)
    if df.empty:
        return df

    rename_map = {
        "name": "名称", "code": "代码", "reason": "题材归因",
        "close": "收盘价", "zhangdie": "涨跌额", "zhangfu": "涨幅%",
        "huanshou": "换手率%", "chengjiaoe": "成交额",
        "chengjiaoliang": "成交量", "ddejingliang": "大单净量",
        "market": "市场",
    }
    df = df.rename(columns=rename_map)
    return df
