"""同花顺北向资金: hsgtApi实时分钟流向."""

from __future__ import annotations

import pandas as pd

from astk.utils.http import http_get

HSGT_HEADERS = {
    "Host": "data.hexin.cn",
    "Referer": "https://data.hexin.cn/",
}


def get_northbound_realtime() -> pd.DataFrame:
    """沪深股通当日实时分钟流向."""
    url = "https://data.hexin.cn/market/hsgtApi/method/dayChart/"
    r = http_get(url, headers=HSGT_HEADERS, timeout=10)
    d = r.json()
    times = d.get("time", [])
    hgt = d.get("hgt", [])
    sgt = d.get("sgt", [])

    n = len(times)

    def _pad(vals: list) -> list:
        return (vals + [None] * n)[:n]

    return pd.DataFrame({
        "time": times,
        "hgt_yi": _pad(hgt),
        "sgt_yi": _pad(sgt),
    })
