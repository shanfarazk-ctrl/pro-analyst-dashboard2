"""
pages/main_dashboard.py
Full Streamlit dashboard UI — all 8 tabs, sidebar, upload support.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import time
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data_fetchers.fetcher import get_fetcher, POPULAR_EXCHANGES, EXCHANGE_SUFFIX
from ai_engine.analyst import get_analyst
from utils.charts import (
    area_trend, bar_chart, line_chart, peer_bar,
    radar_chart, gauge_chart, comparison_heatmap,
    valuation_band, dupont_breakdown
)
from utils.benchmarks import get_benchmarks, SECTORS

# ─── HELPERS ─────────────────────────────────────────────────────────────────
def _pct(n, d=1):
    if n is None: return "—"
    return f"{float(n)*100:.{d}f}%"

def _x(n, d=1):
    if n is None: return "—"
    return f"{float(n):.{d}f}x"

def _m(n):
    if not n: return "—"
    n = abs(float(n))
    if n >= 1e12: return f"{n/1e12:.2f}T"
    if n >= 1e9:  return f"{n/1e9:.2f}B"
    if n >= 1e6:  return f"{n/1e6:.2f}M"
    if n >= 1e3:  return f"{n/1e3:.1f}K"
    return f"{n:.0f}"

def _delta_color(val, good_direction="up"):
    if val is None: return "off"
    if good_direction == "up":   return "normal" if val >= 0 else "inverse"
    else:                        return "inverse" if val >= 0 else "normal"

def score_color(s):
    if s >= 80: return "#00d4aa"
    if s >= 65: return "#4ade80"
    if s >= 50: return "#facc15"
    if s >= 35: return "#f97316"
    return "#ef4444"

def severity_icon(s):
    return {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(s, "⚪")

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding: 10px 0 20px;">
            <div style="font-size:28px;">⬡</div>
            <div style="font-size:16px; font-weight:800; letter-spacing:1px;">PRO ANALYST</div>
            <div style="font-size:10px; color:rgba(255,255,255,0.35); text-transform:uppercase; letter-spacing:1px;">Financial Intelligence</div>
        </div>
        <hr style="border-color:rgba(255,255,255,0.07); margin-bottom:20px;">
        """, unsafe_allow_html=True)

        # Company type toggle
        company_type = st.radio("Company Type", ["🏛️ Listed Company", "🔒 Private Company (Upload)"], label_visibility="collapsed")
        is_private = "Private" in company_type

        company_data = None
        ticker = ""
        exchange = ""

        if is_private:
            st.markdown("#### 📤 Upload Financial Data")
            st.markdown('<div style="font-size:11px; color:rgba(255,255,255,0.4);">Upload Excel/CSV with Income Statement, Balance Sheet & Cash Flow in rows</div>', unsafe_allow_html=True)
            st.markdown(f"<div style='font-size:10px; color:rgba(255,255,255,0.35);'>Debug: FMP key present = {bool(get_fetcher().fmp_key)}; Alpha Vantage key present = {bool(get_fetcher().av_key)}</div>", unsafe_allow_html=True)
            uploaded = st.file_uploader("", type=["xlsx", "csv", "xls"], label_visibility="collapsed")
            company_name_input = st.text_input("Company Name", placeholder="e.g. Acme Industries")
            industry_input     = st.selectbox("Industry", SECTORS, index=SECTORS.index("Consumer Staples") if "Consumer Staples" in SECTORS else 0)
            country_input      = st.text_input("Country", placeholder="e.g. Pakistan")

            if uploaded and st.button("🔍 Analyze Uploaded Data", use_container_width=True):
                with st.spinner("Parsing uploaded financial data..."):
                    fetcher = get_fetcher()
                    try:
                        if uploaded.name.endswith(".csv"):
                            df = pd.read_csv(uploaded, index_col=0)
                        else:
                            xl = pd.ExcelFile(uploaded)
                            # Auto-detect best sheet
                            sheet = xl.sheet_names[0]
                            for s in xl.sheet_names:
                                if any(kw in s.lower() for kw in ["income", "p&l", "financial", "summary"]):
                                    sheet = s; break
                            df = xl.parse(sheet, index_col=0)
                        company_data = fetcher.parse_uploaded_financials(df)
                        company_data["profile"]["name"]     = company_name_input or "Private Co."
                        company_data["profile"]["industry"] = industry_input
                        company_data["profile"]["country"]  = country_input
                        company_data["profile"]["sector"]   = industry_input
                        st.session_state["company_data"] = company_data
                        st.session_state["company_type"] = "private"
                        st.success("✅ Data parsed successfully!")
                    except Exception as e:
                        st.error(f"Parse error: {e}")

            # Download sample template
            st.markdown("---")
            if st.button("📥 Download Template", use_container_width=True):
                sample = _create_upload_template()
                st.download_button("Save Template", sample, "financial_template.xlsx",
                                  mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                  use_container_width=True)

        else:
            st.markdown("#### 🔍 Select Listed Company")
            exchange_label = st.selectbox("Stock Exchange", list(POPULAR_EXCHANGES.keys()))
            exchange       = POPULAR_EXCHANGES[exchange_label]
            ticker         = st.text_input("Ticker Symbol", placeholder="e.g. NESTLE, AAPL, RELIANCE",
                                           help="Enter the ticker as listed on the selected exchange").upper().strip()

            if ticker:
                if st.button(f"📊 Load {ticker}", use_container_width=True, type="primary"):
                    with st.spinner(f"Fetching {ticker} data..."):
                        fetcher = get_fetcher()
                        data = fetcher.fetch_company_data(ticker, exchange)
                        if data.get("success"):
                            st.session_state["company_data"] = data
                            st.session_state["company_type"] = "public"
                            st.success(f"✅ Loaded: {data['profile']['name']}")
                        else:
                            st.error(f"Could not fetch data: {data.get('error', 'Unknown error')}. Try the full Yahoo Finance ticker (e.g. NESTLE.KA)")

        st.markdown("---")
        st.markdown("#### 👥 Add Peer Companies")
        peer_tickers = []
        for i in range(1, 4):
            pt = st.text_input(f"Peer {i} Ticker", key=f"peer_{i}", placeholder=f"e.g. PEER{i}").upper().strip()
            if pt:
                peer_tickers.append(pt)

        if peer_tickers and st.button("Load Peers", use_container_width=True):
            fetcher = get_fetcher()
            peers   = []
            peer_exchange = st.session_state.get("peer_exchange", exchange or "NYSE")
            for pt in peer_tickers:
                with st.spinner(f"Loading {pt}..."):
                    pd_ = fetcher.fetch_company_data(pt, peer_exchange)
                    if pd_.get("success"):
                        peers.append(pd_)
            if peers:
                st.session_state["peers_data"] = peers
                st.success(f"✅ Loaded {len(peers)} peers")

        st.markdown("---")
        st.markdown("#### ⚙️ Analysis Settings")
        scenario      = st.select_slider("Scenario", ["Bear", "Base", "Bull"], value="Base")
        analysis_years = st.slider("Years of History", 3, 10, 5)

        st.session_state["scenario"]       = scenario
        st.session_state["analysis_years"] = analysis_years

        st.markdown("---")
        st.markdown('<div style="font-size:10px; color:rgba(255,255,255,0.2); text-align:center;">Data: Yahoo Finance · FMP · World Bank<br>AI: Anthropic Claude<br>v2.0 · PRO ANALYST</div>', unsafe_allow_html=True)

    return st.session_state.get("company_data"), st.session_state.get("peers_data", [])

