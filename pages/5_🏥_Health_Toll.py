import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.config import COLORS
from src.data_loader import load_basket_prices, load_health, load_u5mort_mena
from src.metrics import basket_price_index

st.set_page_config(page_title="Health Toll · Lebanon Crisis", page_icon="🏥", layout="wide")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
health = load_health()
basket = load_basket_prices()
u5mort = load_u5mort_mena()

# Both-sexes / total rows only, year >= 2000
health_btsx = health[
    health["DIMENSION (CODE)"].isin(["SEX_BTSX", "HOUSEHOLDWEALTH_TOTL"]) &
    (health["YEAR (DISPLAY)"] >= 2000)
].copy()

# ---------------------------------------------------------------------------
# Indicator config — short labels for pills
# ---------------------------------------------------------------------------
INDICATOR_SHORT_NAMES = {
    "NUTSTUNTINGPREV":                "Stunting %",
    "NUTSTUNTINGNUM":                 "Stunting count",
    "NUTRITION_ANAEMIA_CHILDREN_PREV":"Anaemia (children)",
    "MDG_0000000007":                 "Under-5 mortality",
    "MDG_0000000001":                 "Infant mortality",
    "WHOSIS_000003":                  "Neonatal mortality",
    "NUTRITION_WH_2":                 "Wasting %",
    "NUTRITION_WA_2":                 "Underweight %",
    "MORTADO":                        "Adolescent mortality",
    "WHOSIS_000004":                  "Adult mortality",
}
# Drop any codes with no data after the year filter
_available = set(health_btsx["GHO (CODE)"].unique())
INDICATOR_SHORT_NAMES = {k: v for k, v in INDICATOR_SHORT_NAMES.items() if k in _available}

SHORT_TO_CODE = {v: k for k, v in INDICATOR_SHORT_NAMES.items()}
CODE_TO_SHORT = INDICATOR_SHORT_NAMES
pill_options  = list(INDICATOR_SHORT_NAMES.values())

_lbl_df   = health_btsx[health_btsx["GHO (CODE)"].isin(INDICATOR_SHORT_NAMES)][["GHO (CODE)", "GHO (DISPLAY)"]].drop_duplicates()
CODE_TO_FULL = dict(zip(_lbl_df["GHO (CODE)"], _lbl_df["GHO (DISPLAY)"]))

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
# Chart 1: Dual-panel lag timeline — food prices vs stunting
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
basket_annual = basket_annual[basket_annual["year"] >= 2000]

stunt = (
    health_btsx[health_btsx["GHO (CODE)"] == "NUTSTUNTINGPREV"]
    [["YEAR (DISPLAY)", "Numeric"]]
    .dropna()
    .sort_values("YEAR (DISPLAY)")
)

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
        line=dict(color="#ff595e", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(255,89,94,0.08)",
        hovertemplate="<b>%{x}</b><br>Price Index: %{y:.0f}<extra></extra>",
    ),
    row=1, col=1,
)
fig_lag.add_trace(
    go.Scatter(
        x=stunt["YEAR (DISPLAY)"],
        y=stunt["Numeric"],
        name="Stunting %",
        line=dict(color="#6a4c93", width=2.5),
        mode="lines+markers",
        marker=dict(size=6, color="#6a4c93"),
        hovertemplate="<b>%{x}</b><br>Stunting: %{y:.1f}%<extra></extra>",
    ),
    row=2, col=1,
)
for r in [1, 2]:
    fig_lag.add_vrect(x0=2020, x1=2022, fillcolor=COLORS["warning"], opacity=0.08, line_width=0, row=r, col=1)  # type: ignore[arg-type]
    for yr in [2020, 2022]:
        fig_lag.add_vline(x=yr, line_dash="dash", line_color=COLORS["warning"], line_width=1, opacity=0.6, row=r, col=1)  # type: ignore[arg-type]

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
fig_lag.update_layout(height=520, margin=dict(l=60, r=20, t=40, b=40), showlegend=False, hovermode="x unified")
st.plotly_chart(fig_lag, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Chart 2: Health Indicator Explorer — pill buttons + normalized multi-select
# ---------------------------------------------------------------------------
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>Health Indicator Explorer</h3>",
    unsafe_allow_html=True,
)

