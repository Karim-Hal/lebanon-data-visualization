import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.config import COLORS, COUNTRY_COLORS, EVENTS, PALETTE, SERIES
from src.data_loader import load_wdi

st.set_page_config(page_title="Macro Shock · Lebanon Crisis", page_icon="📉", layout="wide")

# ---------------------------------------------------------------------------
# Load & slice data
# ---------------------------------------------------------------------------
wdi = load_wdi()

lbn_gdp = wdi[(wdi["Country Name"] == "Lebanon") & (wdi["Series Code"] == SERIES["gdp"])].copy()
lbn_gdp["gdp_bn"] = lbn_gdp["Value"] / 1e9

lbn_fx = wdi[(wdi["Country Name"] == "Lebanon") & (wdi["Series Code"] == SERIES["official_fx"])].copy()

inflation_all = wdi[wdi["Series Code"] == SERIES["inflation"]].copy()

gdp_pc_all = (
    wdi[wdi["Series Code"] == SERIES["gdp_pc"]]
    .pivot_table(index="Country Name", columns="Year", values="Value")
    .round(0)
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def event_color(key):
    return PALETTE[0] if key == "crisis_red" else PALETTE[1]


# Stagger event annotations vertically so they don't overlap.
# Each tuple: (y in paper coords, x-shift px, horizontal anchor)
EVENT_LAYOUT = [
    (0.93, 6, "left"),   # Banking crisis — top
    (0.72, 6, "left"),   # Port explosion — mid
    (0.51, 6, "left"),   # Subsidy removal — lower
]


def add_event_vlines(fig, row=None, col=None):
    """Add event vlines without annotations (used for small-multiple facets)."""
    kw = {}
    if row is not None:
        kw["row"] = row
    if col is not None:
        kw["col"] = col
    for date_str, _, color_key, dash in EVENTS:
        yr = pd.Timestamp(date_str).year + (pd.Timestamp(date_str).month - 1) / 12
        fig.add_vline(
            x=yr,
            line_dash=dash,
            line_color=event_color(color_key),
            line_width=1,
            opacity=0.55,
            **kw,
        )


def add_event_vlines_annotated(fig):
    """Add event vlines with staggered non-overlapping labels to a single-panel figure."""
    for (date_str, label, color_key, dash), (y_pos, xshift, anchor) in zip(EVENTS, EVENT_LAYOUT):
        yr = pd.Timestamp(date_str).year + (pd.Timestamp(date_str).month - 1) / 12
        col = event_color(color_key)
        fig.add_vline(x=yr, line_dash=dash, line_color=col, line_width=1.5)
        fig.add_annotation(
            x=yr, y=y_pos,
            xref="x", yref="paper",
            text=f"<b>{label}</b>",
            showarrow=False,
            font=dict(size=9, color=col),
            bgcolor="white",
            bordercolor=col,
            borderwidth=1,
            borderpad=4,
            xanchor=anchor,
            xshift=xshift,
        )


# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.markdown(
    f"<h1 style='color:{COLORS['deep_navy']}'>Act 1 — The Macro Shock</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#666;font-size:15px'>GDP collapse, currency devaluation, and inflation compared across Lebanon and five regional peers.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ---------------------------------------------------------------------------
# Chart 1: GDP + Official Exchange Rate (dual-axis, Lebanon only)
# ---------------------------------------------------------------------------
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>GDP & Official Exchange Rate — Lebanon</h3>",
    unsafe_allow_html=True,
)
st.caption("Left axis: GDP in USD billions · Right axis: Official LBP per USD (World Bank)")

fig_dual = make_subplots(specs=[[{"secondary_y": True}]])

fig_dual.add_trace(
    go.Scatter(
        x=lbn_gdp["Year"],
        y=lbn_gdp["gdp_bn"],
        name="GDP (USD bn)",
        line=dict(color=PALETTE[0], width=2.5),
        mode="lines+markers",
        marker=dict(size=5),
        hovertemplate="<b>%{x}</b><br>GDP: $%{y:.1f}B<extra></extra>",
    ),
    secondary_y=False,
)

