"""快速调研流程: 多维度汇总."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from astk.market.tencent_api import tencent_quote
from astk.signals.baidu_api import get_concept_blocks, get_fund_flow_history
from astk.signals.dragon_tiger_api import get_dragon_tiger
from astk.signals.lockup_api import get_lockup_expiry
from astk.utils.output import OutputFormat, render


def quick_research(code: str, fmt: OutputFormat = OutputFormat.table) -> None:
    """新票快速调研 (多维度汇总)."""
    from datetime import date as _date
    console = Console()
    today = _date.today().strftime("%Y-%m-%d")

    if fmt != OutputFormat.table:
        _research_structured(code, today, fmt)
        return

    # 1. 实时行情
    try:
        quotes = tencent_quote([code])
        if code in quotes:
            q = quotes[code]
            console.print(Panel(
                f"[bold]{q['name']}[/bold] ({code})\n"
                f"价格: {q['price']}  涨跌: {q['change_pct']}%\n"
                f"PE(TTM): {q['pe_ttm']}  PB: {q['pb']}\n"
                f"市值: {q['mcap_yi']}亿  换手: {q['turnover_pct']}%\n"
                f"涨停: {q['limit_up']}  跌停: {q['limit_down']}",
                title="实时行情",
            ))
    except Exception as e:
        console.print(f"[red]行情获取失败: {e}[/red]")

    # 2. 概念板块
    try:
        blocks = get_concept_blocks(code)
        tags = blocks.get("concept_tags", [])[:15]
        industries = [b["name"] for b in blocks.get("industry", [])]
        console.print(Panel(
            f"行业: {', '.join(industries)}\n"
            f"概念: {', '.join(tags)}",
            title="板块归属",
        ))
    except Exception as e:
        console.print(f"[yellow]板块数据获取失败: {e}[/yellow]")

    # 3. 资金流向
    try:
        flow = get_fund_flow_history(code, days=5)
        if flow:
            lines = []
            for h in flow[:5]:
                lines.append(f"{h['date']}: 主力={h['mainIn']}万 超大={h['superNetIn']}万")
            console.print(Panel("\n".join(lines), title="资金流向 (近5日)"))
    except Exception as e:
        console.print(f"[yellow]资金流向获取失败: {e}[/yellow]")

    # 4. 龙虎榜
    try:
        dtb = get_dragon_tiger(code, today, look_back=30)
        if dtb["records"]:
            lines = [f"近30日上榜 {len(dtb['records'])} 次"]
            for r in dtb["records"][:5]:
                lines.append(f"  {r['date']}: {r['reason']}")
            if dtb["institution"]:
                inst = dtb["institution"]
                lines.append(f"  机构: 买{inst.get('buy_count', 0)}家 卖{inst.get('sell_count', 0)}家")
            console.print(Panel("\n".join(lines), title="龙虎榜"))
        else:
            console.print("[dim]近30日未上龙虎榜[/dim]")
    except Exception as e:
        console.print(f"[yellow]龙虎榜获取失败: {e}[/yellow]")

    # 5. 解禁预警
    try:
        lockup = get_lockup_expiry(code, today, forward_days=90)
        if lockup["upcoming"]:
            lines = [f"未来90天待解禁 {len(lockup['upcoming'])} 批"]
            for u in lockup["upcoming"]:
                lines.append(f"  {u['date']}: {u['type']} 数量={u['shares']}")
            console.print(Panel("\n".join(lines), title="解禁预警", style="yellow"))
        else:
            console.print("[dim]未来90天无待解禁[/dim]")
    except Exception as e:
        console.print(f"[yellow]解禁数据获取失败: {e}[/yellow]")


def _research_structured(code: str, today: str, fmt: OutputFormat) -> None:
    """Structured output for json/csv mode."""
    sections: dict = {}

    try:
        quotes = tencent_quote([code])
        if code in quotes:
            sections["quote"] = quotes[code]
    except Exception:
        pass

    try:
        blocks = get_concept_blocks(code)
        sections["blocks"] = {
            "industry": [b["name"] for b in blocks.get("industry", [])],
            "concept": blocks.get("concept_tags", [])[:15],
        }
    except Exception:
        pass

    try:
        sections["fund_flow"] = get_fund_flow_history(code, days=5)
    except Exception:
        pass

    try:
        dtb = get_dragon_tiger(code, today, look_back=30)
        sections["dragon_tiger"] = {
            "count": len(dtb["records"]),
            "records": dtb["records"][:5],
            "institution": dtb.get("institution"),
        }
    except Exception:
        pass

    try:
        lockup = get_lockup_expiry(code, today, forward_days=90)
        sections["lockup"] = {
            "upcoming_count": len(lockup["upcoming"]),
            "upcoming": lockup["upcoming"],
        }
    except Exception:
        pass

    render(sections, fmt, title=f"{code} 快速调研")