# ─── MAIN RENDER ─────────────────────────────────────────────────────────────
def render_dashboard():
    company_data, peers_data = render_sidebar()

    if not company_data:
        _render_landing()
        return

    source = company_data.get("source", "unknown")
    source_msg = {
        "fmp": "✅ Live data from FMP is active.",
        "yfinance": "✅ Live data from Yahoo Finance is active (may be rate-limited).",
        "demo": "⚠️ Demo Data Mode — Fallback test data is active.",
    }.get(source, f"ℹ️ Data source: {source}")

    if source == "demo" or company_data.get("is_demo"):
        st.warning(
            f"{source_msg} Add `FMP_API_KEY` to Streamlit Cloud secrets for live data. View Setup Guide →",
            icon="🔑"
        )
    elif source in ["fmp", "yfinance"]:
        st.success(source_msg)
    else:
        st.info(source_msg)

    if company_data.get("error"):
        st.caption(f"Fetch log: {company_data.get('error')}")

    profile = company_data.get("profile", {})
    kpis      = company_data.get("kpis", [])
    mkt       = company_data.get("market_data", {})
    is_private = company_data.get("source") == "upload"

    if not kpis:
        st.error("No financial data available for this company. Try a different ticker.")
        return

    latest    = kpis[-1]
    oldest    = kpis[0]
    scenario  = st.session_state.get("scenario", "Base")
    benchmarks = get_benchmarks(profile.get("industry", "Unknown"))
    analyst   = get_analyst()
    scores    = analyst.calc_score(kpis, benchmarks)
    risk_flags = analyst.generate_risk_flags_ai(kpis)

    # ── COMPANY HEADER ────────────────────────────────────────────────────────
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        <div style="margin-bottom:8px;">
            <span style="font-size:26px; font-weight:800; letter-spacing:-0.5px;">{profile.get('name','Unknown')}</span>
            {"<span style='background:rgba(0,212,170,0.12); border:1px solid rgba(0,212,170,0.3); color:#00d4aa; border-radius:6px; padding:3px 10px; font-size:11px; font-weight:600; margin-left:10px;'>PUBLIC</span>" if not is_private else "<span style='background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.3); color:#818cf8; border-radius:6px; padding:3px 10px; font-size:11px; font-weight:600; margin-left:10px;'>PRIVATE</span>"}
        </div>
        <div style="color:rgba(255,255,255,0.45); font-size:13px;">
            {profile.get('sector','—')} · {profile.get('industry','—')} · {profile.get('country','—')} · {profile.get('currency','USD')}
            {"· Market Cap: " + _m(mkt.get('market_cap')) if not is_private and mkt.get('market_cap') else ""}
        </div>
        """, unsafe_allow_html=True)

        # Scenario badge
        scen_colors = {"Bull": "#4ade80", "Base": "#00d4aa", "Bear": "#ef4444"}
        st.markdown(f'<span style="background:{scen_colors[scenario]}22; border:1px solid {scen_colors[scenario]}44; color:{scen_colors[scenario]}; border-radius:6px; padding:3px 12px; font-size:11px; font-weight:700;">⬡ {scenario.upper()} CASE</span>', unsafe_allow_html=True)

    with col2:
        if risk_flags:
            high_count = len([f for f in risk_flags if f["severity"] == "high"])
            st.markdown(f'<div style="text-align:right; padding-top:8px;"><span style="color:#ef4444; font-size:13px; font-weight:700;">⚠ {len(risk_flags)} Risks ({high_count} High)</span></div>', unsafe_allow_html=True)

    st.markdown('<hr style="border-color:rgba(255,255,255,0.07); margin:12px 0;">', unsafe_allow_html=True)

    # ── TABS ──────────────────────────────────────────────────────────────────
    tabs = st.tabs(["📊 Overview", "📈 Profitability", "💰 Cash Flow", "🏦 Balance Sheet", "👥 Peers", "💎 Valuation", "🌍 Macro & Risk", "🤖 AI Report"])

    # ── TAB 1: OVERVIEW ───────────────────────────────────────────────────────
    with tabs[0]:
        # Score gauges
        st.markdown("#### Financial Health Scorecard")
        gc = st.columns(7)
        score_items = [
            ("Overall", scores["total"]), ("Profitability", scores["profitability"]),
            ("Growth", scores["growth"]), ("Cash Flow", scores["cashflow"]),
            ("Bal. Sheet", scores["balance_sheet"]), ("Efficiency", scores["efficiency"]),
            ("Valuation", scores["valuation"]),
        ]
        for col, (label, score) in zip(gc, score_items):
            with col:
                sl, sc = analyst.score_label(score)
                st.plotly_chart(gauge_chart(score, label, 160), use_container_width=True, config={"displayModeBar": False})

        # KPI cards
        st.markdown("#### Key Metrics")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Revenue", _m(latest["revenue"]),
                     delta=_pct(latest.get("revenue_growth")),
                     delta_color=_delta_color(latest.get("revenue_growth")))
            st.metric("EBITDA Margin", _pct(latest["ebitda_margin"]),
                     delta=f"Ind avg {_pct(benchmarks.get('avg_ebitda_margin'))}",
                     delta_color=_delta_color(latest["ebitda_margin"] - (benchmarks.get("avg_ebitda_margin") or 0.18)))
        with c2:
            st.metric("Net Margin",  _pct(latest["net_margin"]))
            st.metric("ROE",         _pct(latest["roe"]),
                     delta=f"Ind avg {_pct(benchmarks.get('avg_roe'))}",
                     delta_color=_delta_color(latest["roe"] - (benchmarks.get("avg_roe") or 0.15)))
        with c3:
            st.metric("FCF Margin",  _pct(latest["fcf_margin"]),
                     delta="positive" if latest["fcf_margin"] > 0 else "negative",
                     delta_color="normal" if latest["fcf_margin"] > 0 else "inverse")
            st.metric("Debt/EBITDA", _x(latest["debt_ebitda"]),
                     delta_color=_delta_color(-latest["debt_ebitda"]))
        with c4:
            st.metric("Current Ratio",    f"{latest['current_ratio']:.2f}x",
                     delta_color=_delta_color(latest["current_ratio"] - 1.2))
            st.metric("Interest Coverage", _x(latest["interest_coverage"]),
                     delta_color=_delta_color(latest["interest_coverage"] - 3))

        # Charts row
        c1, c2 = st.columns(2)
        with c1:
            fig = area_trend(kpis, [
                ("revenue", "Revenue", "#00d4aa"),
                ("ebitda",  "EBITDA",  "#6366f1"),
                ("net_income", "Net Income", "#f59e0b"),
            ], "Revenue, EBITDA & Net Income Trend")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with c2:
            cats = ["Profitability", "Growth", "Cash Flow", "Balance Sheet", "Efficiency", "Valuation"]
            comp_vals = [scores[k] for k in ["profitability","growth","cashflow","balance_sheet","efficiency","valuation"]]
            ind_vals  = [60, 55, 58, 62, 57, 60]
            fig = radar_chart(cats, comp_vals, ind_vals, profile.get("name", "Company"))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Risk flags
        if risk_flags:
            st.markdown("#### ⚠️ Risk & Red Flags")
            for chunk in [risk_flags[i:i+2] for i in range(0, len(risk_flags), 2)]:
                cols = st.columns(2)
                for col, flag in zip(cols, chunk):
                    with col:
                        sev_colors = {"high": "#ef4444", "medium": "#f97316", "low": "#facc15"}
                        c = sev_colors.get(flag["severity"], "#facc15")
                        st.markdown(f"""
                        <div style="background:rgba(255,255,255,0.03); border:1px solid {c}44; border-left:3px solid {c}; border-radius:8px; padding:10px 14px;">
                            <div style="color:{c}; font-weight:700; font-size:12px;">{flag['type']}</div>
                            <div style="color:rgba(255,255,255,0.6); font-size:12px; margin-top:3px;">{flag['msg']}</div>
                        </div>
                        """, unsafe_allow_html=True)

    # ── TAB 2: PROFITABILITY ──────────────────────────────────────────────────
    with tabs[1]:
        c1, c2, c3, c4 = st.columns(4)
        metrics_p = [
            (c1, "Gross Margin",  _pct(latest["gross_margin"])),
            (c2, "EBITDA Margin", _pct(latest["ebitda_margin"])),
            (c3, "Net Margin",    _pct(latest["net_margin"])),
            (c4, "ROIC",          _pct(latest["roic"])),
        ]
        for col, label, val in metrics_p:
            col.metric(label, val)

        c1, c2 = st.columns(2)
        with c1:
            fig = line_chart(kpis, [
                ("ebitda_margin", "EBITDA Margin", "#00d4aa"),
                ("net_margin",    "Net Margin",    "#6366f1"),
                ("gross_margin",  "Gross Margin",  "#f59e0b"),
            ], "Margin Trends", pct=True,
            reference_lines=[(benchmarks.get("avg_ebitda_margin",0.18)*100, "Ind EBITDA Avg", "#f59e0b")])
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with c2:
            fig = line_chart(kpis, [
                ("roe",  "ROE",  "#00d4aa"),
                ("roa",  "ROA",  "#6366f1"),
                ("roic", "ROIC", "#f59e0b"),
            ], "Return Ratios", pct=True,
            reference_lines=[(benchmarks.get("avg_roe",0.15)*100, "Ind ROE Avg", "#f59e0b")])
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        c1, c2 = st.columns(2)
        with c1:
            fig = bar_chart(kpis, [
                ("revenue",    "Revenue",    "#00d4aa"),
                ("ebitda",     "EBITDA",     "#6366f1"),
                ("net_income", "Net Income", "#f59e0b"),
            ], "Revenue & Earnings (Absolute)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with c2:
            fig = dupont_breakdown(latest)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── TAB 3: CASH FLOW ──────────────────────────────────────────────────────
    with tabs[2]:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("CFO Margin",  _pct(latest["cfo_margin"]))
        c2.metric("FCF Margin",  _pct(latest["fcf_margin"]))
        c3.metric("CFO / NI",    f"{latest['cfo_to_ni']:.2f}x",
                 delta="Quality OK" if latest["cfo_to_ni"] > 0.9 else "⚠ Quality Risk",
                 delta_color="normal" if latest["cfo_to_ni"] > 0.9 else "inverse")
        c4.metric("Capex / Rev", _pct(latest["capex_intensity"]))

        c1, c2 = st.columns(2)
        with c1:
            fig = bar_chart(kpis, [
                ("cfo", "Operating CF",   "#00d4aa"),
                ("net_income", "Net Income", "#6366f1"),
            ], "Cash Flow vs Earnings Quality",
            reference_lines=None)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with c2:
            fig = area_trend(kpis, [
                ("fcf",   "Free Cash Flow", "#4ade80"),
                ("capex", "Capex",          "#ef4444"),
            ], "FCF & Capex Trend")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        fig = line_chart(kpis, [
            ("cfo_margin", "CFO Margin",  "#00d4aa"),
            ("fcf_margin", "FCF Margin",  "#4ade80"),
        ], "Cash Margins Trend", pct=True)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── TAB 4: BALANCE SHEET ──────────────────────────────────────────────────
    with tabs[3]:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Debt/EBITDA",    _x(latest["debt_ebitda"]))
        c2.metric("Net Debt/EBITDA",_x(latest["net_debt_ebitda"]))
        c3.metric("Current Ratio",  f"{latest['current_ratio']:.2f}x")
        c4.metric("Int. Coverage",  _x(latest["interest_coverage"]))

        c1, c2 = st.columns(2)
        with c1:
            fig = line_chart(kpis, [
                ("debt_ebitda",     "Debt/EBITDA",     "#ef4444"),
                ("net_debt_ebitda", "Net Debt/EBITDA", "#f97316"),
            ], "Leverage Ratios Trend",
            reference_lines=[(4.0, "Danger 4x", "#ef4444"), (2.5, "Ind Avg", "#f59e0b")])
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with c2:
            fig = line_chart(kpis, [
                ("current_ratio", "Current Ratio", "#00d4aa"),
                ("quick_ratio",   "Quick Ratio",   "#6366f1"),
            ], "Liquidity Ratios Trend",
            reference_lines=[(1.0, "Min Safe", "#ef4444"), (1.5, "Comfort", "#f59e0b")])
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        c1, c2 = st.columns(2)
        with c1:
            fig = line_chart(kpis, [
                ("interest_coverage", "Interest Coverage", "#4ade80"),
            ], "Interest Coverage Trend",
            reference_lines=[(2.0, "Min 2x", "#ef4444"), (3.0, "Safe 3x", "#f59e0b")])
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with c2:
            # Working capital efficiency
            fig = line_chart(kpis, [
                ("receivable_days", "Receivable Days", "#00d4aa"),
                ("inventory_days",  "Inventory Days",  "#f59e0b"),
                ("payable_days",    "Payable Days",    "#6366f1"),
                ("ccc",             "CCC",             "#ef4444"),
            ], "Working Capital Efficiency (Days)")
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── TAB 5: PEERS ──────────────────────────────────────────────────────────
    with tabs[4]:
        if not peers_data:
            st.info("👈 Add peer companies in the sidebar to enable peer comparison analysis.")
        else:
            all_companies = [company_data] + peers_data
            all_names     = [d["profile"]["name"] for d in all_companies]
            selected_name = profile.get("name", "Company")

            # Build comparison table
            metrics_to_compare = [
                ("ebitda_margin",  "EBITDA Margin",  True,  100,  "%"),
                ("net_margin",     "Net Margin",      True,  100,  "%"),
                ("roe",            "ROE",             True,  100,  "%"),
                ("roic",           "ROIC",            True,  100,  "%"),
                ("debt_ebitda",    "Debt/EBITDA",     False, 1,    "x"),
                ("current_ratio",  "Current Ratio",   True,  1,    "x"),
                ("fcf_margin",     "FCF Margin",      True,  100,  "%"),
                ("revenue_growth", "Revenue Growth",  True,  100,  "%"),
                ("asset_turnover", "Asset Turnover",  True,  1,    "x"),
            ]

            rows = []
            for metric_key, metric_label, higher_is_better, multiplier, unit in metrics_to_compare:
                row = {"Metric": metric_label}
                for d in all_companies:
                    k = d.get("kpis", [{}])[-1] if d.get("kpis") else {}
                    v = k.get(metric_key)
                    row[d["profile"]["name"]] = round(float(v) * multiplier, 1) if v is not None else None
                rows.append(row)

            df_compare = pd.DataFrame(rows).set_index("Metric")

            # Highlight best in green
            st.markdown("#### 📊 Peer Comparison Matrix")
            st.dataframe(df_compare.style.highlight_max(axis=1, color="rgba(0,212,170,0.3)")
                        .format("{:.1f}", na_rep="—"), use_container_width=True)

            # Ranked bar charts
            st.markdown("#### Ranked Peer Charts")
            c1, c2, c3 = st.columns(3)
            chart_metrics = [
                ("ebitda_margin", "EBITDA Margin", "%", True, c1),
                ("roe",           "ROE",           "%", True, c2),
                ("debt_ebitda",   "Debt/EBITDA",   "x", False, c3),
            ]
            for key, label, unit, higher_better, col in chart_metrics:
                vals = []
                names = []
                for d in all_companies:
                    k = d.get("kpis", [{}])[-1] if d.get("kpis") else {}
                    v = k.get(key)
                    if v is not None:
                        vals.append(float(v) * (100 if unit == "%" else 1))
                        names.append(d["profile"]["name"])
                if vals:
                    threshold = None
                    if key == "debt_ebitda": threshold = 4.0
                    fig = peer_bar(names, vals, label, highlight=selected_name,
                                  height=220, suffix=unit, threshold=threshold)
                    col.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── TAB 6: VALUATION ──────────────────────────────────────────────────────
    with tabs[5]:
        if is_private:
            st.info("💡 Valuation multiples not available for private companies. Showing implied EV estimate based on EBITDA.")
            # Implied EV
            ebitda = latest.get("ebitda", 0)
            peer_ev_ebitda = benchmarks.get("avg_ev_ebitda", 12)
            implied_ev = ebitda * peer_ev_ebitda
            c1, c2, c3 = st.columns(3)
            c1.metric("EBITDA", _m(ebitda))
            c2.metric("Industry EV/EBITDA", f"{peer_ev_ebitda:.1f}x")
            c3.metric("Implied EV (Est.)",  _m(implied_ev))
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("P/E Ratio",    f"{mkt.get('pe',0) or 0:.1f}x",  delta=f"Ind avg {benchmarks.get('avg_pe',20):.1f}x")
            c2.metric("EV/EBITDA",   f"{mkt.get('ev_ebitda',0) or 0:.1f}x", delta=f"Ind avg {benchmarks.get('avg_ev_ebitda',12):.1f}x")
            c3.metric("P/B Ratio",   f"{mkt.get('pb',0) or 0:.1f}x")
            c4.metric("Div. Yield",  f"{mkt.get('div_yield',0) or 0:.1f}%")

            c1, c2 = st.columns(2)
            with c1:
                if peers_data:
                    names = [profile.get("name","Co.")] + [p["profile"]["name"] for p in peers_data]
                    pe_vals = [mkt.get("pe", 0) or 0] + [p.get("market_data", {}).get("pe", 0) or 0 for p in peers_data]
                    fig = peer_bar(names, pe_vals, "P/E vs Peers", highlight=profile.get("name"), suffix="x", height=220)
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("Add peers to enable comparison")
            with c2:
                fig = valuation_band(kpis, mkt)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        # Scenario table
        st.markdown("#### 📋 Scenario Analysis")
        scenario_data = pd.DataFrame([
            {"Scenario": "🟢 Bull", "Rev Growth Adj": "+5%", "EBITDA Margin Adj": "+200bps", "Multiple Adj": "+2x", "Implied View": "Upside 20–35%"},
            {"Scenario": "🟡 Base", "Rev Growth Adj": "Consensus", "EBITDA Margin Adj": "Stable", "Multiple Adj": "No change", "Implied View": "Fair Value"},
            {"Scenario": "🔴 Bear", "Rev Growth Adj": "-5%", "EBITDA Margin Adj": "-200bps", "Multiple Adj": "-2x", "Implied View": "Downside 15–25%"},
        ]).set_index("Scenario")
        st.dataframe(scenario_data, use_container_width=True)

    # ── TAB 7: MACRO & RISK ───────────────────────────────────────────────────
    with tabs[6]:
        country = profile.get("country", "USA")
        st.markdown(f"#### 🌍 Macro Environment: {country}")

        if st.button("🔄 Fetch Live Macro Data", use_container_width=False):
            with st.spinner(f"Fetching macro indicators for {country}..."):
                fetcher = get_fetcher()
                macro   = fetcher.fetch_macro_data(country)
                st.session_state["macro_data"] = macro

        macro = st.session_state.get("macro_data", {})
        if macro:
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            indicators = [
                (c1, "GDP Growth",    macro.get("gdp_growth"),    "%"),
                (c2, "Inflation",     macro.get("inflation"),     "%"),
                (c3, "Unemployment",  macro.get("unemployment"),  "%"),
                (c4, "Lending Rate",  macro.get("interest_rate"), "%"),
                (c5, "Current Acc.",  macro.get("current_acc"),   "% of GDP"),
                (c6, "Public Debt",   macro.get("public_debt"),   "% of GDP"),
            ]
            for col, label, val, unit in indicators:
                v_str = f"{val:.1f}{unit}" if val is not None else "N/A"
                col.metric(label, v_str)
        else:
            st.info("Click 'Fetch Live Macro Data' to load real-time macro indicators for " + country)

        st.markdown("---")
        st.markdown("#### ⚠️ Risk Register")
        risk_data = pd.DataFrame([
            {"Risk": "Currency Depreciation", "Category": "Macro", "Severity": "HIGH", "Impact": "Input cost inflation, debt burden", "Mitigation": "FX hedging, USD revenue offset"},
            {"Risk": "Interest Rate Spike",   "Category": "Macro", "Severity": "MEDIUM","Impact": "Higher financing costs", "Mitigation": "Fixed-rate debt, low leverage"},
            {"Risk": "Commodity Price Surge", "Category": "Micro", "Severity": "HIGH",  "Impact": "Margin compression",    "Mitigation": "Pricing power, hedging"},
            {"Risk": "Competitive Entry",     "Category": "Micro", "Severity": "MEDIUM","Impact": "Market share loss",      "Mitigation": "Brand investment, moat"},
            {"Risk": "Regulatory Change",     "Category": "Country","Severity": "LOW",  "Impact": "Compliance cost",        "Mitigation": "Diversification"},
            {"Risk": "Demand Slowdown",       "Category": "Macro", "Severity": "MEDIUM","Impact": "Revenue miss",           "Mitigation": "Product diversification"},
        ])
        st.dataframe(risk_data.style.apply(
            lambda col: ["color: #ef4444" if v == "HIGH" else "color: #f97316" if v == "MEDIUM" else "color: #facc15" for v in col] if col.name == "Severity" else ["" for _ in col], axis=0
        ), use_container_width=True)

    # ── TAB 8: AI REPORT ──────────────────────────────────────────────────────
    with tabs[7]:
        st.markdown("#### 🤖 AI Equity Research Report")
        st.markdown(f'<div style="color:rgba(255,255,255,0.4); font-size:12px; margin-bottom:16px;">Powered by Anthropic Claude · {profile.get("name","Company")} · {scenario} Case · Generated {pd.Timestamp.now().strftime("%d %b %Y")}</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            generate_btn = st.button("✦ Generate Full AI Analysis", type="primary", use_container_width=True)
        with col2:
            quick_mode = st.checkbox("Quick Mode (faster)", value=False)
        with col3:
            if st.button("📥 Export as Text", use_container_width=True):
                report = st.session_state.get("ai_report", "No report generated yet.")
                st.download_button("Download Report", report, f"analyst_report_{profile.get('name','co').replace(' ','_')}.txt",
                                  use_container_width=True)

        if generate_btn:
            macro_data  = st.session_state.get("macro_data", {})
            report_container = st.empty()

            with st.spinner("Generating institutional-grade analysis..."):
                analyst     = get_analyst()
                report_text = analyst.generate_full_analysis(
                    company_data, peers_data, macro_data, benchmarks, scenario
                )
                st.session_state["ai_report"] = report_text

            # Display formatted
            st.markdown("""
            <div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:28px 32px; max-width:900px;">
            """, unsafe_allow_html=True)
            st.markdown(st.session_state.get("ai_report", ""), unsafe_allow_html=False)
            st.markdown("</div>", unsafe_allow_html=True)

        elif st.session_state.get("ai_report"):
            st.markdown("""<div style="background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.08); border-radius:16px; padding:28px 32px;">""", unsafe_allow_html=True)
            st.markdown(st.session_state.get("ai_report", ""), unsafe_allow_html=False)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="text-align:center; padding:60px 20px; background:rgba(255,255,255,0.02); border:1px dashed rgba(0,212,170,0.2); border-radius:16px;">
                <div style="font-size:36px; margin-bottom:12px;">✦</div>
                <div style="font-size:16px; font-weight:600; color:rgba(255,255,255,0.7);">AI Analysis Ready</div>
                <div style="font-size:13px; color:rgba(255,255,255,0.35); margin-top:8px;">Click Generate to create a full institutional-grade equity research report<br>covering profitability, growth, risk, macro environment, and investment thesis</div>
            </div>
            """, unsafe_allow_html=True)

