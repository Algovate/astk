"""Tests for astk.cli — CLI integration with mocked backends."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from typer.testing import CliRunner

from astk.cli import app

runner = CliRunner()


# ── Global flags ─────────────────────────────────────────────


class TestGlobalFlags:
    def test_version(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "astk" in result.output

    def test_help(self):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "行情" in result.output


# ── Layer 1: Market ──────────────────────────────────────────


class TestQuote:
    @patch("astk.market.mootdx_api.get_quotes")
    @patch("astk.market.tencent_api.tencent_quote")
    def test_success(self, mock_tencent, mock_mootdx):
        mock_tencent.return_value = {"688017": {"name": "乐鑫科技", "price": 234.5, "pe_ttm": 56.0, "pb": 3.5, "mcap_yi": 200.0, "turnover_pct": 1.5, "change_pct": 2.0, "last_close": 230.0, "open": 231.0, "change_amt": 4.5, "high": 236.0, "low": 229.0, "amount_wan": 50000, "amplitude_pct": 3.0, "float_mcap_yi": 150.0, "limit_up": 253.0, "limit_down": 207.0, "vol_ratio": 1.2, "pe_static": 50.0}}
        mock_mootdx.return_value = pd.DataFrame()
        result = runner.invoke(app, ["quote", "688017"])
        assert result.exit_code == 0

    @patch("astk.market.mootdx_api.get_quotes")
    @patch("astk.market.tencent_api.tencent_quote")
    def test_json_output(self, mock_tencent, mock_mootdx):
        mock_tencent.return_value = {"688017": {"name": "乐鑫科技", "price": 234.5, "pe_ttm": 0, "pb": 0, "mcap_yi": 0, "turnover_pct": 0, "change_pct": 0, "last_close": 0, "open": 0, "change_amt": 0, "high": 0, "low": 0, "amount_wan": 0, "amplitude_pct": 0, "float_mcap_yi": 0, "limit_up": 0, "limit_down": 0, "vol_ratio": 0, "pe_static": 0}}
        mock_mootdx.return_value = pd.DataFrame()
        result = runner.invoke(app, ["-o", "json", "quote", "688017"])
        assert result.exit_code == 0
        assert "乐鑫科技" in result.output

    def test_invalid_code(self):
        result = runner.invoke(app, ["quote", "abc"])
        assert result.exit_code == 1


class TestKline:
    @patch("astk.market.mootdx_api.get_kline")
    def test_success(self, mock_kline):
        mock_kline.return_value = pd.DataFrame({"open": [100], "close": [101]})
        result = runner.invoke(app, ["kline", "688017"])
        assert result.exit_code == 0


class TestOrderbook:
    @patch("astk.market.mootdx_api.get_quotes")
    def test_success(self, mock_quotes):
        mock_quotes.return_value = pd.DataFrame({
            "bid1": [10.0], "bid_vol1": [100], "ask1": [10.5], "ask_vol1": [200],
            "bid2": [9.9], "bid_vol2": [50], "ask2": [10.6], "ask_vol2": [150],
            "bid3": [9.8], "bid_vol3": [80], "ask3": [10.7], "ask_vol3": [120],
            "bid4": [9.7], "bid_vol4": [60], "ask4": [10.8], "ask_vol4": [90],
            "bid5": [9.6], "bid_vol5": [40], "ask5": [10.9], "ask_vol5": [70],
        })
        result = runner.invoke(app, ["orderbook", "688017"])
        assert result.exit_code == 0

    @patch("astk.market.mootdx_api.get_quotes")
    def test_no_data(self, mock_quotes):
        mock_quotes.return_value = pd.DataFrame()
        result = runner.invoke(app, ["orderbook", "688017"])
        assert result.exit_code == 0


class TestTicks:
    @patch("astk.market.mootdx_api.get_ticks")
    def test_success(self, mock_ticks):
        mock_ticks.return_value = pd.DataFrame({"price": [100], "vol": [50]})
        result = runner.invoke(app, ["ticks", "688017"])
        assert result.exit_code == 0


# ── Layer 2: Research ────────────────────────────────────────


class TestReportList:
    @patch("astk.research.eastmoney_api.eastmoney_reports")
    def test_success(self, mock_reports):
        mock_reports.return_value = [{"publishDate": "2025-01-15", "orgSName": "中信", "emRatingName": "买入", "predictThisYearEps": "2.5", "predictNextYearEps": "3.1", "title": "深度报告"}]
        result = runner.invoke(app, ["report", "list", "688017"])
        assert result.exit_code == 0


class TestReportDownload:
    @patch("astk.research.eastmoney_api.download_pdf")
    @patch("astk.research.eastmoney_api.eastmoney_reports")
    def test_success(self, mock_reports, mock_dl):
        mock_reports.return_value = [{"infoCode": "AN123", "publishDate": "2025-01-15", "orgSName": "中信", "title": "Report"}]
        mock_dl.return_value = "/tmp/report.pdf"
        result = runner.invoke(app, ["report", "download", "688017"])
        assert result.exit_code == 0


class TestConsensus:
    @patch("astk.research.consensus_api.get_consensus_eps")
    def test_success(self, mock_eps):
        mock_eps.return_value = pd.DataFrame({"年度": [2025], "均值": [2.5]})
        result = runner.invoke(app, ["consensus", "688017"])
        assert result.exit_code == 0


class TestIwencai:
    def test_missing_key(self):
        result = runner.invoke(app, ["iwencai", "AI芯片"])
        assert result.exit_code == 1

    @patch("astk.research.iwencai_api.dedup_articles")
    @patch("astk.research.iwencai_api.iwencai_search")
    def test_success(self, mock_search, mock_dedup):
        mock_search.return_value = [{"title": "Report", "publish_date": "2025-01-15", "score": 0.9}]
        mock_dedup.return_value = mock_search.return_value
        result = runner.invoke(app, ["iwencai", "AI芯片"], env={"IWENCAI_API_KEY": "test"})
        assert result.exit_code == 0


# ── Layer 3: News ────────────────────────────────────────────


class TestNews:
    @patch("astk.news.news_api.get_stock_news")
    def test_success(self, mock_news):
        mock_news.return_value = pd.DataFrame({"title": ["headline"]})
        result = runner.invoke(app, ["news", "688017"])
        assert result.exit_code == 0


class TestFlash:
    @patch("astk.news.news_api.get_cls_flash")
    def test_success(self, mock_flash):
        mock_flash.return_value = pd.DataFrame({"content": ["flash"]})
        result = runner.invoke(app, ["flash"])
        assert result.exit_code == 0


class TestGlobalNews:
    @patch("astk.news.news_api.get_global_news")
    def test_success(self, mock_gn):
        mock_gn.return_value = pd.DataFrame({"title": ["news"]})
        result = runner.invoke(app, ["global-news"])
        assert result.exit_code == 0


# ── Layer 4: Fundamentals ───────────────────────────────────


class TestFinance:
    @patch("astk.fundamentals.finance_api.get_finance_snapshot")
    def test_success(self, mock_fin):
        mock_fin.return_value = pd.DataFrame({"字段": ["EPS"], "值": [2.5]})
        result = runner.invoke(app, ["finance", "688017"])
        assert result.exit_code == 0


class TestF10:
    @patch("astk.fundamentals.f10_api.get_f10")
    def test_with_category(self, mock_f10):
        mock_f10.return_value = "some text"
        result = runner.invoke(app, ["f10", "688017", "-c", "公司概况"])
        assert result.exit_code == 0

    @patch("astk.fundamentals.f10_api.get_f10")
    def test_all_categories(self, mock_f10):
        mock_f10.return_value = "text"
        result = runner.invoke(app, ["f10", "688017"])
        assert result.exit_code == 0


class TestInfo:
    @patch("astk.fundamentals.info_api.get_stock_info")
    def test_success(self, mock_info):
        mock_info.return_value = pd.DataFrame({"item": ["总市值"], "value": ["200亿"]})
        result = runner.invoke(app, ["info", "688017"])
        assert result.exit_code == 0


# ── Layer 5: Filings ────────────────────────────────────────


class TestFilingList:
    @patch("astk.filings.cninfo_api.get_filings")
    def test_success(self, mock_filings):
        mock_filings.return_value = pd.DataFrame({"title": ["公告"]})
        result = runner.invoke(app, ["filing", "list", "688017"])
        assert result.exit_code == 0


# ── Layer 6: Signals ────────────────────────────────────────


class TestHot:
    @patch("astk.signals.hot_api.get_hot_stocks")
    def test_success(self, mock_hot):
        mock_hot.return_value = pd.DataFrame({"代码": ["688017"], "名称": ["乐鑫科技"], "涨幅%": [1.5]})
        result = runner.invoke(app, ["hot"])
        assert result.exit_code == 0

    @patch("astk.signals.hot_api.get_hot_stocks")
    def test_with_date(self, mock_hot):
        mock_hot.return_value = pd.DataFrame()
        result = runner.invoke(app, ["hot", "--date", "2025-01-15"])
        assert result.exit_code == 0


class TestNorthbound:
    @patch("astk.utils.cache.save_northbound_snapshot")
    @patch("astk.signals.northbound_api.get_northbound_realtime")
    def test_realtime(self, mock_nb, mock_save):
        mock_nb.return_value = pd.DataFrame({"time": ["15:00"], "hgt_yi": [12.3], "sgt_yi": [8.1]})
        result = runner.invoke(app, ["northbound"])
        assert result.exit_code == 0

    @patch("astk.utils.cache.load_northbound_history")
    def test_history(self, mock_load):
        mock_load.return_value = pd.DataFrame({"date": ["2025-01-15"], "hgt_yi": [12.3]})
        result = runner.invoke(app, ["northbound", "--history"])
        assert result.exit_code == 0


class TestConcept:
    @patch("astk.signals.baidu_api.get_concept_blocks")
    def test_success(self, mock_concept):
        mock_concept.return_value = {"industry": [{"name": "半导体", "change_pct": "2.5"}], "concept": [], "region": []}
        result = runner.invoke(app, ["concept", "688017"])
        assert result.exit_code == 0


class TestFundflow:
    @patch("astk.signals.baidu_api.get_fund_flow_realtime")
    def test_realtime(self, mock_ff):
        mock_ff.return_value = [{"time": "09:30", "mainForce": 100}]
        result = runner.invoke(app, ["fundflow", "688017"])
        assert result.exit_code == 0

    @patch("astk.signals.baidu_api.get_fund_flow_history")
    def test_history(self, mock_ff):
        mock_ff.return_value = [{"date": "2025-01-15", "mainIn": 500}]
        result = runner.invoke(app, ["fundflow", "688017", "--history"])
        assert result.exit_code == 0


class TestDragonTiger:
    @patch("astk.signals.dragon_tiger_api.get_dragon_tiger")
    def test_success(self, mock_dt):
        mock_dt.return_value = {"records": [{"date": "2025-01-15", "reason": "涨幅偏离", "net_buy": 5000, "turnover": 5.2}], "seats": {"buy": [{"name": "中信", "buy_amt": 1000, "sell_amt": 0, "net": 1000}], "sell": []}, "institution": {"buy_count": 3, "sell_count": 1, "net_amount": 2000}}
        result = runner.invoke(app, ["dragon-tiger", "688017"])
        assert result.exit_code == 0


class TestDragonTigerAll:
    @patch("astk.signals.dragon_tiger_api.get_daily_dragon_tiger")
    def test_success(self, mock_dt):
        mock_dt.return_value = {"date": "2025-01-15", "total_records": 1, "stocks": [{"code": "688017", "name": "乐鑫科技"}]}
        result = runner.invoke(app, ["dragon-tiger-all"])
        assert result.exit_code == 0


class TestLockup:
    @patch("astk.signals.lockup_api.get_lockup_expiry")
    def test_success(self, mock_lockup):
        mock_lockup.return_value = {"history": [{"date": "2025-01-10", "type": "首发原股东", "shares": 1000, "ratio": 0.5}], "upcoming": []}
        result = runner.invoke(app, ["lockup", "688017"])
        assert result.exit_code == 0


class TestIndustry:
    @patch("astk.signals.industry_api.get_industry_comparison")
    def test_success(self, mock_ind):
        mock_ind.return_value = {"top": [{"rank": 1, "name": "半导体", "change_pct": 3.5}], "bottom": [], "total": 90}
        result = runner.invoke(app, ["industry"])
        assert result.exit_code == 0


# ── Flows ───────────────────────────────────────────────────


class TestValuation:
    @patch("astk.flows.valuation.full_valuation")
    def test_success(self, mock_val):
        mock_val.return_value = {"name": "乐鑫科技", "code": "688017", "price": 234.5, "mcap_yi": 200.0, "pe_ttm": 56.0, "pb": 3.5, "eps_cur": 4.2, "eps_next": 5.1, "pe_fwd": 55.8, "cagr_pct": 21.0, "peg": 2.65, "digest_years": 1.2, "analyst_count": 15}
        result = runner.invoke(app, ["valuation", "688017"])
        assert result.exit_code == 0


class TestBatch:
    @patch("astk.flows.valuation.full_valuation")
    def test_success(self, mock_val):
        mock_val.return_value = {"name": "Test", "code": "688017", "price": 100}
        result = runner.invoke(app, ["batch", "688017"])
        assert result.exit_code == 0


class TestResearch:
    @patch("astk.flows.research_flow.quick_research")
    def test_success(self, mock_res):
        mock_res.return_value = None
        result = runner.invoke(app, ["research", "688017"])
        assert result.exit_code == 0
