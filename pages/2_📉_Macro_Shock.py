import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.config import COLORS, COUNTRY_COLORS, EVENTS, SERIES
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
# Helper: add event vlines to a go.Figure
# ---------------------------------------------------------------------------
def add_event_vlines(fig, row=None, col=None):
    kwargs = {}
    if row is not None:
        kwargs["row"] = row
    if col is not None:
        kwargs["col"] = col
    for date_str, label, color_key, dash in EVENTS:
        fig.add_vline(
            x=pd.Timestamp(date_str).timestamp() * 1000,
            line_dash=dash,
            line_color=COLORS[color_key],
            line_width=1.5,
            annotation_text=label,
            annotation_position="top right",
            annotation_font_size=10,
            annotation_font_color=COLORS[color_key],
            **kwargs,
        )

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.markdown(
    f"<h1 style='color:{COLORS['deep_navy']}'>Act 1 — The Macro Shock</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#555;font-size:15px'>GDP collapse, currency devaluation, and inflation compared across Lebanon and five regional peers.</p>",
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
        line=dict(color=COLORS["crisis_red"], width=2.5),
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
        line=dict(color=COLORS["steel_blue"], width=2.5, dash="dot"),
        mode="lines+markers",
        marker=dict(size=5),
        hovertemplate="<b>%{x}</b><br>Rate: %{y:,.0f} LBP/USD<extra></extra>",
    ),
    secondary_y=True,
)

# Event vlines — expressed as year floats since X axis is integer Year
for date_str, label, color_key, dash in EVENTS:
    yr = pd.Timestamp(date_str).year + (pd.Timestamp(date_str).month - 1) / 12
    fig_dual.add_vline(
        x=yr,
        line_dash=dash,
        line_color=COLORS[color_key],
        line_width=1.5,
        annotation_text=label,
        annotation_position="top left",
        annotation_font_size=10,
        annotation_font_color=COLORS[color_key],
    )

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
    height=420,
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
st.caption("Consumer price inflation (% annual). Lebanon's 2020–2023 surge dwarfs all regional peers.")

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

# Remove facet label prefix "Country Name="
fig_inf.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))

# Bold Lebanon facet title
fig_inf.for_each_annotation(
    lambda a: a.update(font=dict(color=COLORS["crisis_red"], size=12, family="Segoe UI"))
    if a.text == "Lebanon"
    else a.update(font=dict(color=COLORS["deep_navy"], size=11, family="Segoe UI"))
)

# Add event vlines on each facet
for date_str, label, color_key, dash in EVENTS:
    yr = pd.Timestamp(date_str).year + (pd.Timestamp(date_str).month - 1) / 12
    fig_inf.add_vline(
        x=yr,
        line_dash=dash,
        line_color=COLORS[color_key],
        line_width=1,
        opacity=0.6,
    )

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

# Show only years 2011–2024; format as currency strings
display_years = [y for y in range(2011, 2025) if y in gdp_pc_all.columns]
table_df = gdp_pc_all[display_years].copy()

# Style: highlight Lebanon row
def highlight_lebanon(row):
    if row.name == "Lebanon":
        return [f"background-color:{COLORS['card_bg']};font-weight:bold;color:{COLORS['crisis_red']}"] * len(row)
    return [""] * len(row)

styled = (
    table_df.style
    .apply(highlight_lebanon, axis=1)
    .format("${:,.0f}", na_rep="—")
)

st.dataframe(styled, use_container_width=True)
