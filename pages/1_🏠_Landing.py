import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config import COLORS, EVENTS
from src.data_loader import load_exchange_rate, load_ipc_population_groups, load_wdi
from src.metrics import (
    gdp_contraction,
    latest_unofficial_rate,
    lebanon_peak_inflation,
    lebanese_phase3_plus,
)

st.set_page_config(page_title="Landing · Lebanon Crisis", page_icon="🏠", layout="wide")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
wdi     = load_wdi()
ipc_pop = load_ipc_population_groups()
exrate  = load_exchange_rate()

# ---------------------------------------------------------------------------
# Compute KPIs
# ---------------------------------------------------------------------------
peak_inflation  = lebanon_peak_inflation(wdi)
gdp_drop        = gdp_contraction(wdi, start=2018, end=2023)
phase3_pct      = lebanese_phase3_plus(ipc_pop)
lbp_rate        = latest_unofficial_rate(exrate)

latest_ipc_date = ipc_pop["analysis_date"].max().strftime("%b %Y")
latest_fx_date  = exrate.loc[exrate["date"].idxmax(), "date"].strftime("%b %Y")

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
        .kpi-card {{
            background: {COLORS['card_bg']};
            border-left: 5px solid {COLORS['deep_navy']};
            border-radius: 6px;
            padding: 20px 24px;
            height: 130px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .kpi-card.red {{ border-left-color: {COLORS['crisis_red']}; }}
        .kpi-card.orange {{ border-left-color: {COLORS['warning']}; }}
        .kpi-label {{
            font-size: 13px;
            font-weight: 600;
            color: {COLORS['deep_navy']};
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}
        .kpi-value {{
            font-size: 38px;
            font-weight: 700;
            line-height: 1;
        }}
        .kpi-sub {{
            font-size: 11px;
            color: #666;
            margin-top: 4px;
        }}
        .timeline-event {{
            background: {COLORS['card_bg']};
            border-radius: 6px;
            padding: 16px 18px;
            text-align: center;
            height: 100%;
        }}
        .timeline-dot {{
            width: 14px;
            height: 14px;
            border-radius: 50%;
            display: inline-block;
            margin-bottom: 8px;
        }}
        .section-header {{
            font-size: 13px;
            font-weight: 700;
            color: {COLORS['deep_navy']};
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 4px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.markdown(
    f"<h1 style='color:{COLORS['deep_navy']};margin-bottom:4px'>Lebanon in Crisis</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#555;font-size:15px;margin-top:0'>A decade of economic collapse, food insecurity, and deteriorating health outcomes (2012–2026)</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"""
        <div class="kpi-card red">
            <div class="kpi-label">Peak Annual Inflation</div>
            <div>
                <div class="kpi-value" style="color:{COLORS['crisis_red']}">{peak_inflation:.1f}%</div>
                <div class="kpi-sub">Lebanon consumer prices, peak year</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="kpi-card red">
            <div class="kpi-label">GDP Contraction 2018→2023</div>
            <div>
                <div class="kpi-value" style="color:{COLORS['crisis_red']}">{gdp_drop:.0%}</div>
                <div class="kpi-sub">Share of GDP lost in five years</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div class="kpi-card orange">
            <div class="kpi-label">Lebanese in IPC Phase 3+</div>
            <div>
                <div class="kpi-value" style="color:{COLORS['warning']}">{phase3_pct:.0%}</div>
                <div class="kpi-sub">Lebanese residents · {latest_ipc_date} snapshot</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">LBP per USD (Unofficial)</div>
            <div>
                <div class="kpi-value" style="color:{COLORS['deep_navy']}">{lbp_rate:,.0f}</div>
                <div class="kpi-sub">Unofficial parallel rate · {latest_fx_date}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-top:32px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Crisis timeline
# ---------------------------------------------------------------------------
st.markdown(
    f"<div class='section-header'>Crisis Timeline</div>",
    unsafe_allow_html=True,
)

event_colors = {
    "warning":    COLORS["warning"],
    "crisis_red": COLORS["crisis_red"],
}

# Build a horizontal Plotly timeline
event_dates  = [pd.Timestamp(e[0]) for e in EVENTS]
event_labels = [e[1] for e in EVENTS]
event_clrs   = [event_colors[e[2]] for e in EVENTS]

fig_timeline = go.Figure()

# Baseline axis line
fig_timeline.add_shape(
    type="line",
    x0=pd.Timestamp("2019-01-01"), x1=pd.Timestamp("2022-01-01"),
    y0=0, y1=0,
    line=dict(color=COLORS["deep_navy"], width=2),
)

# Event dots and annotations
for dt, label, color in zip(event_dates, event_labels, event_clrs):
    fig_timeline.add_trace(go.Scatter(
        x=[dt], y=[0],
        mode="markers",
        marker=dict(size=16, color=color, line=dict(width=2, color="white")),
        hovertemplate=f"<b>{label}</b><br>{dt.strftime('%B %Y')}<extra></extra>",
        showlegend=False,
    ))
    fig_timeline.add_annotation(
        x=dt, y=0,
        text=f"<b>{dt.strftime('%b %Y')}</b><br>{label}",
        showarrow=True,
        arrowhead=2,
        arrowcolor=color,
        arrowwidth=1.5,
        ax=0,
        ay=-55,
        font=dict(size=12, color=color),
        bgcolor="white",
        bordercolor=color,
        borderwidth=1.5,
        borderpad=6,
    )

fig_timeline.update_layout(
    height=180,
    margin=dict(l=20, r=20, t=10, b=10),
    xaxis=dict(
        showgrid=False, zeroline=False,
        range=[pd.Timestamp("2018-06-01"), pd.Timestamp("2022-06-01")],
        tickformat="%Y",
    ),
    yaxis=dict(visible=False, range=[-1, 1]),
    plot_bgcolor="white",
    paper_bgcolor="white",
)

st.plotly_chart(fig_timeline, use_container_width=True)

# ---------------------------------------------------------------------------
# Context paragraph
# ---------------------------------------------------------------------------
st.markdown("---")
col_l, col_r = st.columns([2, 1])

with col_l:
    st.markdown(
        f"""
        <h3 style="color:{COLORS['deep_navy']}">About this dashboard</h3>
        <p style="font-size:14px;line-height:1.7;color:#333">
        Lebanon experienced one of the world's most severe economic collapses of the modern era.
        A banking sector crisis in October 2019, compounded by the Beirut port explosion in August 2020
        and the removal of fuel and food subsidies in 2021, triggered a cascading humanitarian emergency.
        The Lebanese pound lost over 98% of its value against the US dollar, while consumer prices
        rose more than 200% in a single year. The ripple effects — food insecurity, child malnutrition,
        and deteriorating health outcomes — are the subject of this dashboard.
        </p>
        <p style="font-size:13px;color:#888">
        <b>Data sources:</b> WFP VAM Food Prices · World Bank WDI · IPC Global Platform · WHO GHO
        </p>
        """,
        unsafe_allow_html=True,
    )

with col_r:
    st.markdown(
        f"""
        <div style="background:{COLORS['card_bg']};border-radius:8px;padding:20px">
            <div style="font-size:12px;font-weight:700;color:{COLORS['deep_navy']};
                        text-transform:uppercase;letter-spacing:0.06em;margin-bottom:12px">
                Navigate the story
            </div>
            <div style="font-size:13px;line-height:2;color:#333">
                📉 <b>Act 1</b> — The Macro Shock<br>
                🛒 <b>Act 2</b> — Food Price Transmission<br>
                🗺️ <b>Act 2 ext.</b> — Who Suffers Most<br>
                🏥 <b>Act 3</b> — The Health Toll
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
