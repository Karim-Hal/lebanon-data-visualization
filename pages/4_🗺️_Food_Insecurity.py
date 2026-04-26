import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import COLORS
from src.data_loader import load_ipc_geo, load_ipc_population_groups, load_wfp_prices

st.set_page_config(page_title="Food Insecurity · Lebanon Crisis", page_icon="🗺️", layout="wide")

ASSETS = Path(__file__).parent.parent / "assets"
GEOJSON_PATH = ASSETS / "geoBoundaries-LBN-ADM1_simplified.geojson"

# Mapping: IPC admin1_normalized sub-district → main governorate
# GeoJSON shapeNames now match the 8 main governorate names used in our data.
IPC_TO_GOV = {
    "Akkar":            "Akkar",
    "Baalbek-El Hermel":"Baalbek-El Hermel",
    "Baalbek":          "Baalbek-El Hermel",
    "El hermel":        "Baalbek-El Hermel",
    "Zahie":            "Baalbek-El Hermel",
    "Beirut":           "Beirut",
    "Bekaa":            "Bekaa",
    "Rachaya":          "Bekaa",
    "North":            "North",
    "El koura":         "North",
    "El batroun":       "North",
    "Bcharre":          "North",
    "Zgharta":          "North",
    "South":            "South",
    "El Nabatieh":      "El Nabatieh",
    "Bent jbell":       "El Nabatieh",
    "Hasbaya":          "El Nabatieh",
    "Jezzine":          "El Nabatieh",
    "Marjaayoun":       "El Nabatieh",
    "Mount Lebanon":    "Mount Lebanon",
    "Jbell":            "Mount Lebanon",
}

PHASE_COLS = {
    "Phase 1": ("Phase 1 percentage current", COLORS["ipc_phase_1"]),
    "Phase 2": ("Phase 2 percentage current", COLORS["ipc_phase_2"]),
    "Phase 3": ("Phase 3 percentage current", COLORS["ipc_phase_3"]),
    "Phase 4": ("Phase 4 percentage current", COLORS["ipc_phase_4"]),
    "Phase 5": ("Phase 5 percentage current", COLORS["ipc_phase_5"]),
}

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
geo     = load_ipc_geo()
ipc_pop = load_ipc_population_groups()
prices  = load_wfp_prices()

geo["gov"] = geo["admin1_normalized"].map(IPC_TO_GOV)

