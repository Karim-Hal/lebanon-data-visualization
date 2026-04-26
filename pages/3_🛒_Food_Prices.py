import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.config import BASKET, COLORS, EVENTS
from src.data_loader import load_basket_prices, load_exchange_rate, load_wfp_prices
from src.metrics import (
    basket_price_index,
    monthly_basket_lbp,
    monthly_basket_usd,
    monthly_unofficial_rate,
    rate_vs_basket_r_squared,
)

st.set_page_config(page_title="Food Prices · Lebanon Crisis", page_icon="🛒", layout="wide")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
prices  = load_wfp_prices()
exrate  = load_exchange_rate()
basket  = load_basket_prices()

# ---------------------------------------------------------------------------
# Slicers
# ---------------------------------------------------------------------------
st.markdown(
    f"<h1 style='color:{COLORS['deep_navy']}'>Act 2 — Food Price Transmission</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#555;font-size:15px'>How Lebanon's currency collapse drove food prices beyond reach — tracked through WFP market data (2012–2026).</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

with st.expander("Filters", expanded=True):
    col_f1, col_f2 = st.columns([2, 3])

    with col_f1:
        all_commodities = sorted(prices["commodity"].unique().tolist())
        selected_commodities = st.multiselect(
            "Commodities (Chart 1)",
            options=all_commodities,
            default=BASKET,
            help="Controls which commodities appear in the price index chart.",
        )

    with col_f2:
        min_date = prices["date"].min().to_pydatetime()
        max_date = prices["date"].max().to_pydatetime()
        date_range = st.slider(
            "Date range (Charts 1 & 2)",
            min_value=min_date,
            max_value=max_date,
            value=(min_date, max_date),
            format="MMM YYYY",
        )

start_ts, end_ts = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])

# ---------------------------------------------------------------------------
# Helper: add event vlines
# ---------------------------------------------------------------------------
def add_vlines(fig):
    for date_str, label, color_key, dash in EVENTS:
        ts = pd.Timestamp(date_str)
        if start_ts <= ts <= end_ts:
            fig.add_vline(
                x=ts.timestamp() * 1000,
                line_dash=dash,
                line_color=COLORS[color_key],
                line_width=1.5,
                annotation_text=label,
                annotation_position="top right",
                annotation_font_size=10,
                annotation_font_color=COLORS[color_key],
            )

# ---------------------------------------------------------------------------
# Chart 1: Commodity price index (2019 = 100)
# ---------------------------------------------------------------------------
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>Commodity Price Index (2019 = 100)</h3>",
    unsafe_allow_html=True,
)
st.caption("Monthly average price index per commodity. Dotted line marks 2019 baseline.")

if selected_commodities:
    df_idx = (
        prices[
            prices["commodity"].isin(selected_commodities) &
            (prices["date"] >= start_ts) &
            (prices["date"] <= end_ts)
        ]
        .groupby(["date", "commodity"], as_index=False)["price_index"]
        .mean()
        .sort_values("date")
    )

    fig_idx = px.line(
        df_idx,
        x="date",
        y="price_index",
        color="commodity",
        labels={"price_index": "Price Index (2019=100)", "date": "", "commodity": "Commodity"},
        markers=False,
    )

    # Baseline at 100
    fig_idx.add_hline(
        y=100,
        line_dash="dot",
        line_color=COLORS["deep_navy"],
        line_width=1.5,
        annotation_text="2019 baseline",
        annotation_position="bottom right",
        annotation_font_size=10,
    )

    add_vlines(fig_idx)

    fig_idx.update_layout(
        height=420,
        margin=dict(l=40, r=20, t=20, b=40),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        yaxis=dict(gridcolor="#E5E5E5"),
    )
    fig_idx.update_xaxes(showgrid=False)

    st.plotly_chart(fig_idx, use_container_width=True)
else:
    st.warning("Select at least one commodity above.")

st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Chart 2: LBP vs USD basket price — dual Y axes
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>Basket Price — LBP vs USD</h3>",
    unsafe_allow_html=True,
)
st.caption(
    "Monthly average price of the six-item food basket. "
    "LBP price (left) exploded while USD price (right) also rose, showing real purchasing-power loss."
)

lbp_monthly = monthly_basket_lbp(basket)
usd_monthly = monthly_basket_usd(basket)

# Filter to selected date range
def filter_ym(df, col="year_month"):
    mask = (df[col] >= start_ts.strftime("%Y-%m")) & (df[col] <= end_ts.strftime("%Y-%m"))
    return df[mask]

lbp_f = filter_ym(lbp_monthly)
usd_f = filter_ym(usd_monthly)

