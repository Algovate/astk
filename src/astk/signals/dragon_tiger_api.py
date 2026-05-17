"""龙虎榜: 个股席位 + 全市场龙虎榜."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import akshare as ak

from astk.utils.http import http_get

logger = logging.getLogger(__name__)

_DC_HEADERS = {"Referer": "https://data.eastmoney.com/"}


def get_dragon_tiger(code: str, trade_date: str, look_back: int = 30) -> dict:
    """龙虎榜数据聚合 (个股维度).

    trade_date: YYYY-MM-DD
    """
    start = datetime.strptime(trade_date, "%Y-%m-%d") - timedelta(days=look_back)
    start_str = start.strftime("%Y%m%d")
    end_str = trade_date.replace("-", "")

    # 1. 上榜记录
    records: list[dict] = []
    try:
        df = ak.stock_lhb_detail_em(start_date=start_str, end_date=end_str)
        if not df.empty:
            df_stock = df[df["代码"] == code]
            for _, row in df_stock.iterrows():
                records.append({
                    "date": str(row.get("日期", "")),
                    "reason": row.get("解读", ""),
                    "net_buy": row.get("龙虎榜净买额", 0),
                    "turnover": row.get("换手率", 0),
                })
    except Exception as e:
        logger.warning("龙虎榜上榜记录获取失败: %s", e)

    # 2. 买卖席位
    seats: dict[str, list[dict]] = {"buy": [], "sell": []}
    if records:
        latest_date = records[0]["date"].replace("-", "")[:8]
        for flag, key in [("买入", "buy"), ("卖出", "sell")]:
            try:
                df_detail = ak.stock_lhb_stock_detail_em(symbol=code, date=latest_date, flag=flag)
                if not df_detail.empty:
                    for _, row in df_detail.head(5).iterrows():
                        seats[key].append({
                            "name": row.get("营业部名称", ""),
                            "buy_amt": row.get("买入额", 0),
                            "sell_amt": row.get("卖出额", 0),
                            "net": row.get("净额", 0),
                        })
            except Exception as e:
                logger.warning("龙虎榜席位数据获取失败 (%s): %s", flag, e)

    # 3. 机构统计
    institution: dict = {}
    try:
        df_inst = ak.stock_lhb_jgmmtj_em(symbol=code)
        if not df_inst.empty:
            row = df_inst.iloc[0]
            institution = {
                "buy_count": row.get("买入机构数", 0),
                "sell_count": row.get("卖出机构数", 0),
                "net_amount": row.get("机构净买入额", 0),
            }
    except Exception as e:
        logger.warning("龙虎榜机构统计获取失败: %s", e)

    return {"records": records, "seats": seats, "institution": institution}


def get_daily_dragon_tiger(trade_date: str, min_net_buy: float | None = None) -> dict:
    """全市场龙虎榜 (东财datacenter直连).

    trade_date: YYYY-MM-DD
    """
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {
        "reportName": "RPT_DAILYBILLBOARD_DETAILSNEW",
        "columns": "ALL",
        "filter": f"(TRADE_DATE>='{trade_date}')(TRADE_DATE<='{trade_date}')",
        "pageNumber": "1",
        "pageSize": "500",
        "sortTypes": "-1",
        "sortColumns": "BILLBOARD_NET_AMT",
        "source": "WEB",
        "client": "WEB",
    }
    r = http_get(url, params=params, headers=_DC_HEADERS, timeout=15)
    d = r.json()
    if not d.get("success") or not d.get("result") or not d["result"].get("data"):
        return {
            "date": trade_date,
            "total_records": 0,
            "stocks": [],
            "note": "无数据（非交易日或盘后未更新）",
        }
    data = d["result"]["data"]
    actual_date = data[0].get("TRADE_DATE", "")[:10] if data else trade_date
    stocks: list[dict] = []
    for row in data:
        net_buy = (row.get("BILLBOARD_NET_AMT") or 0) / 10000
        if min_net_buy is not None and net_buy < min_net_buy:
            continue
        stocks.append({
            "code": row.get("SECURITY_CODE", ""),
            "name": row.get("SECURITY_NAME_ABBR", ""),
            "reason": row.get("EXPLANATION", ""),
            "close": row.get("CLOSE_PRICE") or 0,
            "change_pct": round(float(row.get("CHANGE_RATE") or 0), 2),
            "net_buy_wan": round(net_buy, 1),
            "buy_wan": round((row.get("BILLBOARD_BUY_AMT") or 0) / 10000, 1),
            "sell_wan": round((row.get("BILLBOARD_SELL_AMT") or 0) / 10000, 1),
            "turnover_pct": round(float(row.get("TURNOVERRATE") or 0), 2),
        })
    return {"date": actual_date, "total_records": len(stocks), "stocks": stocks}