# ─── LANDING PAGE ─────────────────────────────────────────────────────────────
def _render_landing():
    st.markdown("""
    <div style="text-align:center; padding: 60px 20px 40px;">
        <div style="font-size:52px; margin-bottom:8px;">⬡</div>
        <h1 style="font-size:36px; font-weight:900; letter-spacing:-1px; margin:0;">PRO ANALYST</h1>
        <p style="color:rgba(255,255,255,0.4); font-size:15px; margin-top:8px;">
            Institutional-grade financial intelligence for any listed or private company worldwide
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    features = [
        ("🌐", "Global Coverage", "Any listed company from 15+ exchanges: PSX, NSE, TADAWUL, NYSE, LSE, HKEX and more"),
        ("🔒", "Private Companies", "Upload your own Excel/CSV financials and get full institutional-grade analysis"),
        ("🤖", "AI Analysis", "Claude-powered equity research: profitability, risk, macro/micro economics, investment thesis"),
        ("⚠️", "Risk Engine", "Auto-generated risk flags, macro indicators, scenario analysis — Bull, Base, Bear"),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3, c4], features):
        with col:
            st.markdown(f"""
            <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.08); border-radius:14px; padding:20px; text-align:center; height:160px;">
                <div style="font-size:28px;">{icon}</div>
                <div style="font-weight:700; font-size:14px; margin:8px 0 6px;">{title}</div>
                <div style="color:rgba(255,255,255,0.4); font-size:12px; line-height:1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("👈 **Get started:** Select a company type and enter a ticker in the sidebar, or upload private company financials.")