fig_dual = make_subplots(specs=[[{"secondary_y": True}]])

fig_dual.add_trace(
    go.Scatter(
        x=lbp_f["year_month"],
        y=lbp_f["price"],
        name="LBP price",
        line=dict(color=COLORS["crisis_red"], width=2.5),
        hovertemplate="<b>%{x}</b><br>LBP: %{y:,.0f}<extra></extra>",
    ),
    secondary_y=False,
)

fig_dual.add_trace(
    go.Scatter(
        x=usd_f["year_month"],
        y=usd_f["usdprice"],
        name="USD price",
        line=dict(color=COLORS["steel_blue"], width=2.5, dash="dot"),
        hovertemplate="<b>%{x}</b><br>USD: $%{y:.2f}<extra></extra>",
    ),
    secondary_y=True,
)

# Event vlines: use add_shape + add_annotation separately because
# add_vline cannot compute annotation position on a string x-axis.
for date_str, label, color_key, dash in EVENTS:
    ts = pd.Timestamp(date_str)
    if start_ts <= ts <= end_ts:
        ym = ts.strftime("%Y-%m")
        dash_style = "dash" if dash == "dash" else "solid"
        fig_dual.add_shape(
            type="line",
            x0=ym, x1=ym,
            y0=0, y1=1,
            xref="x", yref="paper",
            line=dict(color=COLORS[color_key], width=1.5, dash=dash_style),
        )
        fig_dual.add_annotation(
            x=ym, y=1,
            xref="x", yref="paper",
            text=label,
            showarrow=False,
            xanchor="left",
            yanchor="top",
            font=dict(size=10, color=COLORS[color_key]),
            bgcolor="rgba(255,255,255,0.7)",
        )

fig_dual.update_yaxes(
    title_text="Average LBP price",
    secondary_y=False,
    tickformat=",",
    gridcolor="#E5E5E5",
)
fig_dual.update_yaxes(
    title_text="Average USD price",
    secondary_y=True,
    tickprefix="$",
    showgrid=False,
)
fig_dual.update_xaxes(
    title_text="",
    tickangle=-45,
    nticks=16,
    showgrid=False,
)
fig_dual.update_layout(
    height=420,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=60, r=60, t=40, b=60),
    hovermode="x unified",
)

st.plotly_chart(fig_dual, use_container_width=True)

st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Chart 3: Exchange rate vs basket USD price — scatter with OLS trendline
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>Exchange Rate vs Basket USD Price</h3>",
    unsafe_allow_html=True,
)
st.caption(
    "Each dot is one month. X = unofficial LBP/USD rate · Y = average basket price in USD. "
    "The strong correlation shows USD prices rose with the exchange rate, not just in LBP terms."
)

r, r2 = rate_vs_basket_r_squared(basket, exrate)

usd_m  = monthly_basket_usd(basket)
rate_m = monthly_unofficial_rate(exrate)
scatter_df = pd.merge(usd_m, rate_m, on="year_month", suffixes=("_basket", "_rate")).dropna()

fig_scatter = px.scatter(
    scatter_df,
    x="price",
    y="usdprice",
    trendline="ols",
    labels={"price": "Unofficial LBP/USD rate", "usdprice": "Avg basket price (USD)"},
    color_discrete_sequence=[COLORS["steel_blue"]],
    hover_data={"year_month": True, "price": ":.0f", "usdprice": ":.2f"},
)

fig_scatter.update_traces(
    selector=dict(mode="markers"),
    marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color="white")),
)
fig_scatter.update_traces(
    selector=dict(mode="lines"),
    line=dict(color=COLORS["crisis_red"], width=2),
)

# Annotate R²
fig_scatter.add_annotation(
    xref="paper", yref="paper",
    x=0.05, y=0.95,
    text=f"<b>R² = {r2:.3f}</b>  (r = {r:.3f})",
    showarrow=False,
    font=dict(size=14, color=COLORS["deep_navy"]),
    bgcolor="white",
    bordercolor=COLORS["deep_navy"],
    borderwidth=1,
    borderpad=8,
)

fig_scatter.update_layout(
    height=420,
    margin=dict(l=60, r=20, t=20, b=60),
    xaxis=dict(tickformat=",", gridcolor="#E5E5E5"),
    yaxis=dict(tickprefix="$", gridcolor="#E5E5E5"),
)

st.plotly_chart(fig_scatter, use_container_width=True)

st.markdown(
    f"<p style='font-size:13px;color:#555'>Pearson R computed from {len(scatter_df)} monthly observations over the overlapping date range of WFP food prices and unofficial exchange rate data.</p>",
    unsafe_allow_html=True,
)