# ---------------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------------
st.markdown(
    f"<h1 style='color:{COLORS['deep_navy']}'>Act 2 Extended — Who Suffers Most</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#555;font-size:15px'>IPC food insecurity phases by governorate and population group.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ---------------------------------------------------------------------------
# Date slicer
# ---------------------------------------------------------------------------
available_dates = sorted(geo["analysis_date"].dropna().unique())
date_labels     = [pd.Timestamp(d).strftime("%b %Y") for d in available_dates]
date_label_map  = dict(zip(date_labels, available_dates))

selected_label = st.select_slider(
    "IPC snapshot date",
    options=date_labels,
    value=date_labels[-1],
)
selected_date = pd.Timestamp(date_label_map[selected_label])

geo_snap = geo[geo["analysis_date"] == selected_date].copy()

# ---------------------------------------------------------------------------
# Row 1: Choropleth + Donut
# ---------------------------------------------------------------------------
col_map, col_donut = st.columns([3, 2])

# --- Choropleth ---
with col_map:
    st.markdown(
        f"<h3 style='color:{COLORS['deep_navy']}'>IPC Phase 3+ by Governorate</h3>",
        unsafe_allow_html=True,
    )

    if not GEOJSON_PATH.exists():
        st.warning(
            "GeoJSON not found at `assets/geoBoundaries-LBN-ADM1_simplified.geojson`. "
            "Download from HDX Lebanon ADM1 boundaries and place it there."
        )
    else:
        with open(GEOJSON_PATH) as f:
            geojson = json.load(f)

        choro_df = (
            geo_snap.dropna(subset=["gov"])
            .groupby("gov", as_index=False)
            .agg(phase3_pct=("Phase 3+ percentage current", "mean"))
        )
        choro_df["phase3_pct_display"] = (choro_df["phase3_pct"] * 100).round(1)

        # Keserwan-Jbeil is a separate GeoJSON feature carved out of Mount Lebanon.
        # IPC data doesn't distinguish it, so assign it Mount Lebanon's value.
        ml_row = choro_df[choro_df["gov"] == "Mount Lebanon"]
        if not ml_row.empty:
            kj_row = ml_row.copy()
            kj_row["gov"] = "Keserwan-Jbeil"
            choro_df = pd.concat([choro_df, kj_row], ignore_index=True)

        fig_choro = px.choropleth_mapbox(
            choro_df,
            geojson=geojson,
            locations="gov",
            featureidkey="properties.shapeName",
            color="phase3_pct_display",
            color_continuous_scale=[
                [0,   "#C8E6C9"],
                [0.3, COLORS["ipc_phase_3"]],
                [0.6, COLORS["ipc_phase_4"]],
                [1,   COLORS["ipc_phase_5"]],
            ],
            range_color=(0, 60),
            mapbox_style="carto-positron",
            center={"lat": 33.85, "lon": 35.86},
            zoom=7,
            opacity=0.75,
            labels={"phase3_pct_display": "Phase 3+ (%)"},
            hover_name="gov",
            hover_data={"gov": False, "phase3_pct_display": True},
        )

        fig_choro.update_layout(
            height=450,
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_colorbar=dict(
                title="Phase 3+%",
                ticksuffix="%",
                len=0.7,
            ),
        )
        st.plotly_chart(fig_choro, use_container_width=True)

# --- Population group donut ---
with col_donut:
    st.markdown(
        f"<h3 style='color:{COLORS['deep_navy']}'>Phase 3+ by Population Group</h3>",
        unsafe_allow_html=True,
    )

    pop_dates = sorted(ipc_pop["analysis_date"].unique())
    closest_pop_date = min(
        pop_dates,
        key=lambda d: abs((pd.Timestamp(d) - selected_date).days)
    )
    pop_snap = ipc_pop[ipc_pop["analysis_date"] == closest_pop_date].copy()
    pop_snap = pop_snap.dropna(subset=["Phase 3+ number current"])

    if pop_snap.empty:
        st.info("No population group data available for this snapshot.")
    else:
        donut_colors = [
            "#2E74B5", "#C00000", "#1F7A8C", "#E36C09", "#1F3864"
        ]
        fig_donut = px.pie(
            pop_snap,
            names="Level 1",
            values="Phase 3+ number current",
            hole=0.5,
            color_discrete_sequence=donut_colors,
        )
        fig_donut.update_traces(
            textposition="outside",
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>%{value:,.0f} people<br>%{percent}<extra></extra>",
        )
        fig_donut.update_layout(
            height=420,
            margin=dict(l=20, r=20, t=20, b=20),
            showlegend=False,
            annotations=[dict(
                text=f"<b>{pop_snap['Phase 3+ number current'].sum()/1e6:.2f}M</b><br>people",
                x=0.5, y=0.5,
                font=dict(size=14, color=COLORS["deep_navy"]),
                showarrow=False,
            )],
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        st.caption(f"Population group data: closest snapshot = {pd.Timestamp(closest_pop_date).strftime('%b %Y')}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Chart: IPC phase stacked bar by governorate
# ---------------------------------------------------------------------------
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>IPC Phase Distribution by Governorate</h3>",
    unsafe_allow_html=True,
)
st.caption("Stacked bars show % of analysed population in each IPC phase. Phases 3–5 (shaded) indicate food insecurity.")

# Aggregate to GeoJSON governorate level for a cleaner bar chart
bar_df = (
    geo_snap.dropna(subset=["gov"])
    .groupby("gov", as_index=False)
    .agg({col: "mean" for col, _ in PHASE_COLS.values()})
)

# Sort by Phase 3+ descending
bar_df["phase3plus"] = bar_df[["Phase 3 percentage current",
                                "Phase 4 percentage current",
                                "Phase 5 percentage current"]].sum(axis=1)
bar_df = bar_df.sort_values("phase3plus", ascending=False)

fig_bar = go.Figure()
for phase_name, (col, color) in PHASE_COLS.items():
    fig_bar.add_trace(go.Bar(
        name=phase_name,
        x=bar_df["gov"],
        y=(bar_df[col] * 100).round(1),
        marker_color=color,
        marker_line_width=0,
        hovertemplate=f"<b>%{{x}}</b><br>{phase_name}: %{{y:.1f}}%<extra></extra>",
    ))

fig_bar.update_layout(
    barmode="stack",
    height=400,
    margin=dict(l=40, r=20, t=20, b=80),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    yaxis=dict(title="% of population", ticksuffix="%", gridcolor="#E5E5E5", range=[0, 100]),
    xaxis=dict(title="", tickangle=-30),
    hovermode="x unified",
)

st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Chart: Food price by governorate (most recent 12 months, basket items)
# ---------------------------------------------------------------------------
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>Average Basket Price by Governorate — Last 12 Months</h3>",
    unsafe_allow_html=True,
)
st.caption("Average USD price of basket commodities per governorate. admin1 = governorate in WFP data.")

from src.config import BASKET

cutoff = prices["date"].max() - pd.DateOffset(months=12)
gov_price = (
    prices[prices["commodity"].isin(BASKET) & (prices["date"] >= cutoff)]
    .groupby("admin1", as_index=False)["usdprice"]
    .mean()
    .sort_values("usdprice", ascending=True)
)

fig_gov = go.Figure(go.Bar(
    x=gov_price["usdprice"],
    y=gov_price["admin1"],
    orientation="h",
    marker_color=COLORS["steel_blue"],
    hovertemplate="<b>%{y}</b><br>Avg USD: $%{x:.2f}<extra></extra>",
))

fig_gov.update_layout(
    height=340,
    margin=dict(l=20, r=40, t=10, b=40),
    xaxis=dict(title="Avg basket price (USD)", tickprefix="$", gridcolor="#E5E5E5"),
    yaxis=dict(title=""),
)

st.plotly_chart(fig_gov, use_container_width=True)