TRACE_COLORS = [
    "#1982c4", "#ff595e", "#8ac926", "#6a4c93", "#ffca3a",
    "#46dff7", "#a99df2", "#ff89a6", "#7f6aa3", "#af848c",
]

selected_pills = st.pills(
    "Select indicators — pick multiple to compare on a normalized scale",
    options=pill_options,
    selection_mode="multi",
    default=[pill_options[0]],
    key="indicator_pills",
)

selected_codes = [SHORT_TO_CODE[p] for p in (selected_pills or [])]

if not selected_codes:
    st.info("Select at least one indicator above to display the chart.")
else:
    multi_mode = len(selected_codes) > 1
    fig_ind = go.Figure()

    for i, code in enumerate(selected_codes):
        df_i = (
            health_btsx[health_btsx["GHO (CODE)"] == code]
            [["YEAR (DISPLAY)", "Numeric"]]
            .dropna()
            .sort_values("YEAR (DISPLAY)")
        )
        if df_i.empty:
            continue

        color      = TRACE_COLORS[i % len(TRACE_COLORS)]
        short_name = CODE_TO_SHORT.get(code, code)

        if multi_mode:
            vmin, vmax = df_i["Numeric"].min(), df_i["Numeric"].max()
            y_vals     = (df_i["Numeric"] - vmin) / (vmax - vmin) * 100 if vmax > vmin else df_i["Numeric"] * 0 + 50
            hover      = f"<b>%{{x}}</b><br>{short_name}: %{{customdata:.2f}} (raw)<extra></extra>"
            fig_ind.add_trace(go.Scatter(
                x=df_i["YEAR (DISPLAY)"], y=y_vals,
                name=short_name, mode="lines+markers",
                line=dict(color=color, width=2.5),
                marker=dict(size=6, color=color),
                customdata=df_i["Numeric"].values,
                hovertemplate=hover,
            ))
        else:
            fig_ind.add_trace(go.Scatter(
                x=df_i["YEAR (DISPLAY)"], y=df_i["Numeric"],
                name=short_name, mode="lines+markers",
                line=dict(color=color, width=2.5),
                marker=dict(size=6, color=color),
                fill="tozeroy",
                fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
                hovertemplate=f"<b>%{{x}}</b><br>{short_name}: %{{y:.2f}}<extra></extra>",
            ))

    all_years = health_btsx[health_btsx["GHO (CODE)"].isin(selected_codes)]["YEAR (DISPLAY)"].dropna()
    if not all_years.empty and int(all_years.min()) <= 2021 and int(all_years.max()) >= 2019:
        _ind_events = [
            (2019, "Banking crisis",  0.97, "right"),
            (2020, "Port explosion",  0.58, "left"),
            (2021, "Subsidy removal", 0.97, "left"),
        ]
        for yr, lbl, y_paper, anchor in _ind_events:
            if int(all_years.min()) <= yr <= int(all_years.max()):
                fig_ind.add_vline(x=yr, line_dash="dash", line_color=COLORS["warning"], line_width=1.5)
                fig_ind.add_annotation(
                    x=yr, y=y_paper, xref="x", yref="paper",
                    text=lbl, showarrow=False,
                    font=dict(size=10, color=COLORS["warning"]),
                    xanchor=anchor, yanchor="top",
                    bgcolor="rgba(255,255,255,0.75)",
                )

    yaxis_title = "Normalized (0 = min, 100 = max)" if multi_mode else "Value"
    fig_ind.update_layout(
        height=400,
        margin=dict(l=60, r=20, t=20, b=40),
        xaxis=dict(title="Year", dtick=2, showgrid=False),
        yaxis=dict(title=yaxis_title, gridcolor="#E5E5E5"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    st.plotly_chart(fig_ind, use_container_width=True)

    if multi_mode:
        st.caption("Each indicator is min-max normalized to 0–100 so different scales align. Hover to see raw values.  ·  Lebanon (LBN)  ·  Source: WHO GHO")
    else:
        full_label = CODE_TO_FULL.get(selected_codes[0], selected_codes[0])
        st.caption(f"Indicator: {full_label}  ·  Lebanon (LBN)  ·  Source: WHO GHO")

st.markdown("---")

# ---------------------------------------------------------------------------
# Chart 3: Key Nutrition & Mortality Trends — small multiples
# ---------------------------------------------------------------------------
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>Key Nutrition & Mortality Trends</h3>",
    unsafe_allow_html=True,
)
st.caption("Model-based / both-sexes estimates. Lebanon (LBN). Data from 2000.")

MULTI_CODES = {
    "Stunting prevalence (%)":       "NUTSTUNTINGPREV",
    "Anaemia in children (%)":       "NUTRITION_ANAEMIA_CHILDREN_PREV",
    "Infant mortality (per 1,000)":  "MDG_0000000001",
    "Under-5 mortality (per 1,000)": "MDG_0000000007",
}
MULTI_COLORS = ["#ff595e", "#ffca3a", "#1982c4", "#6a4c93"]

fig_multi = make_subplots(
    rows=2, cols=2,
    subplot_titles=list(MULTI_CODES.keys()),
    vertical_spacing=0.14,
    horizontal_spacing=0.10,
)
for (title, code), (row, col), color in zip(MULTI_CODES.items(), [(1,1),(1,2),(2,1),(2,2)], MULTI_COLORS):
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
            x=df_m["YEAR (DISPLAY)"], y=df_m["Numeric"],
            mode="lines+markers", line=dict(color=color, width=2),
            marker=dict(size=4), showlegend=False,
            hovertemplate="<b>%{x}</b><br>%{y:.2f}<extra></extra>",
        ),
        row=row, col=col,
    )
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
fig_multi.update_layout(height=520, margin=dict(l=40, r=20, t=50, b=40))
st.plotly_chart(fig_multi, use_container_width=True)

