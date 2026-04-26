import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.config import COLORS, EVENTS, PALETTE
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
            border-left: 5px solid;
            border-radius: 6px;
            padding: 20px 24px;
            height: 130px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            background: {COLORS['card_bg']};
        }}
        .kpi-label {{
            font-size: 12px;
            font-weight: 700;
            color: {COLORS['deep_navy']};
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }}
        .kpi-value {{
            font-size: 38px;
            font-weight: 800;
            line-height: 1;
        }}
        .kpi-sub {{
            font-size: 11px;
            color: #888;
            margin-top: 4px;
        }}
        .section-label {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #999;
            margin-bottom: 12px;
        }}
        .act-card {{
            border-left: 4px solid;
            border-radius: 6px;
            padding: 14px 16px;
            margin-bottom: 10px;
            background: {COLORS['card_bg']};
        }}
        .act-title {{
            font-size: 14px;
            font-weight: 700;
            color: {COLORS['deep_navy']};
            margin-bottom: 4px;
        }}
        .act-desc {{
            font-size: 12px;
            color: #555;
            line-height: 1.55;
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
    f"<p style='color:#666;font-size:15px;margin-top:0'>A decade of economic collapse, food insecurity, and deteriorating health outcomes &nbsp;·&nbsp; 2012–2026</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ---------------------------------------------------------------------------
# KPI cards — four crisis indicators
# ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-left-color:{PALETTE[0]}">
            <div class="kpi-label">Peak Annual Inflation</div>
            <div>
                <div class="kpi-value" style="color:{PALETTE[0]}">{peak_inflation:.1f}%</div>
                <div class="kpi-sub">Lebanon consumer prices, peak year</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-left-color:{PALETTE[0]}">
            <div class="kpi-label">GDP Contraction 2018 → 2023</div>
            <div>
                <div class="kpi-value" style="color:{PALETTE[0]}">{gdp_drop:.0%}</div>
                <div class="kpi-sub">Share of GDP lost in five years</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-left-color:{PALETTE[1]}">
            <div class="kpi-label">Lebanese in IPC Phase 3+</div>
            <div>
                <div class="kpi-value" style="color:{PALETTE[1]}">{phase3_pct:.0%}</div>
                <div class="kpi-sub">Lebanese residents · {latest_ipc_date} snapshot</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        f"""
        <div class="kpi-card" style="border-left-color:{PALETTE[3]}">
            <div class="kpi-label">LBP per USD (Unofficial)</div>
            <div>
                <div class="kpi-value" style="color:{PALETTE[3]}">{lbp_rate:,.0f}</div>
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
st.markdown('<div class="section-label">Crisis Timeline</div>', unsafe_allow_html=True)

event_colors = {
    "warning":    PALETTE[1],
    "crisis_red": PALETTE[0],
}

event_dates  = [pd.Timestamp(e[0]) for e in EVENTS]
event_labels = [e[1] for e in EVENTS]
event_clrs   = [event_colors[e[2]] for e in EVENTS]

fig_timeline = go.Figure()

fig_timeline.add_shape(
    type="line",
    x0=pd.Timestamp("2019-01-01"), x1=pd.Timestamp("2022-01-01"),
    y0=0, y1=0,
    line=dict(color=COLORS["deep_navy"], width=2),
)

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

st.markdown("---")

# ---------------------------------------------------------------------------
# About + story navigation
# ---------------------------------------------------------------------------
col_about, col_gap, col_acts = st.columns([3, 0.3, 2.5])

with col_about:
    st.markdown(
        f"""
        <div class="section-label">About this dashboard</div>
        <p style="font-size:14px;line-height:1.8;color:#333;margin-top:0">
        Lebanon experienced one of the world's most severe economic collapses of the modern era.
        A banking-sector crisis in <b style="color:{PALETTE[1]}">October 2019</b>,
        compounded by the <b style="color:{PALETTE[0]}">Beirut port explosion</b> in August 2020
        and the removal of fuel and food subsidies in 2021, triggered a cascading humanitarian emergency.
        The Lebanese pound lost over <b>98%</b> of its value against the US dollar,
        while consumer prices rose more than <b>200%</b> in a single year.
        </p>
        <p style="font-size:14px;line-height:1.8;color:#333">
        The ripple effects — surging food prices, widespread food insecurity, child malnutrition,
        and deteriorating health outcomes — are the subject of this five-act narrative.
        </p>
        <p style="font-size:12px;color:#aaa;margin-top:16px">
            <b style="color:#888">Data sources</b>&nbsp;·&nbsp;
            WFP VAM Food Prices &nbsp;·&nbsp; World Bank WDI &nbsp;·&nbsp;
            IPC Global Platform &nbsp;·&nbsp; WHO Global Health Observatory
        </p>
        """,
        unsafe_allow_html=True,
    )

with col_acts:
    st.markdown('<div class="section-label">Navigate the story</div>', unsafe_allow_html=True)

    acts = [
        (
            "📉", "Act 1 — The Macro Shock", PALETTE[0],
            "How Lebanon's economy unravelled: GDP fell by over 60%, inflation peaked above 200%, "
            "and the official exchange rate diverged sharply from the black market. Compare Lebanon's "
            "trajectory against five regional peers — Jordan, Egypt, Syria, Saudi Arabia, and the UAE.",
        ),
        (
            "🛒", "Act 2 — Food Price Transmission", PALETTE[1],
            "How the macro shock passed directly into household food costs. Track six staple commodities "
            "on a 2019=100 index, watch LBP and USD prices diverge, and see how closely the unofficial "
            "exchange rate predicts basket prices.",
        ),
        (
            "🗺️", "Act 2 Ext. — Who Suffers Most", PALETTE[2],
            "IPC food insecurity phases broken down by governorate and by population group. "
            "Which regions are deepest in crisis? How do Lebanese residents, Syrian refugees, "
            "and Palestinian refugees differ in exposure?",
        ),
        (
            "🏥", "Act 3 — The Health Toll", PALETTE[4],
            "The delayed human cost: stunting, wasting, anaemia, and infant mortality plotted "
            "against food price trends with a lagged overlay. Nutrition indicators worsen "
            "years after the price shock — the crisis is still unfolding.",
        ),
    ]

    for icon, title, color, desc in acts:
        st.markdown(
            f"""
            <div class="act-card" style="border-left-color:{color}">
                <div class="act-title">{icon} {title}</div>
                <div class="act-desc">{desc}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
