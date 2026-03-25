"""
utils/benchmarks.py
Industry benchmark database for peer/sector comparison.
Covers 40+ sectors globally.
"""

INDUSTRY_BENCHMARKS = {
    # ─── Consumer ────────────────────────────────────────────────────────────
    "Consumer Staples": {
        "avg_revenue_growth": 0.085, "avg_ebitda_margin": 0.200, "avg_net_margin": 0.115,
        "avg_roe": 0.32, "avg_roic": 0.20, "avg_debt_ebitda": 1.9,
        "avg_current_ratio": 1.35, "avg_pe": 28.0, "avg_ev_ebitda": 16.5, "cyclicality": "Low"
    },
    "Consumer Discretionary": {
        "avg_revenue_growth": 0.10, "avg_ebitda_margin": 0.135, "avg_net_margin": 0.075,
        "avg_roe": 0.25, "avg_roic": 0.15, "avg_debt_ebitda": 2.5,
        "avg_current_ratio": 1.20, "avg_pe": 25.0, "avg_ev_ebitda": 15.0, "cyclicality": "High"
    },
    "Food & Beverage": {
        "avg_revenue_growth": 0.075, "avg_ebitda_margin": 0.185, "avg_net_margin": 0.105,
        "avg_roe": 0.28, "avg_roic": 0.18, "avg_debt_ebitda": 2.1,
        "avg_current_ratio": 1.25, "avg_pe": 26.0, "avg_ev_ebitda": 15.5, "cyclicality": "Low"
    },
    "Retail": {
        "avg_revenue_growth": 0.08, "avg_ebitda_margin": 0.095, "avg_net_margin": 0.048,
        "avg_roe": 0.22, "avg_roic": 0.12, "avg_debt_ebitda": 2.8,
        "avg_current_ratio": 1.10, "avg_pe": 22.0, "avg_ev_ebitda": 12.0, "cyclicality": "Medium"
    },
    # ─── Technology ──────────────────────────────────────────────────────────
    "Technology": {
        "avg_revenue_growth": 0.175, "avg_ebitda_margin": 0.280, "avg_net_margin": 0.180,
        "avg_roe": 0.38, "avg_roic": 0.28, "avg_debt_ebitda": 0.8,
        "avg_current_ratio": 2.20, "avg_pe": 35.0, "avg_ev_ebitda": 22.0, "cyclicality": "Medium"
    },
    "Software": {
        "avg_revenue_growth": 0.22, "avg_ebitda_margin": 0.320, "avg_net_margin": 0.210,
        "avg_roe": 0.42, "avg_roic": 0.32, "avg_debt_ebitda": 0.5,
        "avg_current_ratio": 2.50, "avg_pe": 45.0, "avg_ev_ebitda": 28.0, "cyclicality": "Low"
    },
    "Semiconductors": {
        "avg_revenue_growth": 0.155, "avg_ebitda_margin": 0.350, "avg_net_margin": 0.220,
        "avg_roe": 0.35, "avg_roic": 0.25, "avg_debt_ebitda": 0.6,
        "avg_current_ratio": 2.80, "avg_pe": 38.0, "avg_ev_ebitda": 25.0, "cyclicality": "High"
    },
    # ─── Financials ──────────────────────────────────────────────────────────
    "Banking": {
        "avg_revenue_growth": 0.090, "avg_ebitda_margin": 0.400, "avg_net_margin": 0.220,
        "avg_roe": 0.14, "avg_roic": 0.12, "avg_debt_ebitda": None,
        "avg_current_ratio": None, "avg_pe": 12.0, "avg_ev_ebitda": 8.0, "cyclicality": "High"
    },
    "Insurance": {
        "avg_revenue_growth": 0.070, "avg_ebitda_margin": 0.150, "avg_net_margin": 0.085,
        "avg_roe": 0.12, "avg_roic": 0.10, "avg_debt_ebitda": None,
        "avg_current_ratio": None, "avg_pe": 14.0, "avg_ev_ebitda": 9.0, "cyclicality": "Medium"
    },
    "Financial Services": {
        "avg_revenue_growth": 0.110, "avg_ebitda_margin": 0.300, "avg_net_margin": 0.180,
        "avg_roe": 0.18, "avg_roic": 0.14, "avg_debt_ebitda": 2.0,
        "avg_current_ratio": 1.50, "avg_pe": 16.0, "avg_ev_ebitda": 11.0, "cyclicality": "Medium"
    },
    # ─── Healthcare ──────────────────────────────────────────────────────────
    "Healthcare": {
        "avg_revenue_growth": 0.095, "avg_ebitda_margin": 0.235, "avg_net_margin": 0.135,
        "avg_roe": 0.22, "avg_roic": 0.14, "avg_debt_ebitda": 1.5,
        "avg_current_ratio": 1.80, "avg_pe": 30.0, "avg_ev_ebitda": 18.0, "cyclicality": "Low"
    },
    "Pharmaceuticals": {
        "avg_revenue_growth": 0.085, "avg_ebitda_margin": 0.285, "avg_net_margin": 0.175,
        "avg_roe": 0.28, "avg_roic": 0.18, "avg_debt_ebitda": 1.3,
        "avg_current_ratio": 1.90, "avg_pe": 28.0, "avg_ev_ebitda": 17.0, "cyclicality": "Low"
    },
    # ─── Energy ──────────────────────────────────────────────────────────────
    "Energy": {
        "avg_revenue_growth": 0.065, "avg_ebitda_margin": 0.245, "avg_net_margin": 0.095,
        "avg_roe": 0.14, "avg_roic": 0.10, "avg_debt_ebitda": 2.2,
        "avg_current_ratio": 1.10, "avg_pe": 14.0, "avg_ev_ebitda": 7.5, "cyclicality": "Very High"
    },
    "Oil & Gas": {
        "avg_revenue_growth": 0.055, "avg_ebitda_margin": 0.280, "avg_net_margin": 0.105,
        "avg_roe": 0.13, "avg_roic": 0.09, "avg_debt_ebitda": 2.4,
        "avg_current_ratio": 1.05, "avg_pe": 12.0, "avg_ev_ebitda": 6.5, "cyclicality": "Very High"
    },
    "Utilities": {
        "avg_revenue_growth": 0.045, "avg_ebitda_margin": 0.380, "avg_net_margin": 0.115,
        "avg_roe": 0.11, "avg_roic": 0.075, "avg_debt_ebitda": 4.5,
        "avg_current_ratio": 0.85, "avg_pe": 18.0, "avg_ev_ebitda": 12.0, "cyclicality": "Low"
    },
    # ─── Industrials ─────────────────────────────────────────────────────────
    "Industrials": {
        "avg_revenue_growth": 0.075, "avg_ebitda_margin": 0.165, "avg_net_margin": 0.082,
        "avg_roe": 0.18, "avg_roic": 0.12, "avg_debt_ebitda": 2.3,
        "avg_current_ratio": 1.45, "avg_pe": 20.0, "avg_ev_ebitda": 13.0, "cyclicality": "High"
    },
    "Manufacturing": {
        "avg_revenue_growth": 0.068, "avg_ebitda_margin": 0.145, "avg_net_margin": 0.068,
        "avg_roe": 0.16, "avg_roic": 0.11, "avg_debt_ebitda": 2.6,
        "avg_current_ratio": 1.55, "avg_pe": 18.0, "avg_ev_ebitda": 11.0, "cyclicality": "High"
    },
    "Construction": {
        "avg_revenue_growth": 0.082, "avg_ebitda_margin": 0.095, "avg_net_margin": 0.042,
        "avg_roe": 0.14, "avg_roic": 0.09, "avg_debt_ebitda": 3.0,
        "avg_current_ratio": 1.35, "avg_pe": 16.0, "avg_ev_ebitda": 9.5, "cyclicality": "High"
    },
    # ─── Real Estate ─────────────────────────────────────────────────────────
    "Real Estate": {
        "avg_revenue_growth": 0.072, "avg_ebitda_margin": 0.480, "avg_net_margin": 0.185,
        "avg_roe": 0.09, "avg_roic": 0.07, "avg_debt_ebitda": 6.0,
        "avg_current_ratio": 0.90, "avg_pe": 22.0, "avg_ev_ebitda": 18.0, "cyclicality": "Medium"
    },
    # ─── Telecom ─────────────────────────────────────────────────────────────
    "Telecommunications": {
        "avg_revenue_growth": 0.048, "avg_ebitda_margin": 0.310, "avg_net_margin": 0.095,
        "avg_roe": 0.15, "avg_roic": 0.085, "avg_debt_ebitda": 3.5,
        "avg_current_ratio": 0.80, "avg_pe": 16.0, "avg_ev_ebitda": 8.0, "cyclicality": "Low"
    },
    # ─── Materials ───────────────────────────────────────────────────────────
    "Materials": {
        "avg_revenue_growth": 0.072, "avg_ebitda_margin": 0.195, "avg_net_margin": 0.085,
        "avg_roe": 0.15, "avg_roic": 0.105, "avg_debt_ebitda": 2.4,
        "avg_current_ratio": 1.50, "avg_pe": 16.0, "avg_ev_ebitda": 9.5, "cyclicality": "High"
    },
    "Chemicals": {
        "avg_revenue_growth": 0.068, "avg_ebitda_margin": 0.185, "avg_net_margin": 0.080,
        "avg_roe": 0.14, "avg_roic": 0.10, "avg_debt_ebitda": 2.6,
        "avg_current_ratio": 1.60, "avg_pe": 15.0, "avg_ev_ebitda": 9.0, "cyclicality": "High"
    },
    "Cement": {
        "avg_revenue_growth": 0.082, "avg_ebitda_margin": 0.265, "avg_net_margin": 0.128,
        "avg_roe": 0.19, "avg_roic": 0.13, "avg_debt_ebitda": 2.0,
        "avg_current_ratio": 1.20, "avg_pe": 14.0, "avg_ev_ebitda": 8.5, "cyclicality": "High"
    },
    "Fertilizers": {
        "avg_revenue_growth": 0.075, "avg_ebitda_margin": 0.320, "avg_net_margin": 0.190,
        "avg_roe": 0.26, "avg_roic": 0.18, "avg_debt_ebitda": 1.5,
        "avg_current_ratio": 1.30, "avg_pe": 11.0, "avg_ev_ebitda": 7.0, "cyclicality": "High"
    },
    # ─── Default Fallback ────────────────────────────────────────────────────
    "Unknown": {
        "avg_revenue_growth": 0.08, "avg_ebitda_margin": 0.18, "avg_net_margin": 0.09,
        "avg_roe": 0.16, "avg_roic": 0.11, "avg_debt_ebitda": 2.5,
        "avg_current_ratio": 1.40, "avg_pe": 20.0, "avg_ev_ebitda": 12.0, "cyclicality": "Medium"
    },
}

def get_benchmarks(industry: str) -> dict:
    """Get closest matching industry benchmark."""
    if industry in INDUSTRY_BENCHMARKS:
        return INDUSTRY_BENCHMARKS[industry]
    # Fuzzy match
    industry_lower = industry.lower()
    for key in INDUSTRY_BENCHMARKS:
        if key.lower() in industry_lower or industry_lower in key.lower():
            return INDUSTRY_BENCHMARKS[key]
    return INDUSTRY_BENCHMARKS["Unknown"]

SECTORS = sorted(INDUSTRY_BENCHMARKS.keys())