st.markdown("---")

# ---------------------------------------------------------------------------
# Chart 5: Dumbbell — Lebanon 2019 vs latest year across all indicators
# ---------------------------------------------------------------------------
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>Lebanon Child Health: Before & After the Economic Collapse</h3>",
    unsafe_allow_html=True,
)
st.caption(
    "Percentage change in key health indicators between 2019 and the latest available year. "
    "All indicators shown are 'lower is better' — teal means the situation improved, red means it worsened. "
    "Hover to see the exact values."
)

_DB_CODES = {
    "Under-5 mortality":    "MDG_0000000007",
    "Infant mortality":     "MDG_0000000001",
    "Neonatal mortality":   "WHOSIS_000003",
    "Adolescent mortality": "MORTADO",
    "Stunting %":           "NUTSTUNTINGPREV",
    "Wasting %":            "NUTRITION_WH_2",
    "Underweight %":        "NUTRITION_WA_2",
    "Anaemia (children)":   "NUTRITION_ANAEMIA_CHILDREN_PREV",
}

_db_rows = []
for _short, _code in _DB_CODES.items():
    _dfc = (
        health_btsx[health_btsx["GHO (CODE)"] == _code]
        [["YEAR (DISPLAY)", "Numeric"]]
        .dropna()
        .sort_values("YEAR (DISPLAY)")
    )
    if len(_dfc) < 2:
        continue
    # Closest available year ≤ 2019 as the pre-crisis baseline
    _pre = _dfc[_dfc["YEAR (DISPLAY)"] <= 2019]
    if _pre.empty:
        continue
    _base = _pre.iloc[-1]
    _latest = _dfc.iloc[-1]
    if int(_base["YEAR (DISPLAY)"]) == int(_latest["YEAR (DISPLAY)"]):
        continue  # no post-2019 data for this indicator
    _pct    = float((_latest["Numeric"] - _base["Numeric"]) / _base["Numeric"] * 100)
    _db_rows.append({
        "indicator":   _short,
        "val_base":    float(_base["Numeric"]),
        "yr_base":     int(_base["YEAR (DISPLAY)"]),
        "val_latest":  float(_latest["Numeric"]),
        "yr_latest":   int(_latest["YEAR (DISPLAY)"]),
        "pct":         _pct,
        "improved":    _pct < 0,
    })

