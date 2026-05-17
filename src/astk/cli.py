"""astk CLI — A股全栈数据工具."""

from __future__ import annotations

from datetime import date
from typing import Annotated, Optional

import typer

from astk import __version__
from astk.utils.output import OutputFormat

app = typer.Typer(
    name="astk",
    help="A股全栈数据工具 — 行情/研报/信号/新闻/基础数据/公告",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Subcommand groups
report_app = typer.Typer(help="研报相关命令")
filing_app = typer.Typer(help="公告相关命令")
app.add_typer(report_app, name="report")
app.add_typer(filing_app, name="filing")

# Global output format, stored in context
_output_format = OutputFormat.table


def _get_output() -> OutputFormat:
    return _output_format


def _version_callback(value: bool):
    if value:
        typer.echo(f"astk {__version__}")
        raise typer.Exit()


@app.callback()
def global_options(
    output: OutputFormat = typer.Option(
        OutputFormat.table,
        "--output",
        "-o",
        help="输出格式: table, json, csv",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        is_eager=True,
        callback=_version_callback,
        help="显示版本号",
    ),
):
    """A股全栈数据工具."""
    global _output_format
    _output_format = output


# ── Layer 1: Market ──────────────────────────────────────────


@app.command()
def quote(
    code: Annotated[str, typer.Argument(help="股票代码，如 688017")],
):
    """实时行情 (mootdx + 腾讯合并)."""
    from astk.market.mootdx_api import get_quotes
    from astk.market.tencent_api import tencent_quote
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        c = normalize_code(code)
        tencent = tencent_quote([c])
        mootdx = get_quotes([c])
        merged = {}
        if c in tencent:
            merged.update(tencent[c])
        if not mootdx.empty:
            merged["mootdx_price"] = mootdx.iloc[0].get("price", "")
        render(merged, _get_output(), title=f"{code} 实时行情")

    _run()


@app.command()
def kline(
    code: Annotated[str, typer.Argument(help="股票代码")],
    period: Annotated[str, typer.Option("--period", "-p", help="K线周期: day/week/month/1m/5m/15m/30m/60m")] = "day",
    limit: Annotated[int, typer.Option("--limit", "-n", help="返回条数")] = 50,
):
    """K线数据."""
    from astk.market.mootdx_api import get_kline
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    period_map = {
        "day": 4, "week": 5, "month": 6,
        "1m": 7, "5m": 8, "15m": 9, "30m": 10, "60m": 11,
    }

    @handle_errors
    def _run():
        c = normalize_code(code)
        cat = period_map.get(period, 4)
        df = get_kline(c, category=cat, offset=limit)
        render(df, _get_output(), title=f"{code} K线 ({period})")

    _run()


@app.command()
def orderbook(
    code: Annotated[str, typer.Argument(help="股票代码")],
):
    """五档盘口."""
    from astk.market.mootdx_api import get_quotes
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        c = normalize_code(code)
        df = get_quotes([c])
        if df.empty:
            from astk.utils.errors import DataUnavailableError
            raise DataUnavailableError("无盘口数据")
        row = df.iloc[0]
        bids, asks = [], []
        for i in range(1, 6):
            bids.append({"level": f"买{i}", "price": row.get(f"bid{i}", ""), "vol": row.get(f"bid_vol{i}", "")})
            asks.append({"level": f"卖{i}", "price": row.get(f"ask{i}", ""), "vol": row.get(f"ask_vol{i}", "")})
        render(asks[::-1] + bids, _get_output(), title=f"{code} 五档盘口")

    _run()


@app.command()
def ticks(
    code: Annotated[str, typer.Argument(help="股票代码")],
    date_str: Annotated[Optional[str], typer.Option("--date", "-d", help="日期 YYYY-MM-DD")] = None,
):
    """逐笔成交."""
    from astk.market.mootdx_api import get_ticks
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        c = normalize_code(code)
        d = date_str.replace("-", "") if date_str else None
        df = get_ticks(c, date=d)
        render(df, _get_output(), title=f"{code} 逐笔成交")

    _run()


# ── Layer 2: Research ────────────────────────────────────────


@report_app.command("list")
def report_list(
    code: Annotated[str, typer.Argument(help="股票代码")],
    pages: Annotated[int, typer.Option("--pages", "-p", help="拉取页数")] = 3,
):
    """研报列表."""
    from astk.research.eastmoney_api import eastmoney_reports
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        c = normalize_code(code)
        records = eastmoney_reports(c, max_pages=pages)
        rows = []
        for r in records[:50]:
            rows.append({
                "日期": (r.get("publishDate") or "")[:10],
                "机构": r.get("orgSName", ""),
                "评级": r.get("emRatingName", ""),
                "今年EPS": r.get("predictThisYearEps", ""),
                "明年EPS": r.get("predictNextYearEps", ""),
                "标题": (r.get("title") or "")[:50],
            })
        render(rows, _get_output(), title=f"{code} 研报 (共{len(records)}篇)")

    _run()


@report_app.command("download")
def report_download(
    code: Annotated[str, typer.Argument(help="股票代码")],
    target_dir: Annotated[str, typer.Option("--dir", help="保存目录")] = "./reports",
    limit: Annotated[int, typer.Option("--limit", "-n", help="下载数量")] = 10,
):
    """下载研报PDF."""
    from astk.research.eastmoney_api import eastmoney_reports, download_pdf
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors

    @handle_errors
    def _run():
        c = normalize_code(code)
        records = eastmoney_reports(c, max_pages=2)
        from rich.console import Console
        console = Console()
        for r in records[:limit]:
            path = download_pdf(r, target_dir=target_dir)
            if path:
                console.print(f"[green]✓[/green] {path}")
            else:
                console.print(f"[yellow]✗[/yellow] {r.get('title', '')[:50]}")
        console.print(f"完成，共处理 {min(limit, len(records))} 篇")

    _run()


@app.command()
def consensus(
    code: Annotated[str, typer.Argument(help="股票代码")],
):
    """机构一致预期EPS."""
    from astk.research.consensus_api import get_consensus_eps
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        c = normalize_code(code)
        df = get_consensus_eps(c)
        render(df, _get_output(), title=f"{code} 机构一致预期")

    _run()


@app.command()
def iwencai(
    query: Annotated[str, typer.Argument(help="自然语言查询")],
    channel: Annotated[str, typer.Option("--channel", "-c", help="渠道: report/announcement/news")] = "report",
    size: Annotated[int, typer.Option("--size", "-s", help="返回条数")] = 50,
):
    """iwencai NL语义搜索."""
    from astk.research.iwencai_api import iwencai_search, dedup_articles
    from astk.utils.errors import handle_errors, AuthenticationError
    from astk.utils.output import render

    @handle_errors
    def _run():
        import os
        if not os.environ.get("IWENCAI_API_KEY"):
            raise AuthenticationError("未设置 IWENCAI_API_KEY 环境变量。申请: https://www.iwencai.com/skillhub")
        articles = iwencai_search(query, channel=channel, size=size)
        articles = dedup_articles(articles)
        rows = []
        for a in articles[:30]:
            rows.append({
                "日期": (a.get("publish_date") or "")[:10],
                "标题": (a.get("title") or "")[:60],
                "分数": a.get("score", ""),
            })
        render(rows, _get_output(), title=f"iwencai: {query}")

    _run()


# ── Layer 3: News ────────────────────────────────────────────


@app.command()
def news(
    code: Annotated[str, typer.Argument(help="股票代码")],
):
    """个股新闻."""
    from astk.news.news_api import get_stock_news
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        c = normalize_code(code)
        df = get_stock_news(c)
        render(df, _get_output(), title=f"{code} 新闻")

    _run()


@app.command()
def flash():
    """财联社快讯."""
    from astk.news.news_api import get_cls_flash
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        df = get_cls_flash()
        render(df, _get_output(), title="财联社快讯")

    _run()


@app.command("global-news")
def global_news():
    """东财全球资讯."""
    from astk.news.news_api import get_global_news
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        df = get_global_news()
        render(df, _get_output(), title="全球资讯")

    _run()


# ── Layer 4: Fundamentals ───────────────────────────────────


@app.command()
def finance(
    code: Annotated[str, typer.Argument(help="股票代码")],
):
    """37字段季报快照."""
    from astk.fundamentals.finance_api import get_finance_snapshot
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        c = normalize_code(code)
        df = get_finance_snapshot(c)
        render(df, _get_output(), title=f"{code} 季报快照")

    _run()


@app.command()
def f10(
    code: Annotated[str, typer.Argument(help="股票代码")],
    category: Annotated[Optional[str], typer.Option("--category", "-c", help="分类: 最新提示/公司概况/财务分析/股东研究/股本结构/资本运作/业内点评/行业分析/公司大事")] = None,
):
    """F10公司资料."""
    from astk.fundamentals.f10_api import get_f10
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors

    @handle_errors
    def _run():
        c = normalize_code(code)
        if category:
            from astk.utils.output import render
            text = get_f10(c, category)
            if text:
                print(text)
            else:
                print(f"(无 {category} 数据)")
        else:
            categories = ["最新提示", "公司概况", "财务分析", "股东研究", "股本结构", "资本运作", "业内点评", "行业分析", "公司大事"]
            from rich.console import Console
            console = Console()
            for cat in categories:
                text = get_f10(c, cat)
                console.print(f"\n[bold]== {cat} ==[/bold]")
                print(text[:500] if text else "(空)")

    _run()


@app.command()
def info(
    code: Annotated[str, typer.Argument(help="股票代码")],
):
    """个股基本面."""
    from astk.fundamentals.info_api import get_stock_info
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        c = normalize_code(code)
        df = get_stock_info(c)
        render(df, _get_output(), title=f"{code} 基本面")

    _run()


# ── Layer 5: Filings ────────────────────────────────────────


@filing_app.command("list")
def filing_list(
    code: Annotated[str, typer.Argument(help="股票代码")],
):
    """巨潮公告."""
    from astk.filings.cninfo_api import get_filings
    from astk.utils.code import normalize_code, get_cninfo_market
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        c = normalize_code(code)
        market = get_cninfo_market(c)
        df = get_filings(c, market=market)
        render(df, _get_output(), title=f"{code} 公告")

    _run()


# ── Layer 6: Signals ────────────────────────────────────────


@app.command()
def hot(
    date_str: Annotated[Optional[str], typer.Option("--date", "-d", help="日期 YYYY-MM-DD")] = None,
):
    """同花顺强势股 + 题材归因."""
    from astk.signals.hot_api import get_hot_stocks
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        df = get_hot_stocks(date_str)
        cols = ["代码", "名称", "涨幅%", "换手率%", "题材归因"]
        cols = [c for c in cols if c in df.columns]
        render(df, _get_output(), title="强势股 + 题材归因", columns=cols)

    _run()


@app.command()
def northbound(
    history: Annotated[bool, typer.Option("--history", help="显示历史缓存")] = False,
    days: Annotated[int, typer.Option("--days", "-n", help="历史天数")] = 20,
):
    """北向资金流向."""
    from astk.signals.northbound_api import get_northbound_realtime
    from astk.utils.cache import load_northbound_history
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        if history:
            df = load_northbound_history(days)
            render(df, _get_output(), title=f"北向资金历史 (近{days}天)")
        else:
            df = get_northbound_realtime()
            render(df, _get_output(), title="北向资金实时")

    _run()


@app.command()
def concept(
    code: Annotated[str, typer.Argument(help="股票代码")],
):
    """概念板块归属."""
    from astk.signals.baidu_api import get_concept_blocks
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        c = normalize_code(code)
        data = get_concept_blocks(c)
        rows = []
        for block_type in ["industry", "concept", "region"]:
            for item in data.get(block_type, []):
                rows.append({
                    "类型": block_type,
                    "名称": item.get("name", ""),
                    "涨跌幅": item.get("change_pct", ""),
                })
        render(rows, _get_output(), title=f"{code} 板块归属")

    _run()


@app.command()
def fundflow(
    code: Annotated[str, typer.Argument(help="股票代码")],
    history: Annotated[bool, typer.Option("--history", help="历史资金流向")] = False,
    days: Annotated[int, typer.Option("--days", "-n", help="历史天数")] = 20,
):
    """个股资金流向."""
    from astk.signals.baidu_api import get_fund_flow_realtime, get_fund_flow_history
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        c = normalize_code(code)
        if history:
            rows = get_fund_flow_history(c, days=days)
            render(rows, _get_output(), title=f"{code} 资金流向历史")
        else:
            from datetime import date as _date
            d = _date.today().strftime("%Y%m%d")
            rows = get_fund_flow_realtime(c, date=d)
            render(rows, _get_output(), title=f"{code} 实时资金流向")

    _run()


@app.command("dragon-tiger")
def dragon_tiger(
    code: Annotated[str, typer.Argument(help="股票代码")],
    date_str: Annotated[Optional[str], typer.Option("--date", "-d", help="截止日期 YYYY-MM-DD")] = None,
    lookback: Annotated[int, typer.Option("--lookback", "-l", help="回看天数")] = 30,
):
    """龙虎榜 (个股)."""
    from astk.signals.dragon_tiger_api import get_dragon_tiger
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        from datetime import date as _date
        c = normalize_code(code)
        d = date_str or _date.today().strftime("%Y-%m-%d")
        data = get_dragon_tiger(c, trade_date=d, look_back=lookback)
        from rich.console import Console
        console = Console()
        console.print(f"[bold]上榜记录 ({len(data['records'])}次):[/bold]")
        render(data["records"], _get_output(), title="上榜记录")
        if data["seats"]["buy"]:
            console.print(f"\n[bold]买入席位 TOP5:[/bold]")
            render(data["seats"]["buy"], _get_output(), title="买入席位")
        if data["institution"]:
            console.print(f"\n[bold]机构动向:[/bold]")
            render(data["institution"], _get_output(), title="机构动向")

    _run()


@app.command("dragon-tiger-all")
def dragon_tiger_all(
    date_str: Annotated[Optional[str], typer.Option("--date", "-d", help="日期 YYYY-MM-DD")] = None,
    min_net_buy: Annotated[Optional[float], typer.Option("--min-net-buy", help="净买入下限(万)")] = None,
):
    """全市场龙虎榜."""
    from astk.signals.dragon_tiger_api import get_daily_dragon_tiger
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        from datetime import date as _date
        d = date_str or _date.today().strftime("%Y-%m-%d")
        data = get_daily_dragon_tiger(d, min_net_buy=min_net_buy)
        render(data["stocks"], _get_output(), title=f"龙虎榜 {data['date']} ({data['total_records']}条)")

    _run()


@app.command()
def lockup(
    code: Annotated[str, typer.Argument(help="股票代码")],
    date_str: Annotated[Optional[str], typer.Option("--date", "-d", help="截止日期 YYYY-MM-DD")] = None,
    forward: Annotated[int, typer.Option("--forward", "-f", help="前瞻天数")] = 90,
):
    """限售解禁日历."""
    from astk.signals.lockup_api import get_lockup_expiry
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        from datetime import date as _date
        c = normalize_code(code)
        d = date_str or _date.today().strftime("%Y-%m-%d")
        data = get_lockup_expiry(c, trade_date=d, forward_days=forward)
        from rich.console import Console
        console = Console()
        console.print(f"[bold]历史解禁 ({len(data['history'])}批):[/bold]")
        if data["history"]:
            render(data["history"], _get_output(), title="历史解禁")
        console.print(f"\n[bold]未来{forward}天待解禁 ({len(data['upcoming'])}批):[/bold]")
        if data["upcoming"]:
            render(data["upcoming"], _get_output(), title="待解禁")

    _run()


@app.command()
def industry(
    top: Annotated[int, typer.Option("--top", "-n", help="TOP N")] = 20,
):
    """行业横向对比."""
    from astk.signals.industry_api import get_industry_comparison
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        data = get_industry_comparison(top_n=top)
        render(data["top"], _get_output(), title=f"行业涨幅 TOP{top}")

    _run()


# ── Flows ───────────────────────────────────────────────────


@app.command()
def valuation(
    code: Annotated[str, typer.Argument(help="股票代码")],
):
    """单票完整估值分析."""
    from astk.flows.valuation import full_valuation
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        c = normalize_code(code)
        result = full_valuation(c)
        render(result, _get_output(), title=f"{result.get('name', code)} 估值分析")

    _run()


@app.command()
def batch(
    codes: Annotated[list[str], typer.Argument(help="多个股票代码")],
):
    """批量估值对比."""
    from astk.flows.valuation import full_valuation
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors
    from astk.utils.output import render

    @handle_errors
    def _run():
        rows = []
        for raw in codes:
            try:
                c = normalize_code(raw)
                r = full_valuation(c)
                rows.append(r)
            except Exception as e:
                rows.append({"code": raw, "error": str(e)})
        render(rows, _get_output(), title="批量估值对比")

    _run()


@app.command("research")
def research_cmd(
    code: Annotated[str, typer.Argument(help="股票代码")],
):
    """新票快速调研 (多维度汇总)."""
    from astk.flows.research_flow import quick_research
    from astk.utils.code import normalize_code
    from astk.utils.errors import handle_errors

    @handle_errors
    def _run():
        c = normalize_code(code)
        quick_research(c)

    _run()


if __name__ == "__main__":
    app()
