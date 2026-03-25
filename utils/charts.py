"""
utils/charts.py
Plotly chart factory for the dashboard.
Dark theme, consistent styling throughout.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Optional

# ─── THEME ───────────────────────────────────────────────────────────────────
COLORS = {
    "primary":   "#00d4aa",
    "secondary": "#6366f1",
    "warning":   "#f59e0b",
    "danger":    "#ef4444",
    "success":   "#4ade80",
    "muted":     "rgba(255,255,255,0.4)",
    "grid":      "rgba(255,255,255,0.05)",
    "bg":        "rgba(0,0,0,0)",
    "paper":     "rgba(0,0,0,0)",
}

PALETTE = ["#00d4aa", "#6366f1", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#84cc16", "#f97316"]

BASE_LAYOUT = dict(
    paper_bgcolor=COLORS["paper"],
    plot_bgcolor=COLORS["bg"],
    font=dict(family="DM Sans, sans-serif", color="white", size=12),
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11, color="rgba(255,255,255,0.6)")),
    xaxis=dict(
        gridcolor=COLORS["grid"], showgrid=True,
        tickfont=dict(color=COLORS["muted"], size=10),
        linecolor="rgba(255,255,255,0.1)", zeroline=False,
    ),
    yaxis=dict(
        gridcolor=COLORS["grid"], showgrid=True,
        tickfont=dict(color=COLORS["muted"], size=10),
        linecolor="rgba(255,255,255,0.1)", zeroline=False,
    ),
)

def _base_fig(**kwargs):
    fig = go.Figure()
    layout = {**BASE_LAYOUT, **kwargs}
    fig.update_layout(**layout)
    return fig

# ─── REVENUE / EBITDA TREND ───────────────────────────────────────────────────
def area_trend(kpis: list[dict], metrics: list[tuple], title: str = "", height: int = 280) -> go.Figure:
    """Area chart for trend data."""
    fig = _base_fig(title=dict(text=title, font=dict(size=13, color="rgba(255,255,255,0.6)"), x=0), height=height)
    years = [k["year"] for k in kpis]
    for i, (key, label, color) in enumerate(metrics):
        vals = [k.get(key, 0) for k in kpis]
        fig.add_trace(go.Scatter(
            x=years, y=vals, name=label, mode="lines+markers",
            line=dict(color=color, width=2.5),
            marker=dict(size=5, color=color),
            fill="tozeroy" if i == 0 else "tonexty",
            fillcolor=color.replace(")", ", 0.08)").replace("rgb(", "rgba(") if "rgb" in color else f"{color}14",
        ))
    return fig

def bar_chart(kpis: list[dict], metrics: list[tuple], title: str = "", height: int = 280) -> go.Figure:
    """Grouped bar chart."""
    fig = _base_fig(title=dict(text=title, font=dict(size=13, color="rgba(255,255,255,0.6)"), x=0), height=height, barmode="group")
    years = [k["year"] for k in kpis]
    for key, label, color in metrics:
        vals = [k.get(key, 0) for k in kpis]
        fig.add_trace(go.Bar(
            x=years, y=vals, name=label,
            marker=dict(color=color, opacity=0.85, line=dict(width=0)),
        ))
    fig.update_traces(marker_cornerradius=4)
    return fig

def line_chart(kpis: list[dict], metrics: list[tuple], title: str = "", height: int = 280,
               pct: bool = False, reference_lines: list = None) -> go.Figure:
    """Multi-line chart with optional reference lines."""
    fig = _base_fig(title=dict(text=title, font=dict(size=13, color="rgba(255,255,255,0.6)"), x=0), height=height)
    years = [k["year"] for k in kpis]
    for key, label, color in metrics:
        vals = [((k.get(key) or 0) * 100 if pct else (k.get(key) or 0)) for k in kpis]
        fig.add_trace(go.Scatter(
            x=years, y=vals, name=label, mode="lines+markers",
            line=dict(color=color, width=2.5),
            marker=dict(size=5, color=color),
        ))
    if reference_lines:
        for y_val, label, color in reference_lines:
            fig.add_hline(y=y_val, line=dict(color=color, width=1, dash="dot"),
                         annotation=dict(text=label, font=dict(size=10, color=color), x=1))
    if pct:
        fig.update_yaxes(ticksuffix="%")
    return fig

# ─── PEER COMPARISON ─────────────────────────────────────────────────────────
def peer_bar(companies: list[str], values: list[float], title: str,
             highlight: str = None, color: str = None, height: int = 200,
             suffix: str = "", threshold: float = None) -> go.Figure:
    """Horizontal ranked bar chart for peer comparison."""
    sorted_pairs = sorted(zip(values, companies), reverse=True)
    vals_s, comps_s = zip(*sorted_pairs) if sorted_pairs else ([], [])

    colors = []
    for c in comps_s:
        if c == highlight:
            colors.append(COLORS["primary"])
        else:
            colors.append("rgba(99,102,241,0.5)")

    fig = _base_fig(title=dict(text=title, font=dict(size=12, color="rgba(255,255,255,0.5)"), x=0), height=height)
    fig.add_trace(go.Bar(
        y=list(comps_s), x=list(vals_s), orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{v:.1f}{suffix}" for v in vals_s],
        textposition="outside",
        textfont=dict(size=10, color="rgba(255,255,255,0.7)"),
    ))
    if threshold is not None:
        fig.add_vline(x=threshold, line=dict(color=COLORS["danger"], dash="dot", width=1.5),
                     annotation=dict(text=f"Threshold {threshold}", font=dict(size=9, color=COLORS["danger"])))
    fig.update_traces(marker_cornerradius=3)
    return fig

# ─── RADAR CHART ─────────────────────────────────────────────────────────────
def radar_chart(categories: list[str], company_vals: list[float], industry_vals: list[float],
                company_name: str, height: int = 320) -> go.Figure:
    cats = categories + [categories[0]]
    comp = company_vals + [company_vals[0]]
    ind  = industry_vals + [industry_vals[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=comp, theta=cats, fill="toself", name=company_name,
        line=dict(color=COLORS["primary"], width=2.5),
        fillcolor="rgba(0,212,170,0.12)"))
    fig.add_trace(go.Scatterpolar(r=ind, theta=cats, fill="toself", name="Industry Avg",
        line=dict(color=COLORS["secondary"], width=1.5, dash="dot"),
        fillcolor="rgba(99,102,241,0.06)"))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9, color=COLORS["muted"]),
                           gridcolor=COLORS["grid"]),
            angularaxis=dict(tickfont=dict(size=10, color=COLORS["muted"]), gridcolor=COLORS["grid"]),
        ),
        paper_bgcolor=COLORS["paper"], plot_bgcolor=COLORS["bg"],
        font=dict(family="DM Sans, sans-serif", color="white"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10, color="rgba(255,255,255,0.6)")),
        height=height, margin=dict(l=30, r=30, t=30, b=30),
    )
    return fig

# ─── GAUGE / SCORE ────────────────────────────────────────────────────────────
def gauge_chart(score: float, title: str, height: int = 180) -> go.Figure:
    if score >= 80:   color = COLORS["primary"]
    elif score >= 65: color = COLORS["success"]
    elif score >= 50: color = COLORS["warning"]
    elif score >= 35: color = "#f97316"
    else:             color = COLORS["danger"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(font=dict(size=28, color="white", family="DM Mono, monospace")),
        title=dict(text=title, font=dict(size=11, color="rgba(255,255,255,0.5)")),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=0, tickcolor="rgba(0,0,0,0)"),
            bar=dict(color=color, thickness=0.75),
            bgcolor="rgba(255,255,255,0.04)",
            borderwidth=0,
            steps=[
                dict(range=[0, 35],  color="rgba(239,68,68,0.05)"),
                dict(range=[35, 65], color="rgba(250,204,21,0.05)"),
                dict(range=[65, 100],color="rgba(0,212,170,0.05)"),
            ],
            threshold=dict(line=dict(color=color, width=3), thickness=0.85, value=score),
        )
    ))
    fig.update_layout(paper_bgcolor=COLORS["paper"], height=height,
                     font=dict(family="DM Sans, sans-serif", color="white"),
                     margin=dict(l=15, r=15, t=40, b=10))
    return fig

# ─── WATERFALL ────────────────────────────────────────────────────────────────
def waterfall(categories: list[str], values: list[float], title: str = "", height: int = 280) -> go.Figure:
    measures = ["relative"] * len(values)
    measures[0] = "absolute"
    fig = go.Figure(go.Waterfall(
        x=categories, y=values, measure=measures,
        increasing=dict(marker=dict(color=COLORS["primary"])),
        decreasing=dict(marker=dict(color=COLORS["danger"])),
        totals=dict(marker=dict(color=COLORS["secondary"])),
        connector=dict(line=dict(color=COLORS["grid"], dash="dot")),
        textposition="outside",
        text=[f"{v:+.1f}" for v in values],
        textfont=dict(size=10, color="rgba(255,255,255,0.7)"),
    ))
    fig.update_layout(**{**BASE_LAYOUT,
        "title": dict(text=title, font=dict(size=13, color="rgba(255,255,255,0.6)"), x=0),
        "height": height,
    })
    return fig

# ─── HEATMAP COMPARISON ───────────────────────────────────────────────────────
def comparison_heatmap(df: pd.DataFrame, title: str = "", height: int = 280) -> go.Figure:
    """Color-coded comparison heatmap."""
    # Normalize each row to 0-1
    df_norm = df.copy()
    for col in df.select_dtypes(include=[np.number]).columns:
        mn, mx = df[col].min(), df[col].max()
        if mx != mn:
            df_norm[col] = (df[col] - mn) / (mx - mn)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    text_vals = df[numeric_cols].round(2).astype(str).values

    fig = go.Figure(go.Heatmap(
        z=df_norm[numeric_cols].values,
        x=numeric_cols,
        y=df.index if df.index.name else df.iloc[:, 0].tolist(),
        text=text_vals, texttemplate="%{text}",
        colorscale=[[0, "rgba(239,68,68,0.4)"], [0.5, "rgba(250,204,21,0.4)"], [1, "rgba(0,212,170,0.5)"]],
        showscale=False,
        textfont=dict(size=11, color="white"),
    ))
    fig.update_layout(**{**BASE_LAYOUT, "height": height,
        "title": dict(text=title, font=dict(size=13, color="rgba(255,255,255,0.6)"), x=0)})
    return fig

# ─── VALUATION BAND ───────────────────────────────────────────────────────────
def valuation_band(kpis: list[dict], market_data: dict, metric: str = "ev_ebitda",
                   title: str = "EV/EBITDA Historical Band", height: int = 250) -> go.Figure:
    """Historical valuation band chart."""
    years = [k["year"] for k in kpis]
    current_val = market_data.get(metric, 0) or 0
    # Simulate historical valuation band (for real use, store historical multiples)
    vals = [current_val * np.random.uniform(0.8, 1.2) for _ in years]
    avg  = np.mean(vals)
    std  = np.std(vals)

    fig = _base_fig(title=dict(text=title, font=dict(size=13, color="rgba(255,255,255,0.6)"), x=0), height=height)
    fig.add_trace(go.Scatter(x=years+years[::-1],
        y=[avg+std]*len(years)+[avg-std]*len(years),
        fill="toself", fillcolor="rgba(99,102,241,0.1)",
        line=dict(color="rgba(0,0,0,0)"), name="+/- 1 Std Dev"))
    fig.add_trace(go.Scatter(x=years, y=vals, name=f"{metric.upper().replace('_','/')}",
        line=dict(color=COLORS["primary"], width=2.5),
        marker=dict(size=5, color=COLORS["primary"])))
    fig.add_hline(y=avg, line=dict(color=COLORS["warning"], dash="dash", width=1.5),
                 annotation=dict(text=f"5Y Avg {avg:.1f}x", font=dict(size=10, color=COLORS["warning"])))
    fig.add_hline(y=current_val, line=dict(color=COLORS["success"], dash="dot", width=2),
                 annotation=dict(text=f"Current {current_val:.1f}x", font=dict(size=10, color=COLORS["success"])))
    return fig

# ─── DUPONT WATERFALL ─────────────────────────────────────────────────────────
def dupont_breakdown(kpi: dict, title: str = "DuPont ROE Decomposition") -> go.Figure:
    net_margin   = (kpi.get("net_margin", 0) or 0) * 100
    asset_turn   = kpi.get("asset_turnover", 0) or 0
    fin_leverage = 1 / max(kpi.get("roa", 0.01), 0.001) * max(kpi.get("roe", 0.01), 0.001) / 100
    roe          = (kpi.get("roe", 0) or 0) * 100

    fig = go.Figure()
    items = [
        ("Net Margin", net_margin, COLORS["primary"]),
        ("× Asset Turnover", asset_turn * 10, COLORS["secondary"]),
        ("× Financial Leverage", fin_leverage * 10, COLORS["warning"]),
        ("= ROE", roe, COLORS["success"]),
    ]
    for label, val, color in items:
        fig.add_trace(go.Bar(
            x=[label], y=[val], name=label,
            marker=dict(color=color, opacity=0.85),
            text=[f"{val:.1f}"], textposition="outside",
            textfont=dict(size=11, color="white"),
        ))
    fig.update_layout(**{**BASE_LAYOUT, "height": 220, "showlegend": False, "barmode": "group",
        "title": dict(text=title, font=dict(size=13, color="rgba(255,255,255,0.6)"), x=0)})
    fig.update_traces(marker_cornerradius=4)
    return fig