# Sort descending so worst is first → ends up at chart bottom; best last → chart top
_db_rows.sort(key=lambda r: r["pct"], reverse=True)

if _db_rows:
    _names = [r["indicator"] for r in _db_rows]

    fig_db = go.Figure()

    # Connecting lines (add_shape supports category names on yref="y")
    for _r in _db_rows:
        _lc = "#8ac926" if _r["improved"] else "#ff595e"
        fig_db.add_shape(
            type="line",
            x0=0, x1=_r["pct"],
            y0=_r["indicator"], y1=_r["indicator"],
            line=dict(color=_lc, width=3),
        )

    # Baseline dots — gray, all at x=0, always labelled "2019" for consistency
    fig_db.add_trace(go.Scatter(
        x=[0] * len(_db_rows),
        y=_names,
        mode="markers",
        marker=dict(color="#BBBBBB", size=13, line=dict(color="white", width=2)),
        name="2019 (baseline)",
        customdata=[[r["val_base"]] for r in _db_rows],
        hovertemplate="<b>%{y}</b><br>2019: %{customdata[0]:.1f}<extra></extra>",
    ))

    # Improved dots — teal
    _imp = [r for r in _db_rows if r["improved"]]
    if _imp:
        fig_db.add_trace(go.Scatter(
            x=[r["pct"] for r in _imp],
            y=[r["indicator"] for r in _imp],
            mode="markers",
            marker=dict(color="#8ac926", size=13, line=dict(color="white", width=2)),
            name="Improved",
            customdata=[[r["yr_latest"], r["val_latest"], r["pct"]] for r in _imp],
            hovertemplate="<b>%{y}</b><br>%{customdata[0]}: %{customdata[1]:.1f}<br>Change since 2019: %{customdata[2]:+.1f}%<extra></extra>",
        ))

    # Worsened dots — red
    _wors = [r for r in _db_rows if not r["improved"]]
    if _wors:
        fig_db.add_trace(go.Scatter(
            x=[r["pct"] for r in _wors],
            y=[r["indicator"] for r in _wors],
            mode="markers",
            marker=dict(color="#ff595e", size=13, line=dict(color="white", width=2)),
            name="Worsened",
            customdata=[[r["yr_latest"], r["val_latest"], r["pct"]] for r in _wors],
            hovertemplate="<b>%{y}</b><br>%{customdata[0]}: %{customdata[1]:.1f}<br>Change since 2019: %{customdata[2]:+.1f}%<extra></extra>",
        ))

    # % change labels next to each colored dot
    for _r in _db_rows:
        _lc    = "#8ac926" if _r["improved"] else "#ff595e"
        _shift = 16 if _r["pct"] >= 0 else -16
        _anch  = "left" if _r["pct"] >= 0 else "right"
        fig_db.add_annotation(
            x=_r["pct"], y=_r["indicator"],
            text=f"{_r['pct']:+.0f}%",
            showarrow=False,
            font=dict(size=10, color=_lc),
            xshift=_shift, xanchor=_anch,
        )

    # Zero reference line — labelled "2019" so the baseline is self-explanatory
    fig_db.add_vline(
        x=0, line_color="#AAAAAA", line_width=1.5,
        annotation_text="2019", annotation_position="top",
        annotation_font_size=11, annotation_font_color="#888888",
    )

    fig_db.update_layout(
        height=max(360, len(_db_rows) * 52),
        margin=dict(l=20, r=80, t=20, b=40),
        xaxis=dict(
            title="Percentage Change Since 2019 (%)",
            showgrid=True, gridcolor="#E5E5E5",
            zeroline=False, ticksuffix="%",
        ),
        yaxis=dict(showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        plot_bgcolor="#FAFAFA",
        hovermode="y",
    )
    st.plotly_chart(fig_db, use_container_width=True)
    st.caption("Source: WHO GHO · Lebanon (LBN). Baseline is the closest available data point at or before 2019, shown uniformly as '2019' for visual consistency.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Chart 6: MENA Regional Under-5 Mortality Comparison
# ---------------------------------------------------------------------------
st.markdown(
    f"<h3 style='color:{COLORS['deep_navy']}'>Regional Under-5 Mortality — MENA Comparison</h3>",
    unsafe_allow_html=True,
)
st.caption(
    "Under-5 mortality rate (probability of dying by age 5 per 1,000 live births). "
    "Lebanon highlighted in red. World average shown as dashed reference.  ·  Source: WHO · 2000–2023."
)

MENA_PEERS = ["Lebanon", "Saudi Arabia", "Jordan", "Syrian Arab Republic", "Egypt", "World"]
MENA_COLORS = {
    "Lebanon":              "#ff595e",
    "Saudi Arabia":         "#1982c4",
    "Jordan":               "#46dff7",
    "Syrian Arab Republic": "#ffca3a",
    "Egypt":                "#6a4c93",
    "World":                "#af848c",
}

u5_filt = u5mort[u5mort["country"].isin(MENA_PEERS)].sort_values(["country", "year"])
fig_mena = go.Figure()

for country in MENA_PEERS:
    cdf = u5_filt[u5_filt["country"] == country]
    if cdf.empty:
        continue
    is_lebanon = country == "Lebanon"
    is_world   = country == "World"
    fig_mena.add_trace(go.Scatter(
        x=cdf["year"],
        y=cdf["rate"],
        name=country,
        mode="lines+markers",
        line=dict(
            color=MENA_COLORS.get(country, "#888888"),
            width=3 if is_lebanon else 2,
            dash="dash" if is_world else "solid",
        ),
        marker=dict(size=5 if is_lebanon else 4),
        hovertemplate=f"<b>{country}</b><br>%{{x}}: %{{y:.1f}} per 1,000<extra></extra>",
    ))

# Staggered annotations: left / mid / right so labels don't collide
_mena_events = [
    (2019, "Banking crisis",   0.97, "right"),   # top, text sits left of line
    (2020, "Port explosion",   0.58, "left"),    # mid-height, text sits right of line
    (2021, "Subsidy removal",  0.97, "left"),    # top, text sits right of line
]
for yr, lbl, y_paper, anchor in _mena_events:
    fig_mena.add_vline(x=yr, line_dash="dash", line_color=COLORS["warning"], line_width=1.5)
    fig_mena.add_annotation(
        x=yr, y=y_paper, xref="x", yref="paper",
        text=lbl, showarrow=False,
        font=dict(size=10, color=COLORS["warning"]),
        xanchor=anchor, yanchor="top",
        bgcolor="rgba(255,255,255,0.75)",
    )

fig_mena.update_layout(
    height=440,
    margin=dict(l=60, r=80, t=20, b=40),
    xaxis=dict(title="Year", dtick=2, showgrid=False),
    yaxis=dict(title="Under-5 mortality (per 1,000 live births)", gridcolor="#E5E5E5"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    hovermode="x unified",
)
st.plotly_chart(fig_mena, use_container_width=True)
