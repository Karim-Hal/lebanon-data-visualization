import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from plotly.subplots import make_subplots

from src.config import COLORS
from src.data_loader import load_basket_prices, load_health
from src.metrics import basket_price_index

st.set_page_config(page_title="Health Toll · Lebanon Crisis", page_icon="🏥", layout="wide")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
health  = load_health()
basket  = load_basket_prices()

# Filter to both-sexes / total rows only to avoid double-counting
health_btsx = health[
    health["DIMENSION (CODE)"].isin(["SEX_BTSX", "HOUSEHOLDWEALTH_TOTL"])
].copy()

# Indicators available for the slicer (with decent data coverage)
PRIORITY_CODES = [
    "NUTSTUNTINGPREV",
    "NUTSTUNTINGNUM",
    "NUTRITION_ANAEMIA_CHILDREN_PREV",
    "MDG_0000000007",
    "MDG_0000000001",
    "WHOSIS_000003",
    "NUTRITION_WH_2",
    "NUTRITION_WA_2",
    "MORTADO",
    "WHOSIS_000004",
]

slicer_df = (
    health_btsx[health_btsx["GHO (CODE)"].isin(PRIORITY_CODES)]
    [["GHO (CODE)", "GHO (DISPLAY)"]]
    .drop_duplicates()
    .sort_values("GHO (CODE)")
)
# Shorten labels for the selectbox
def short_label(s):
    return s[:80] + "…" if len(s) > 80 else s

slicer_df["label"] = slicer_df["GHO (DISPLAY)"].apply(short_label)
label_to_code = dict(zip(slicer_df["label"], slicer_df["GHO (CODE)"]))

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.markdown(
    f"<h1 style='color:{COLORS['deep_navy']}'>Act 3 — The Health Toll</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#555;font-size:15px'>"
    "Stunting, wasting, anaemia, and mortality in Lebanon — with a lagged view against food price shocks."
    "</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ---------------------------------------------------------------------------
# Chart 1: Dual-panel lag timeline
# Top: basket price index   Bottom: stunting prevalence
# ---------------------------------------------------------------------------
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>Food Prices vs Stunting Prevalence — Lag View</h3>",
    unsafe_allow_html=True,
)
st.caption(
    "Top: Monthly basket price index (2019=100). "
    "Bottom: Annual stunting prevalence % (model-based estimates). "
    "Shaded band highlights the 2020–2022 crisis window."
)

basket_idx = basket_price_index(basket)
basket_idx["year"] = basket_idx["year_month"].str[:4].astype(int)
basket_annual = basket_idx.groupby("year", as_index=False)["price_index"].mean()

stunt = (
    health_btsx[health_btsx["GHO (CODE)"] == "NUTSTUNTINGPREV"]
    [["YEAR (DISPLAY)", "Numeric"]]
    .dropna()
    .sort_values("YEAR (DISPLAY)")
)

# Align year range
yr_min = max(basket_annual["year"].min(), int(stunt["YEAR (DISPLAY)"].min()))
yr_max = min(basket_annual["year"].max(), int(stunt["YEAR (DISPLAY)"].max()))
basket_annual = basket_annual[(basket_annual["year"] >= yr_min) & (basket_annual["year"] <= yr_max)]
stunt = stunt[(stunt["YEAR (DISPLAY)"] >= yr_min) & (stunt["YEAR (DISPLAY)"] <= yr_max)]

fig_lag = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.08,
    subplot_titles=("Basket Price Index (2019=100)", "Stunting Prevalence (%)"),
)

fig_lag.add_trace(
    go.Scatter(
        x=basket_annual["year"],
        y=basket_annual["price_index"],
        name="Price Index",
        line=dict(color=COLORS["crisis_red"], width=2.5),
        fill="tozeroy",
        fillcolor="rgba(192,0,0,0.08)",
        hovertemplate="<b>%{x}</b><br>Price Index: %{y:.0f}<extra></extra>",
    ),
    row=1, col=1,
)