# ─── TEMPLATE GENERATOR ───────────────────────────────────────────────────────
def _create_upload_template():
    """Generate a sample Excel template for private company upload."""
    import io
    rows = {
        "Metric": [
            "Revenue", "Cost of Goods Sold", "Gross Profit", "EBITDA", "EBIT",
            "Net Income", "Depreciation & Amortization", "Interest Expense", "Tax Expense",
            "— Balance Sheet —",
            "Total Assets", "Total Equity", "Total Debt", "Cash & Equivalents",
            "Current Assets", "Current Liabilities", "Inventory", "Accounts Receivable", "Accounts Payable",
            "— Cash Flow —",
            "Operating Cash Flow", "Capital Expenditure", "Free Cash Flow",
        ],
        "2019": [50000, 30000, 20000, 10000, 8500, 5500, 1500, 800, 1500,
                 "", 40000, 15000, 12000, 3000, 15000, 10000, 4000, 5000, 6000,
                 "", 8000, 2000, 6000],
        "2020": [55000, 32000, 23000, 11500, 9800, 6500, 1700, 850, 1700,
                 "", 44000, 17000, 12500, 3500, 17000, 11000, 4200, 5500, 6500,
                 "", 9200, 2200, 7000],
        "2021": [62000, 36000, 26000, 13000, 11200, 7500, 1800, 900, 1800,
                 "", 49000, 19500, 13000, 4000, 19500, 12000, 4600, 6000, 7000,
                 "", 10500, 2400, 8100],
        "2022": [70000, 40000, 30000, 15000, 13000, 8800, 2000, 950, 2000,
                 "", 55000, 22000, 13500, 5000, 22000, 13500, 5000, 6800, 7800,
                 "", 12000, 2700, 9300],
        "2023": [80000, 45000, 35000, 17500, 15200, 10500, 2300, 1000, 2300,
                 "", 63000, 25500, 14000, 6000, 25500, 15000, 5500, 7800, 8800,
                 "", 14000, 3000, 11000],
    }
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Financials", index=False)
        ws = writer.sheets["Financials"]
        ws.column_dimensions["A"].width = 32
        for col in ["B", "C", "D", "E", "F"]:
            ws.column_dimensions[col].width = 14
    buf.seek(0)
    return buf.read()
