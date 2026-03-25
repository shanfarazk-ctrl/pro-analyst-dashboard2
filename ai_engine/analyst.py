"""
ai_engine/analyst.py
AI-powered financial analysis engine using Anthropic Claude.
Covers: company analysis, peer comparison, macro/micro risk assessment.
"""

import os
import re
import anthropic
import streamlit as st
from typing import Optional

def _get_anthropic_key():
    try:
        return st.secrets["api_keys"]["ANTHROPIC_API_KEY"]
    except Exception:
        return os.getenv("ANTHROPIC_API_KEY", "")

def _fmt_pct(n):
    if n is None: return "N/A"
    return f"{float(n)*100:.1f}%"

def _fmt_x(n):
    if n is None: return "N/A"
    return f"{float(n):.1f}x"

def _fmt_m(n):
    if not n: return "N/A"
    n = float(n)
    if abs(n) >= 1e12: return f"{n/1e12:.2f}T"
    if abs(n) >= 1e9:  return f"{n/1e9:.2f}B"
    if abs(n) >= 1e6:  return f"{n/1e6:.2f}M"
    if abs(n) >= 1e3:  return f"{n/1e3:.2f}K"
    return f"{n:.0f}"

class AIAnalyst:
    def __init__(self):
        key = _get_anthropic_key()
        if not key:
            self.client = None
        else:
            self.client = anthropic.Anthropic(api_key=key)

    def _stream_response(self, prompt: str, system: str = "", max_tokens: int = 2500):
        """Stream Claude response to Streamlit."""
        if not self.client:
            yield "⚠️ **API Key Missing** — Please add your `ANTHROPIC_API_KEY` in Streamlit secrets or `.env` file."
            return
        try:
            with self.client.messages.stream(
                model="claude-opus-4-5",
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}]
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            yield f"\n\n⚠️ Analysis error: {str(e)}"

    def _call(self, prompt: str, system: str = "", max_tokens: int = 2500) -> str:
        """Non-streaming call for structured output."""
        if not self.client:
            return "API key not configured."
        try:
            msg = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}]
            )
            return msg.content[0].text
        except Exception as e:
            return f"Analysis error: {str(e)}"

    # ── MAIN COMPANY ANALYSIS ─────────────────────────────────────────────────
    def generate_full_analysis(self, company_data: dict, peers_data: list[dict],
                                macro_data: dict, industry_benchmarks: dict,
                                scenario: str = "Base") -> str:
        """Generate comprehensive institutional-grade equity research report."""

        profile  = company_data.get("profile", {})
        kpis     = company_data.get("kpis", [])
        mkt      = company_data.get("market_data", {})
        is_private = company_data.get("source") == "upload"

        if not kpis:
            return "Insufficient financial data to generate analysis."

        latest = kpis[-1]
        oldest = kpis[0]
        rev_cagr = ((latest["revenue"] / max(oldest["revenue"], 1)) ** (1 / max(len(kpis)-1, 1)) - 1) if len(kpis) > 1 else 0

        # Build peer summary
        peer_summary = ""
        if peers_data:
            peer_summary = "**Peer Comparison (latest year):**\n"
            for p in peers_data:
                pk = p.get("kpis", [])
                if pk:
                    pl = pk[-1]
                    peer_summary += (
                        f"- {p['profile']['name']}: Revenue CAGR {_fmt_pct(pl.get('revenue_growth'))}, "
                        f"EBITDA Margin {_fmt_pct(pl.get('ebitda_margin'))}, "
                        f"Net Margin {_fmt_pct(pl.get('net_margin'))}, "
                        f"ROE {_fmt_pct(pl.get('roe'))}, "
                        f"Debt/EBITDA {_fmt_x(pl.get('debt_ebitda'))}\n"
                    )

        # Macro context
        macro_ctx = ""
        if macro_data:
            macro_ctx = f"""
**Macro Environment ({macro_data.get('country', 'N/A')}):**
- GDP Growth: {macro_data.get('gdp_growth', 'N/A')}%
- Inflation: {macro_data.get('inflation', 'N/A')}%
- Unemployment: {macro_data.get('unemployment', 'N/A')}%
- Lending Rate: {macro_data.get('interest_rate', 'N/A')}%
- Current Account: {macro_data.get('current_acc', 'N/A')}% of GDP
- Public Debt/GDP: {macro_data.get('public_debt', 'N/A')}%
"""

        system_prompt = """You are a Managing Director-level equity research analyst with 20+ years at a top-tier global investment bank (Goldman Sachs / JP Morgan caliber). 
You write institutional-quality research that hedge funds and asset managers rely on for investment decisions.
Your analysis is data-driven, insight-rich, and uses industry/peer context throughout. 
You clearly identify risks and opportunities. You never write generic definitions. You always interpret numbers, not just report them."""

        user_prompt = f"""Write a comprehensive, institutional-grade equity research report for the following company.

═══════════════════════════════════════════════════════════════
COMPANY PROFILE
═══════════════════════════════════════════════════════════════
Name: {profile.get('name', 'Unknown')}
Type: {'Private Company' if is_private else 'Public Listed'}
Sector: {profile.get('sector', 'N/A')} | Industry: {profile.get('industry', 'N/A')}
Country: {profile.get('country', 'N/A')} | Currency: {profile.get('currency', 'USD')}
{'Market Cap: ' + _fmt_m(mkt.get('market_cap')) if not is_private else 'Private — No Market Data'}

═══════════════════════════════════════════════════════════════
FINANCIAL SNAPSHOT ({latest['year']})
═══════════════════════════════════════════════════════════════
Revenue:        {_fmt_m(latest['revenue'])} | Growth YoY: {_fmt_pct(latest.get('revenue_growth'))} | 5Y CAGR: {_fmt_pct(rev_cagr)}
EBITDA:         {_fmt_m(latest['ebitda'])} | Margin: {_fmt_pct(latest['ebitda_margin'])}
Net Income:     {_fmt_m(latest['net_income'])} | Margin: {_fmt_pct(latest['net_margin'])}
ROE:            {_fmt_pct(latest['roe'])} | ROIC: {_fmt_pct(latest['roic'])} | ROA: {_fmt_pct(latest['roa'])}
FCF:            {_fmt_m(latest['fcf'])} | FCF Margin: {_fmt_pct(latest['fcf_margin'])} | CFO/NI: {_fmt_x(latest['cfo_to_ni'])}
Debt/EBITDA:    {_fmt_x(latest['debt_ebitda'])} | Net Debt/EBITDA: {_fmt_x(latest['net_debt_ebitda'])}
Interest Cover: {_fmt_x(latest['interest_coverage'])}
Current Ratio:  {latest['current_ratio']:.2f}x | Quick Ratio: {latest['quick_ratio']:.2f}x
Gross Margin:   {_fmt_pct(latest['gross_margin'])} | EBIT Margin: {_fmt_pct(latest['ebit_margin'])}
Asset Turnover: {latest['asset_turnover']:.2f}x
Receivable Days:{latest['receivable_days']:.0f}d | Inventory Days: {latest['inventory_days']:.0f}d | Payable Days: {latest['payable_days']:.0f}d | CCC: {latest['ccc']:.0f}d

{'─── Market Data ───' if not is_private else '─── No Market Data (Private) ───'}
{'P/E: ' + _fmt_x(mkt.get('pe')) + ' | Forward P/E: ' + _fmt_x(mkt.get('forward_pe')) + ' | P/B: ' + _fmt_x(mkt.get('pb')) + ' | EV/EBITDA: ' + _fmt_x(mkt.get('ev_ebitda')) + ' | Beta: ' + str(mkt.get('beta','N/A')) if not is_private else 'Valuation based on internal metrics only'}

═══════════════════════════════════════════════════════════════
INDUSTRY BENCHMARKS
═══════════════════════════════════════════════════════════════
Avg EBITDA Margin: {_fmt_pct(industry_benchmarks.get('avg_ebitda_margin'))}
Avg Net Margin:    {_fmt_pct(industry_benchmarks.get('avg_net_margin'))}
Avg Revenue Growth:{_fmt_pct(industry_benchmarks.get('avg_revenue_growth'))}
Avg ROE:           {_fmt_pct(industry_benchmarks.get('avg_roe'))}
Avg Debt/EBITDA:   {_fmt_x(industry_benchmarks.get('avg_debt_ebitda'))}
Avg P/E:           {_fmt_x(industry_benchmarks.get('avg_pe'))}

{peer_summary}

{macro_ctx}

═══════════════════════════════════════════════════════════════
SCENARIO: {scenario.upper()}
═══════════════════════════════════════════════════════════════
{"Bull Case: +5% revenue growth, +200bps margin expansion, multiple re-rating upside" if scenario == "Bull" else "Base Case: Consensus estimates, stable margins, fair value" if scenario == "Base" else "Bear Case: -5% revenue decline, margin compression, de-rating risk"}

═══════════════════════════════════════════════════════════════
REQUIRED OUTPUT — Use exact markdown headers below
═══════════════════════════════════════════════════════════════

## 📊 Executive Summary
[3-4 sentences: Overall health (Strong/Moderate/Weak), valuation stance (Undervalued/Fair/Overvalued if public), investment view (Buy/Hold/Avoid style), conviction level. Be specific with numbers.]

## 🏭 Business Quality & Industry Position
[Competitive moat, pricing power, revenue quality, cyclicality, market position. Compare explicitly to peers.]

## 📈 Profitability Analysis
[Interpret margin trends — are they structurally improving or under pressure? ROE decomposition (DuPont lens). Compare to industry avg. Identify margin drivers and risks.]

## 🚀 Growth Analysis
[Historical growth quality and consistency. 5Y CAGR vs peers. Organic vs. other growth. Forward outlook based on macro and sector dynamics. Key growth constraints.]

## 💰 Cash Flow & Earnings Quality
[CFO vs. Net Income divergence analysis. FCF trend. Is this a cash-generative business? Capex discipline. Earnings quality flag if applicable.]

## 🏦 Balance Sheet & Solvency
[Leverage trajectory — improving or deteriorating? Liquidity adequacy. Debt maturity concern if applicable. Peer comparison on leverage. Red flag if Debt/EBITDA > 4x.]

## ⚙️ Efficiency & Working Capital
[Asset utilization. CCC trend. Receivable/inventory management. Operational execution quality vs peers.]

"""
        
        # Build valuation section based on whether private or public
        if is_private:
            valuation_section = """## 💎 Value Assessment (Private)
[Internal rate of return potential. EV/EBITDA implied range based on peers. EBITDA-based valuation estimate.]"""
        else:
            valuation_section = """## 💎 Valuation Analysis
[P/E, EV/EBITDA vs peers and sector. Historical valuation band context. Implied upside/downside. Premium or discount justified?]"""
        
        user_prompt += valuation_section + """

## 🌍 Macro & Micro-Economic Risk Analysis
[This section is critical. Cover:]
**Macroeconomic Risks:**
- Country-level risks (GDP, inflation, currency, interest rate cycle, sovereign risk)
- Global risks (supply chain, commodity prices, FX exposure, geopolitical)
- Central bank policy impact on cost of capital and consumer spending

**Microeconomic / Industry Risks:**
- Competitive intensity and market share dynamics
- Input cost pressures and pricing power
- Regulatory and policy risks
- Consumer behavior shifts
- Technology disruption risk
- Labor cost and talent dynamics

## ⚠️ Risk Register
[Create a formatted table:]
| Risk | Category | Severity | Impact | Mitigation |
|------|----------|----------|--------|------------|
[List 6-8 specific risks with HIGH/MEDIUM/LOW severity]

## 🔭 Early Warning Signals
[5 specific leading indicators investors should watch. Be precise — include threshold levels where applicable.]

## 📋 Scenario Analysis
**Bull Case 🟢**: [Revenue growth, margin, valuation multiple, implied upside %]
**Base Case 🟡**: [Consensus view, fair value range]
**Bear Case 🔴**: [Downside triggers, floor valuation, implied decline %]

## 🎯 Investment Thesis
**5 Key Positives:**
1. [Specific, data-backed positive]
2. [Specific, data-backed positive]
3. [Specific, data-backed positive]
4. [Specific, data-backed positive]
5. [Specific, data-backed positive]

**5 Key Concerns:**
1. [Specific, data-backed concern]
2. [Specific, data-backed concern]
3. [Specific, data-backed concern]
4. [Specific, data-backed concern]
5. [Specific, data-backed concern]

**Key Catalysts to Watch:** [3 specific events/data points that could re-rate the stock]

**Final Conclusion:** [2-3 definitive sentences with your investment stance. Be direct. Don't hedge excessively.]

---
*Analysis generated by PRO ANALYST AI | Based on latest available data | Not financial advice*
"""
        return self._call(user_prompt, system_prompt, max_tokens=3500)

    # ── STREAMING VERSION ─────────────────────────────────────────────────────
    def stream_full_analysis(self, company_data: dict, peers_data: list[dict],
                              macro_data: dict, industry_benchmarks: dict,
                              scenario: str = "Base"):
        """Streaming version for real-time display."""
        # Build the same prompt (reuse logic)
        analysis = self.generate_full_analysis(company_data, peers_data, macro_data, industry_benchmarks, scenario)
        # Simulate streaming by yielding chunks
        for i in range(0, len(analysis), 20):
            yield analysis[i:i+20]

    # ── RISK FLAG ANALYSIS ────────────────────────────────────────────────────
    def generate_risk_flags_ai(self, kpis: list[dict]) -> list[dict]:
        """Generate structured risk flags from KPIs."""
        flags = []
        if not kpis:
            return flags
        l = kpis[-1]
        prev = kpis[-2] if len(kpis) > 1 else None

        rules = [
            (l.get("debt_ebitda", 0) > 4,         "🔴 High Leverage",         "high",   f"Debt/EBITDA {_fmt_x(l.get('debt_ebitda'))} exceeds 4.0x danger threshold"),
            (l.get("current_ratio", 2) < 1.0,      "🔴 Liquidity Crisis Risk", "high",   f"Current ratio {l.get('current_ratio',0):.2f}x — current liabilities exceed current assets"),
            (l.get("current_ratio", 2) < 1.3,      "🟡 Tight Liquidity",       "medium", f"Current ratio {l.get('current_ratio',0):.2f}x below 1.3x comfort level"),
            (l.get("interest_coverage", 5) < 2,    "🔴 Interest Coverage Risk","high",   f"Coverage {_fmt_x(l.get('interest_coverage'))} — risk of debt service difficulty"),
            (l.get("cfo_to_ni", 1) < 0.8,          "🟡 Earnings Quality Flag", "medium", f"CFO/NI {_fmt_x(l.get('cfo_to_ni'))} — net income may be inflating true cash earnings"),
            (l.get("fcf", 1) < 0,                  "🔴 Negative Free Cash Flow","high",  f"FCF negative — company consuming cash after capex"),
            (l.get("net_margin", 0.1) < 0,         "🔴 Loss-Making",           "high",   "Net income negative — business not profitable at bottom line"),
            (l.get("debt_ebitda", 0) > 2.5 and l.get("debt_ebitda", 0) <= 4, "🟡 Elevated Leverage", "medium", f"Debt/EBITDA {_fmt_x(l.get('debt_ebitda'))} elevated — watch cash generation"),
            (l.get("receivable_days", 0) > 90,     "🟡 Slow Collections",      "medium", f"Receivable days {l.get('receivable_days',0):.0f}d — potential bad debt or revenue recognition risk"),
            (l.get("inventory_days", 0) > 120,     "🟡 Inventory Build-up",    "medium", f"Inventory days {l.get('inventory_days',0):.0f}d — demand slowdown or supply chain risk"),
            (prev and l.get("ebitda_margin",0) < prev.get("ebitda_margin",0) - 0.015, "🟡 Margin Compression", "medium", f"EBITDA margin declined {_fmt_pct(prev.get('ebitda_margin',0) - l.get('ebitda_margin',0))} YoY"),
            (l.get("roic", 0.1) < 0.08,            "🟡 Weak Capital Returns",  "medium", f"ROIC {_fmt_pct(l.get('roic'))} — below typical cost of capital (~8–10%)"),
            (prev and l.get("revenue", 0) < prev.get("revenue", 0), "🟡 Revenue Decline", "medium", f"Revenue fell YoY — watch for structural demand weakness"),
        ]

        for condition, flag_type, severity, msg in rules:
            if condition:
                flags.append({"type": flag_type, "severity": severity, "msg": msg})

        return flags

    # ── SCORING MODEL ─────────────────────────────────────────────────────────
    def calc_score(self, kpis: list[dict], benchmarks: dict) -> dict:
        """Calculate weighted financial health score (0–100)."""
        if not kpis:
            return {"total": 0}
        l = kpis[-1]
        bm = benchmarks

        def score_metric(val, benchmark, higher_is_better=True, scale=2.0):
            if not val or not benchmark or benchmark == 0:
                return 50
            ratio = val / benchmark
            if not higher_is_better:
                ratio = 1 / max(ratio, 0.01)
            return min(100, max(0, 50 + (ratio - 1) * 100 / scale))

        profitability = (
            score_metric(l.get("ebitda_margin"), bm.get("avg_ebitda_margin", 0.2)) * 0.4 +
            score_metric(l.get("net_margin"),    bm.get("avg_net_margin", 0.1))    * 0.3 +
            score_metric(l.get("roe"),           bm.get("avg_roe", 0.15))          * 0.3
        )
        growth = (
            score_metric(l.get("revenue_growth"), bm.get("avg_revenue_growth", 0.08)) * 0.5 +
            score_metric(l.get("ebitda_growth"),  bm.get("avg_revenue_growth", 0.08)) * 0.3 +
            min(100, max(0, l.get("roic", 0) * 500)) * 0.2
        )
        cashflow = (
            score_metric(l.get("fcf_margin"), 0.08) * 0.4 +
            min(100, max(0, l.get("cfo_to_ni", 0) * 80)) * 0.4 +
            score_metric(1 - l.get("capex_intensity", 0.05), 0.95) * 0.2
        )
        balance_sheet = (
            score_metric(l.get("debt_ebitda", 2), bm.get("avg_debt_ebitda", 2.5), False) * 0.4 +
            min(100, max(0, l.get("current_ratio", 1) * 50)) * 0.3 +
            min(100, max(0, l.get("interest_coverage", 3) * 8)) * 0.3
        )
        efficiency = (
            min(100, max(0, l.get("asset_turnover", 0.5) * 60)) * 0.4 +
            score_metric(l.get("current_ratio"), bm.get("avg_current_ratio", 1.5)) * 0.3 +
            min(100, max(0, 100 - l.get("ccc", 60))) * 0.3
        )
        valuation = 55  # Default neutral — market data context needed

        risk_penalty = len([f for f in self.generate_risk_flags_ai(kpis) if f["severity"] == "high"]) * 5
        risk_penalty += len([f for f in self.generate_risk_flags_ai(kpis) if f["severity"] == "medium"]) * 2

        total = (
            profitability  * 0.22 +
            growth         * 0.20 +
            cashflow       * 0.18 +
            balance_sheet  * 0.18 +
            efficiency     * 0.12 +
            valuation      * 0.10 -
            risk_penalty
        )

        return {
            "profitability":  round(min(100, max(0, profitability))),
            "growth":         round(min(100, max(0, growth))),
            "cashflow":       round(min(100, max(0, cashflow))),
            "balance_sheet":  round(min(100, max(0, balance_sheet))),
            "efficiency":     round(min(100, max(0, efficiency))),
            "valuation":      round(valuation),
            "risk_penalty":   round(min(30, max(0, risk_penalty))),
            "total":          round(min(100, max(0, total))),
        }

    def score_label(self, score: float) -> tuple[str, str]:
        if score >= 80: return "Excellent", "#00d4aa"
        if score >= 65: return "Strong",    "#4ade80"
        if score >= 50: return "Moderate",  "#facc15"
        if score >= 35: return "Weak",      "#f97316"
        return "High Concern", "#ef4444"

# Singleton
_analyst_instance = None

def get_analyst() -> AIAnalyst:
    global _analyst_instance
    if _analyst_instance is None:
        _analyst_instance = AIAnalyst()
    return _analyst_instance