fig_lag.add_trace(
    go.Scatter(
        x=stunt["YEAR (DISPLAY)"],
        y=stunt["Numeric"],
        name="Stunting %",
        line=dict(color=COLORS["deep_navy"], width=2.5),
        mode="lines+markers",
        marker=dict(size=6),
        hovertemplate="<b>%{x}</b><br>Stunting: %{y:.1f}%<extra></extra>",
    ),
    row=2, col=1,
)

# Shaded rectangle: 2020–2022 crisis window
for row in [1, 2]:
    fig_lag.add_vrect(
        x0=2020, x1=2022,
        fillcolor=COLORS["warning"],
        opacity=0.08,
        line_width=0,
        row=row, col=1,
    )
    fig_lag.add_vline(
        x=2020, line_dash="dash", line_color=COLORS["warning"],
        line_width=1, opacity=0.6, row=row, col=1,
    )
    fig_lag.add_vline(
        x=2022, line_dash="dash", line_color=COLORS["warning"],
        line_width=1, opacity=0.6, row=row, col=1,
    )

fig_lag.add_annotation(
    x=2021, y=1, xref="x", yref="paper",
    text="Crisis window<br>2020–2022",
    showarrow=False,
    font=dict(size=10, color=COLORS["warning"]),
    bgcolor="rgba(255,255,255,0.8)",
)

fig_lag.update_yaxes(title_text="Price Index", row=1, col=1, gridcolor="#E5E5E5")
fig_lag.update_yaxes(title_text="Stunting (%)", row=2, col=1, ticksuffix="%", gridcolor="#E5E5E5")
fig_lag.update_xaxes(title_text="Year", row=2, col=1, dtick=2)
fig_lag.update_layout(
    height=520,
    margin=dict(l=60, r=20, t=40, b=40),
    showlegend=False,
    hovermode="x unified",
)

st.plotly_chart(fig_lag, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Chart 2: Nutrition small multiples (indicator slicer)
# ---------------------------------------------------------------------------
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>Health Indicator Explorer</h3>",
    unsafe_allow_html=True,
)

selected_label = st.selectbox(
    "Select indicator",
    options=list(label_to_code.keys()),
    index=0,
)
selected_code = label_to_code[selected_label]

indicator_df = (
    health_btsx[health_btsx["GHO (CODE)"] == selected_code]
    [["YEAR (DISPLAY)", "Numeric"]]
    .dropna()
    .sort_values("YEAR (DISPLAY)")
)

if indicator_df.empty:
    st.warning("No data available for this indicator.")
else:
    full_label = slicer_df.loc[slicer_df["GHO (CODE)"] == selected_code, "GHO (DISPLAY)"].iloc[0]

    fig_ind = go.Figure()
    fig_ind.add_trace(go.Scatter(
        x=indicator_df["YEAR (DISPLAY)"],
        y=indicator_df["Numeric"],
        mode="lines+markers",
        line=dict(color=COLORS["steel_blue"], width=2.5),
        marker=dict(size=7, color=COLORS["steel_blue"]),
        fill="tozeroy",
        fillcolor="rgba(46,116,181,0.08)",
        hovertemplate="<b>%{x}</b><br>Value: %{y:.2f}<extra></extra>",
    ))

    # Crisis vlines if chart spans 2019-2021
    year_min = int(indicator_df["YEAR (DISPLAY)"].min())
    year_max = int(indicator_df["YEAR (DISPLAY)"].max())
    if year_min <= 2021 and year_max >= 2019:
        crisis_years = {"2019": "Banking crisis", "2020": "Port explosion", "2021": "Subsidy removal"}
        for yr_str, label in crisis_years.items():
            yr = int(yr_str)
            if year_min <= yr <= year_max:
                fig_ind.add_vline(
                    x=yr, line_dash="dash",
                    line_color=COLORS["warning"], line_width=1.5,
                    annotation_text=label,
                    annotation_position="top right",
                    annotation_font_size=10,
                    annotation_font_color=COLORS["warning"],
                )

    fig_ind.update_layout(
        height=380,
        margin=dict(l=60, r=20, t=20, b=40),
        xaxis=dict(title="Year", dtick=2, showgrid=False),
        yaxis=dict(title="Value", gridcolor="#E5E5E5"),
        hovermode="x unified",
    )
    st.plotly_chart(fig_ind, use_container_width=True)
    st.caption(f"Indicator: {full_label}  ·  Lebanon (LBN)  ·  Source: WHO GHO")