fig_dual.add_trace(
    go.Scatter(
        x=lbn_fx["Year"],
        y=lbn_fx["Value"],
        name="Official LBP/USD",
        line=dict(color=PALETTE[3], width=2.5, dash="dot"),
        mode="lines+markers",
        marker=dict(size=5),
        hovertemplate="<b>%{x}</b><br>Rate: %{y:,.0f} LBP/USD<extra></extra>",
    ),
    secondary_y=True,
)

add_event_vlines_annotated(fig_dual)

fig_dual.update_yaxes(
    title_text="GDP (USD billions)",
    secondary_y=False,
    tickprefix="$",
    ticksuffix="B",
    gridcolor="#E5E5E5",
)
fig_dual.update_yaxes(
    title_text="Official LBP per USD",
    secondary_y=True,
    tickformat=",",
    showgrid=False,
)
fig_dual.update_xaxes(title_text="Year", dtick=1)
fig_dual.update_layout(
    height=440,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=60, r=60, t=40, b=40),
    hovermode="x unified",
)

st.plotly_chart(fig_dual, use_container_width=True)

st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Chart 2: Inflation small multiples — all 6 countries
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>Annual Inflation — Regional Comparison</h3>",
    unsafe_allow_html=True,
)
st.caption(
    "Consumer price inflation (% annual). Each panel uses an independent Y axis to show "
    "each country's own trend — Lebanon's scale peaks above 200%, while peers range from 2–35%."
)

fig_inf = px.line(
    inflation_all.sort_values(["Country Name", "Year"]),
    x="Year",
    y="Value",
    color="Country Name",
    facet_col="Country Name",
    facet_col_wrap=3,
    color_discrete_map=COUNTRY_COLORS,
    labels={"Value": "Inflation (%)", "Year": ""},
    markers=True,
)

fig_inf.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
fig_inf.for_each_annotation(
    lambda a: a.update(font=dict(color=PALETTE[0], size=12, family="Segoe UI"))
    if a.text == "Lebanon"
    else a.update(font=dict(color=COLORS["deep_navy"], size=11, family="Segoe UI"))
)

add_event_vlines(fig_inf)

fig_inf.update_yaxes(matches=None, showticklabels=True, ticksuffix="%", gridcolor="#E5E5E5")
fig_inf.update_xaxes(dtick=3, tickangle=-45)
fig_inf.update_traces(marker=dict(size=4), line=dict(width=2))
fig_inf.update_layout(
    height=500,
    showlegend=False,
    margin=dict(l=40, r=20, t=60, b=40),
)

st.plotly_chart(fig_inf, use_container_width=True)

st.info(
    "**Note:** Syria data ends at 2019 — the World Bank stopped reporting inflation figures after the conflict intensified.",
    icon="ℹ️",
)

st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Chart 3: GDP per capita table — country × year
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>GDP per Capita (USD) — Country × Year</h3>",
    unsafe_allow_html=True,
)
st.caption("Source: World Bank WDI · NY.GDP.PCAP.CD")

display_years = [y for y in range(2011, 2025) if y in gdp_pc_all.columns]
table_df = gdp_pc_all[display_years].copy()

def style_table(row):
    if row.name == "Lebanon":
        return [
            f"background-color:{PALETTE[0]}18;color:{PALETTE[0]};font-weight:700"
        ] * len(row)
    # Alternate rows for readability
    countries = list(table_df.index)
    idx = countries.index(row.name)
    bg = COLORS["card_bg"] if idx % 2 == 0 else "white"
    return [f"background-color:{bg};color:{COLORS['deep_navy']}"] * len(row)

styled = (
    table_df.style
    .apply(style_table, axis=1)
    .format("${:,.0f}", na_rep="—")
    .set_table_styles([
        {
            "selector": "th",
            "props": [
                ("background-color", COLORS["deep_navy"]),
                ("color", "white"),
                ("font-weight", "700"),
                ("font-size", "12px"),
                ("text-align", "center"),
            ],
        },
        {
            "selector": "th.row_heading",
            "props": [
                ("background-color", COLORS["card_bg"]),
                ("color", COLORS["deep_navy"]),
                ("font-weight", "600"),
            ],
        },
    ])
)

st.dataframe(styled, use_container_width=True)
