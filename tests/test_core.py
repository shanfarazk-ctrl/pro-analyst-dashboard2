"""
tests/test_core.py
Core unit tests for PRO ANALYST dashboard.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
import pandas as pd
from data_fetchers.fetcher import DataFetcher, POPULAR_EXCHANGES, EXCHANGE_SUFFIX
from ai_engine.analyst import AIAnalyst
from utils.benchmarks import get_benchmarks, SECTORS, INDUSTRY_BENCHMARKS
from utils.charts import area_trend, bar_chart, line_chart

# ─── SAMPLE DATA ─────────────────────────────────────────────────────────────
SAMPLE_KPIS = [
    {"year": 2021, "revenue": 1e9, "ebitda": 2e8, "net_income": 1e8,
     "gross_margin": 0.40, "ebitda_margin": 0.20, "ebit_margin": 0.15, "net_margin": 0.10,
     "roe": 0.18, "roa": 0.09, "roic": 0.14, "revenue_growth": 0.08, "ebitda_growth": 0.10,
     "ni_growth": 0.12, "cfo": 1.8e8, "capex": 5e7, "fcf": 1.3e8,
     "cfo_margin": 0.18, "fcf_margin": 0.13, "cfo_to_ni": 1.8, "capex_intensity": 0.05,
     "debt_equity": 0.8, "debt_ebitda": 2.0, "net_debt": 2e8, "net_debt_ebitda": 1.0,
     "interest_coverage": 8.0, "current_ratio": 1.8, "quick_ratio": 1.4, "cash_ratio": 0.5,
     "asset_turnover": 0.9, "inventory_days": 45, "receivable_days": 40, "payable_days": 35, "ccc": 50},
    {"year": 2022, "revenue": 1.1e9, "ebitda": 2.2e8, "net_income": 1.1e8,
     "gross_margin": 0.41, "ebitda_margin": 0.20, "ebit_margin": 0.155, "net_margin": 0.10,
     "roe": 0.19, "roa": 0.095, "roic": 0.145, "revenue_growth": 0.10, "ebitda_growth": 0.10,
     "ni_growth": 0.10, "cfo": 2.0e8, "capex": 6e7, "fcf": 1.4e8,
     "cfo_margin": 0.18, "fcf_margin": 0.127, "cfo_to_ni": 1.82, "capex_intensity": 0.055,
     "debt_equity": 0.75, "debt_ebitda": 1.9, "net_debt": 1.8e8, "net_debt_ebitda": 0.82,
     "interest_coverage": 9.0, "current_ratio": 1.9, "quick_ratio": 1.5, "cash_ratio": 0.55,
     "asset_turnover": 0.95, "inventory_days": 43, "receivable_days": 38, "payable_days": 36, "ccc": 45},
]

SAMPLE_BENCHMARKS = get_benchmarks("Consumer Staples")

# ─── TESTS: FETCHER ───────────────────────────────────────────────────────────
class TestFetcher:
    def test_exchanges_populated(self):
        assert len(POPULAR_EXCHANGES) >= 10
        assert "🇵🇰 Pakistan (PSX)" in POPULAR_EXCHANGES

    def test_exchange_suffixes(self):
        assert EXCHANGE_SUFFIX.get("PSX") == ".KA"
        assert EXCHANGE_SUFFIX.get("NYSE") == ""
        assert EXCHANGE_SUFFIX.get("LSE") == ".L"

    def test_build_ticker(self):
        f = DataFetcher()
        assert f.build_ticker("NESTLE", "PSX") == "NESTLE.KA"
        assert f.build_ticker("AAPL", "NYSE") == "AAPL"
        assert f.build_ticker("RELIANCE", "NSE") == "RELIANCE.NS"

    def test_parse_uploaded_empty(self):
        f = DataFetcher()
        empty_df = pd.DataFrame({"Metric": ["Revenue"], "2023": [0]})
        result = f.parse_uploaded_financials(empty_df)
        assert isinstance(result, dict)
        assert "success" in result

    def test_calc_kpis_structure(self):
        f = DataFetcher()
        fake_data = {
            "income": [
                {"year": 2022, "revenue": 1e9, "cogs": 6e8, "gross_profit": 4e8, "ebitda": 2e8,
                 "ebit": 1.5e8, "net_income": 1e8, "interest_expense": 2e7, "tax_expense": 3e7, "depreciation": 5e7},
                {"year": 2023, "revenue": 1.1e9, "cogs": 6.5e8, "gross_profit": 4.5e8, "ebitda": 2.2e8,
                 "ebit": 1.7e8, "net_income": 1.1e8, "interest_expense": 2e7, "tax_expense": 3.2e7, "depreciation": 5e7},
            ],
            "balance_sheet": [
                {"year": 2022, "total_assets": 1.5e9, "total_equity": 5e8, "debt": 3e8, "cash": 1e8,
                 "current_assets": 5e8, "current_liabilities": 3e8, "inventory": 1e8, "receivables": 1.2e8, "payables": 9e7},
                {"year": 2023, "total_assets": 1.6e9, "total_equity": 5.5e8, "debt": 2.8e8, "cash": 1.2e8,
                 "current_assets": 5.5e8, "current_liabilities": 3.1e8, "inventory": 1.1e8, "receivables": 1.3e8, "payables": 9.5e7},
            ],
            "cashflow": [
                {"year": 2022, "cfo": 1.8e8, "capex": 5e7, "fcf": 1.3e8},
                {"year": 2023, "cfo": 2.0e8, "capex": 6e7, "fcf": 1.4e8},
            ],
        }
        kpis = f._calc_kpis(fake_data)
        assert len(kpis) == 2
        assert "ebitda_margin" in kpis[0]
        assert "current_ratio" in kpis[0]
        assert "debt_ebitda" in kpis[0]
        assert kpis[1]["revenue_growth"] is not None

# ─── TESTS: AI ANALYST ───────────────────────────────────────────────────────
class TestAnalyst:
    def test_score_structure(self):
        analyst = AIAnalyst()
        scores = analyst.calc_score(SAMPLE_KPIS, SAMPLE_BENCHMARKS)
        assert "total" in scores
        assert 0 <= scores["total"] <= 100
        assert "profitability" in scores
        assert "balance_sheet" in scores

    def test_risk_flags_no_crash(self):
        analyst = AIAnalyst()
        flags = analyst.generate_risk_flags_ai(SAMPLE_KPIS)
        assert isinstance(flags, list)
        for f in flags:
            assert "type" in f
            assert "severity" in f
            assert f["severity"] in ["high", "medium", "low"]

    def test_risk_flags_detects_high_leverage(self):
        analyst = AIAnalyst()
        high_leverage_kpis = [dict(SAMPLE_KPIS[0]), dict(SAMPLE_KPIS[1])]
        high_leverage_kpis[1]["debt_ebitda"] = 5.0
        flags = analyst.generate_risk_flags_ai(high_leverage_kpis)
        types = [f["type"] for f in flags]
        assert any("Leverage" in t for t in types)

    def test_score_label(self):
        analyst = AIAnalyst()
        assert analyst.score_label(85)[0] == "Excellent"
        assert analyst.score_label(70)[0] == "Strong"
        assert analyst.score_label(55)[0] == "Moderate"
        assert analyst.score_label(40)[0] == "Weak"
        assert analyst.score_label(20)[0] == "High Concern"

# ─── TESTS: BENCHMARKS ───────────────────────────────────────────────────────
class TestBenchmarks:
    def test_all_sectors_have_required_keys(self):
        required = ["avg_ebitda_margin", "avg_net_margin", "avg_roe", "avg_pe"]
        for sector, data in INDUSTRY_BENCHMARKS.items():
            for key in required:
                assert key in data, f"{sector} missing {key}"

    def test_fuzzy_match(self):
        bm = get_benchmarks("Food & Beverage Packaging")
        assert bm is not None
        assert "avg_ebitda_margin" in bm

    def test_unknown_fallback(self):
        bm = get_benchmarks("Completely Unknown Industry XYZ")
        assert bm["avg_pe"] == 20.0  # Default fallback

    def test_sectors_list(self):
        assert len(SECTORS) >= 20

# ─── TESTS: CHARTS ───────────────────────────────────────────────────────────
class TestCharts:
    def test_area_trend_no_crash(self):
        fig = area_trend(SAMPLE_KPIS, [("revenue", "Revenue", "#00d4aa")], "Test")
        assert fig is not None

    def test_bar_chart_no_crash(self):
        fig = bar_chart(SAMPLE_KPIS, [("ebitda", "EBITDA", "#6366f1")], "Test")
        assert fig is not None

    def test_line_chart_pct(self):
        fig = line_chart(SAMPLE_KPIS, [("ebitda_margin", "Margin", "#00d4aa")], pct=True)
        assert fig is not None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