st.markdown("---")

# ---------------------------------------------------------------------------
# Chart 3: Nutrition small multiples — 4 key indicators side by side
# ---------------------------------------------------------------------------
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>Key Nutrition & Mortality Trends</h3>",
    unsafe_allow_html=True,
)
st.caption("Model-based / both-sexes estimates. All Lebanon (LBN).")

MULTI_CODES = {
    "Stunting prevalence (%)":         "NUTSTUNTINGPREV",
    "Anaemia in children (%)":         "NUTRITION_ANAEMIA_CHILDREN_PREV",
    "Infant mortality (per 1,000)":    "MDG_0000000001",
    "Under-5 mortality (per 1,000)":   "MDG_0000000007",
}
MULTI_COLORS = [COLORS["crisis_red"], COLORS["warning"], COLORS["steel_blue"], COLORS["teal"]]

fig_multi = make_subplots(
    rows=2, cols=2,
    subplot_titles=list(MULTI_CODES.keys()),
    vertical_spacing=0.14,
    horizontal_spacing=0.10,
)

positions = [(1,1),(1,2),(2,1),(2,2)]
for (title, code), (row, col), color in zip(MULTI_CODES.items(), positions, MULTI_COLORS):
    df_m = (
        health_btsx[health_btsx["GHO (CODE)"] == code]
        [["YEAR (DISPLAY)", "Numeric"]]
        .dropna()
        .sort_values("YEAR (DISPLAY)")
    )
    if df_m.empty:
        continue
    fig_multi.add_trace(
        go.Scatter(
            x=df_m["YEAR (DISPLAY)"],
            y=df_m["Numeric"],
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=4),
            showlegend=False,
            hovertemplate="<b>%{x}</b><br>%{y:.2f}<extra></extra>",
        ),
        row=row, col=col,
    )
    # Crisis shading where data spans the period
    yr_min_m = int(df_m["YEAR (DISPLAY)"].min())
    yr_max_m = int(df_m["YEAR (DISPLAY)"].max())
    if yr_min_m <= 2020 <= yr_max_m:
        fig_multi.add_vrect(
            x0=2020, x1=min(2022, yr_max_m),
            fillcolor=COLORS["warning"], opacity=0.07,
            line_width=0, row=row, col=col,
        )

fig_multi.update_xaxes(dtick=5, showgrid=False)
fig_multi.update_yaxes(gridcolor="#E5E5E5")
fig_multi.update_layout(
    height=520,
    margin=dict(l=40, r=20, t=50, b=40),
)

st.plotly_chart(fig_multi, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# MENA regional scatter — known limitation
# ---------------------------------------------------------------------------
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>Regional Under-5 Mortality Comparison</h3>",
    unsafe_allow_html=True,
)
st.warning(
    "**Known data limitation:** The WHO GHO health file (`health_filtered.csv`) contains Lebanon data only. "
    "Regional under-5 mortality (`SH.DYN.MORT`) is not present in the World Bank WDI export either. "
    "A MENA peer comparison cannot be produced without an additional data pull from WHO GHO or UNICEF. "
    "No data has been fabricated.",
    icon="⚠️",
)
st.markdown(
    "<p style='font-size:13px;color:#888'>"
    "To add this chart: download the WHO GHO <code>MDG_0000000007</code> indicator for EMRO countries "
    "and place it in <code>data/who_u5mort_mena.csv</code>."
    "</p>",
    unsafe_allow_html=True,
)
