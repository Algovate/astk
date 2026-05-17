"""mootdx F10: 九大类公司文本资料."""

from __future__ import annotations

from astk.market.mootdx_api import _client


CATEGORIES = [
    "最新提示", "公司概况", "财务分析",
    "股东研究", "股本结构", "资本运作",
    "业内点评", "行业分析", "公司大事",
]


def get_f10(symbol: str, name: str) -> str | None:
    """获取指定类别的F10文本数据."""
    client = _client()
    text = client.F10(symbol=symbol, name=name)
    if not text:
        return None
    # V2.1 截断: 股东研究中的历史十大股东列表只保留最新一期
    if name == "股东研究" and text:
        marker = "4.股东变化"
        idx = text.find(marker)
        if idx >= 0:
            section = text[idx:]
            # Keep only first period entry (up to double newline after first block)
            parts = section.split("\n\n")
            if len(parts) > 2:
                section = "\n\n".join(parts[:2]) + "\n...(截断，只保留最新一期)"
                text = text[:idx] + section
    return text
