# astk

A股全栈数据 CLI 工具 — 6 层数据架构 · 21 个端点 · 7 个数据源

## 功能概览

| 层级 | 分类 | 命令 | 说明 |
|------|------|------|------|
| L1 | 行情 | `quote` | 实时行情 (mootdx + 腾讯合并) |
| | | `kline` | K 线数据 (日线/周线/月线/分钟) |
| | | `orderbook` | 五档盘口 |
| | | `ticks` | 逐笔成交 |
| L2 | 研报 | `report list` | 研报列表 |
| | | `report download` | 下载研报 PDF |
| | | `consensus` | 机构一致预期 EPS |
| | | `iwencai` | 自然语言语义搜索 |
| L3 | 新闻 | `news` | 个股新闻 |
| | | `flash` | 财联社快讯 |
| | | `global-news` | 东财全球资讯 |
| L4 | 基础面 | `finance` | 37 字段季报快照 |
| | | `f10` | F10 公司资料 (9 分类) |
| | | `info` | 个股基本面 |
| L5 | 公告 | `filing list` | 巨潮公告 |
| L6 | 信号 | `hot` | 强势股 + 题材归因 |
| | | `northbound` | 北向资金流向 |
| | | `concept` | 概念板块归属 |
| | | `fundflow` | 个股资金流向 |
| | | `dragon-tiger` | 龙虎榜 (个股) |
| | | `dragon-tiger-all` | 全市场龙虎榜 |
| | | `lockup` | 限售解禁日历 |
| | | `industry` | 行业横向对比 |
| — | 工作流 | `valuation` | 单票完整估值分析 |
| | | `batch` | 批量估值对比 |
| | | `research` | 新票快速调研 |

## 安装

要求 Python >= 3.12，推荐使用 [uv](https://github.com/astral-sh/uv)：

```bash
uv pip install -e .
```

或 pip：

```bash
pip install -e .
```

## 快速开始

```bash
# 实时行情
astk quote 688017

# K 线
astk kline 000001 -p week -n 100

# 五档盘口
astk orderbook 600519

# 研报列表
astk report list 300750

# 机构一致预期
astk consensus 300750

# 财联社快讯
astk flash

# 季报快照 (37 字段)
astk finance 000858

# F10 公司资料
astk f10 000858
astk f10 000858 -c 公司概况

# 巨潮公告
astk filing list 002594

# 北向资金
astk northbound
astk northbound --history -n 30

# 龙虎榜
astk dragon-tiger 000001 -l 30
astk dragon-tiger-all -d 2025-01-15

# 限售解禁
astk lockup 688017 -f 90

# 行业对比
astk industry -n 20

# 估值分析
astk valuation 300750

# 批量对比
astk batch 000858 000568 600519

# 快速调研
astk research 002594
```

## 全局选项

```bash
-o, --output TEXT   输出格式: table (默认), json, csv
-v, --version       显示版本号
```

```bash
astk quote 000001 -o json
astk finance 600519 -o csv
```

## 环境变量

| 变量 | 用途 | 必需 |
|------|------|------|
| `IWENCAI_API_KEY` | 问财语义搜索 API Key | 仅 `iwencai` 命令需要 |

## 数据源

| 数据源 | 用途 |
|--------|------|
| mootdx | 通达信 TCP 行情 (实时/K 线/盘口/逐笔) |
| 腾讯财经 | HTTP 实时行情补充 |
| 东方财富 | 研报、一致预期、新闻、全球资讯 |
| 问财 (iwencai) | 自然语言语义搜索 |
| 巨潮资讯 (cninfo) | 监管公告 |
| 同花顺 | 强势股/题材归因 |
| 百度股市通 | 概念板块、资金流向、行业对比 |

## 依赖

- [akshare](https://github.com/akfamily/akshare) — A 股数据接口
- [mootdx](https://github.com/mootdx/mootdx) — 通达信行情协议
- [pandas](https://pandas.pydata.org/) — 数据处理
- [typer](https://typer.tiangolo.com/) — CLI 框架
- [rich](https://rich.readthedocs.io/) — 终端格式化
- [stockstats](https://github.com/jealous/stockstats) — 股票统计指标
- [wencai](https://github.com/zbyeah/wencai) — 问财 API
- [requests](https://docs.python-requests.org/) — HTTP 请求

## License

MIT
