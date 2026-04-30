"""Lebanon Crisis Dashboard — HTML Report Generator.
Run: python generate_report.py  ->  writes report.html
"""

# -- Streamlit stub (must come before any src/ import) -----------------------
import sys
from types import ModuleType
_st = ModuleType("streamlit")
_st.cache_data = lambda f: f          # identity: no caching, no crash
sys.modules["streamlit"] = _st

# -- Standard library ---------------------------------------------------------
import json
from pathlib import Path

# -- Third-party --------------------------------------------------------------
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import pearsonr

# -- Project ------------------------------------------------------------------
from src.config import (
    BASKET, COLORS, COUNTRY_COLORS, EVENTS, PALETTE,
    POPULATION_GROUPS, SERIES,
)
from src.data_loader import (
    load_basket_prices, load_exchange_rate, load_health,
    load_ipc_geo, load_ipc_population_groups,
    load_u5mort_mena, load_wdi, load_wfp_prices,
)
from src.metrics import (
    basket_price_index, gdp_contraction, lebanese_phase3_plus,
    latest_unofficial_rate, lebanon_peak_inflation,
    monthly_basket_lbp, monthly_basket_usd,
    monthly_unofficial_rate, rate_vs_basket_r_squared,
)

# -- Paths --------------------------------------------------------------------
ROOT         = Path(__file__).parent
ASSETS       = ROOT / "assets"
GEOJSON_PATH = ASSETS / "geoBoundaries-LBN-ADM1_simplified.geojson"

# -- Global Plotly style ------------------------------------------------------
_BASE = dict(
    font=dict(family="DM Sans, sans-serif", color="#1F3864", size=12),
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
)

# -- Data loading -------------------------------------------------------------
def load_all():
    return dict(
        wdi    = load_wdi(),
        prices = load_wfp_prices(),
        exrate = load_exchange_rate(),
        basket = load_basket_prices(),
        ipc_geo= load_ipc_geo(),
        ipc_pop= load_ipc_population_groups(),
        health = load_health(),
        u5mort = load_u5mort_mena(),
    )

# =============================================================================
# HTML primitives
# =============================================================================

CSS = (
    ":root{"
    "--navy:#1F3864;--red:#C00000;--blue:#2E74B5;"
    "--bg:#F4F6F9;--white:#FFFFFF;--card-bg:#EBF3FB;"
    "--muted:#6B7280;--border:#D5DCE8;"
    "--shadow:0 2px 10px rgba(31,56,100,0.08);"
    "}"
    "*{box-sizing:border-box;margin:0;padding:0}"
    "html{scroll-behavior:smooth}"
    "body{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--navy)}"

    "nav{"
    "position:fixed;top:0;left:0;right:0;z-index:100;"
    "height:54px;background:var(--navy);"
    "display:flex;align-items:center;justify-content:space-between;"
    "padding:0 48px;box-shadow:0 1px 16px rgba(0,0,0,0.22);"
    "}"
    ".brand{"
    "font-family:'DM Serif Display',serif;font-size:17px;"
    "color:white;letter-spacing:-0.01em;white-space:nowrap;"
    "}"
    "nav ul{list-style:none;display:flex;gap:28px}"
    "nav ul li a{"
    "font-size:11px;font-weight:600;letter-spacing:0.09em;"
    "text-transform:uppercase;color:rgba(255,255,255,0.55);"
    "text-decoration:none;"
    "padding-bottom:2px;border-bottom:2px solid transparent;"
    "transition:color .2s,border-color .2s;"
    "}"
    "nav ul li a:hover{color:white}"
    "nav ul li a.active{color:white;border-bottom-color:var(--red)}"

    "#s-landing{"
    "background:var(--navy);"
    "padding:106px 60px 72px;"
    "color:white;"
    "}"
    ".hero-kicker{"
    "font-size:10px;font-weight:700;letter-spacing:0.2em;"
    "text-transform:uppercase;color:rgba(255,255,255,0.4);"
    "margin-bottom:18px;"
    "}"
    ".hero h1{"
    "font-family:'DM Serif Display',serif;"
    "font-size:62px;font-weight:400;line-height:1.04;"
    "letter-spacing:-0.025em;margin-bottom:20px;"
    "}"
    ".hero h1 span{color:#ff595e}"
    ".hero-sub{"
    "font-size:16px;color:rgba(255,255,255,0.65);"
    "max-width:620px;line-height:1.75;margin-bottom:52px;"
    "}"
    ".kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin-bottom:48px}"
    ".kpi-card{"
    "background:rgba(255,255,255,0.07);"
    "border:1px solid rgba(255,255,255,0.1);"
    "border-top:3px solid;border-radius:8px;padding:22px 20px;"
    "}"
    ".kpi-label{"
    "font-size:9px;font-weight:700;letter-spacing:0.14em;"
    "text-transform:uppercase;color:rgba(255,255,255,0.45);margin-bottom:14px;"
    "}"
    ".kpi-value{"
    "font-size:42px;font-weight:700;line-height:1;"
    "letter-spacing:-0.02em;color:white;"
    "}"
    ".kpi-sub{font-size:11px;color:rgba(255,255,255,0.35);margin-top:8px;line-height:1.4}"
    ".timeline-wrap{background:rgba(255,255,255,0.04);border-radius:8px;padding:16px 16px 4px}"

    "section{padding:72px 60px}"
    "section:nth-of-type(even){background:var(--white)}"
    "section:nth-of-type(odd){background:var(--bg)}"
    ".section-meta{display:flex;align-items:center;gap:14px;margin-bottom:10px}"
    ".section-tag{"
    "font-size:10px;font-weight:700;letter-spacing:0.12em;"
    "text-transform:uppercase;color:var(--muted);"
    "border:1px solid var(--border);border-radius:20px;padding:3px 12px;"
    "}"
    ".section-eyebrow{font-size:10px;font-weight:600;color:var(--muted);letter-spacing:0.08em;text-transform:uppercase}"
    "h2.section-title{"
    "font-family:'DM Serif Display',serif;"
    "font-size:36px;font-weight:400;color:var(--navy);"
    "letter-spacing:-0.01em;margin-bottom:8px;"
    "}"
    ".section-sub{"
    "font-size:14px;color:var(--muted);margin-bottom:44px;"
    "max-width:680px;line-height:1.65;"
    "}"

    ".chart-card{"
    "background:white;border-radius:10px;"
    "box-shadow:var(--shadow);padding:22px 22px 12px;margin-bottom:22px;"
    "}"
    ".chart-title{font-size:13px;font-weight:600;color:var(--navy);margin-bottom:3px}"
    ".chart-caption{font-size:11px;color:var(--muted);margin-bottom:14px;line-height:1.5}"
    ".plot-container{width:100%}"

    ".g2{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-bottom:22px}"
    ".g55{display:grid;grid-template-columns:55fr 45fr;gap:22px;margin-bottom:22px}"
    ".g60{display:grid;grid-template-columns:60fr 40fr;gap:22px;margin-bottom:22px}"
    ".g65{display:grid;grid-template-columns:65fr 35fr;gap:22px;margin-bottom:22px}"

    ".callout{"
    "background:var(--card-bg);border-left:4px solid var(--blue);"
    "border-radius:0 10px 10px 0;padding:28px 24px;"
    "display:flex;flex-direction:column;justify-content:center;"
    "}"
    ".callout-stat{"
    "font-size:54px;font-weight:700;color:var(--navy);"
    "letter-spacing:-0.03em;line-height:1;"
    "}"
    ".callout-stat-label{"
    "font-size:10px;font-weight:700;letter-spacing:0.12em;"
    "text-transform:uppercase;color:var(--muted);margin-top:8px;margin-bottom:18px;"
    "}"
    ".callout-body{font-size:13px;color:#374151;line-height:1.7}"

    ".tbl-wrap{overflow-x:auto}"
    "table.data-tbl{width:100%;border-collapse:collapse;font-size:12px}"
    "table.data-tbl th{"
    "background:var(--navy);color:white;padding:9px 12px;"
    "font-weight:600;text-align:right;font-size:10px;letter-spacing:0.05em;"
    "text-transform:uppercase;white-space:nowrap;"
    "}"
    "table.data-tbl th:first-child{text-align:left}"
    "table.data-tbl td{"
    "padding:7px 12px;text-align:right;"
    "border-bottom:1px solid var(--border);"
    "}"
    "table.data-tbl td:first-child{text-align:left;font-weight:500}"
    "table.data-tbl tr.lbn td{background:var(--card-bg);color:var(--red);font-weight:700}"

    ".source-line{"
    "font-size:10px;color:var(--muted);margin-top:36px;"
    "padding-top:16px;border-top:1px solid var(--border);"
    "}"

    "::-webkit-scrollbar{width:6px;height:6px}"
    "::-webkit-scrollbar-track{background:transparent}"
    "::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}"
)

NAV_HTML = (
    "<nav>"
    "<span class=\"brand\">Lebanon in Crisis</span>"
    "<ul>"
    "<li><a href=\"#s-landing\">Overview</a></li>"
    "<li><a href=\"#s-macro\">Macro Shock</a></li>"
    "<li><a href=\"#s-food\">Food Prices</a></li>"
    "<li><a href=\"#s-insecurity\">Food Insecurity</a></li>"
    "<li><a href=\"#s-health\">Health Toll</a></li>"
    "</ul>"
    "</nav>"
)

NAV_JS = (
    "(function(){"
    "const sections=document.querySelectorAll('#s-landing,section[id]');"
    "const links=document.querySelectorAll('nav ul li a');"
    "const obs=new IntersectionObserver(entries=>{"
    "entries.forEach(e=>{"
    "if(e.isIntersecting){"
    "links.forEach(l=>l.classList.remove('active'));"
    "const a=document.querySelector('nav ul li a[href=\"#'+e.target.id+'\"]');"
    "if(a)a.classList.add('active');"
    "}"
    "});"
    "},{threshold:0.25});"
    "sections.forEach(s=>obs.observe(s));"
    "})();"
)

PLOTLY_RENDER_JS = (
    "(function(){"
    "const cfg={responsive:true,displayModeBar:true,displaylogo:false,"
    "modeBarButtonsToRemove:['lasso2d','select2d','toImage']};"
    "document.querySelectorAll('script[type=\"application/json\"][data-plot]').forEach(el=>{"
    "const fig=JSON.parse(el.textContent);"
    "const div=document.getElementById(el.dataset.plot);"
    "if(div)Plotly.newPlot(div,fig.data,fig.layout,cfg);"
    "});"
    "})();"
)


def _plot_tag(fig_id, fig_json):
    return (
        '<script type="application/json" data-plot="plot-' + fig_id + '">' + fig_json + '</script>\n'
        '<div id="plot-' + fig_id + '" class="plot-container"></div>'
    )


def build_html(body):
    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "<meta charset=\"UTF-8\"/>\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"/>\n"
        "<title>Lebanon in Crisis - Data Dashboard</title>\n"
        "<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\"/>\n"
        "<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin/>\n"
        "<link href=\"https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1"
        "&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700"
        "&display=swap\" rel=\"stylesheet\"/>\n"
        "<script src=\"https://cdn.plot.ly/plotly-2.35.2.min.js\"></script>\n"
        "<style>" + CSS + "</style>\n"
        "</head>\n"
        "<body>\n"
        + NAV_HTML + "\n"
        + body + "\n"
        "<script>" + NAV_JS + "</script>\n"
        "<script>" + PLOTLY_RENDER_JS + "</script>\n"
        "</body>\n"
        "</html>"
    )


# =============================================================================
# Figure builders
# =============================================================================

def _fig_timeline():
    event_dates  = [pd.Timestamp(e[0]) for e in EVENTS]
    event_labels = [e[1]               for e in EVENTS]
    event_colors = [COLORS[e[2]]       for e in EVENTS]

    fig = go.Figure()
    fig.add_shape(
        type="line",
        x0=pd.Timestamp("2019-01-01"), x1=pd.Timestamp("2022-06-01"),
        y0=0, y1=0,
        line=dict(color="rgba(255,255,255,0.4)", width=2),
    )
    for dt, label, color in zip(event_dates, event_labels, event_colors):
        fig.add_trace(go.Scatter(
            x=[dt], y=[0], mode="markers",
            marker=dict(size=16, color=color, line=dict(width=2, color="white")),
            hovertemplate="<b>" + label + "</b><br>" + dt.strftime("%B %Y") + "<extra></extra>",
            showlegend=False,
        ))
        fig.add_annotation(
            x=dt, y=0,
            text="<b>" + dt.strftime("%b %Y") + "</b><br>" + label,
            showarrow=True, arrowhead=2, arrowcolor=color, arrowwidth=1.5,
            ax=0, ay=-60,
            font=dict(size=11, color=color, family="DM Sans, sans-serif"),
            bgcolor="rgba(31,56,100,0.85)", bordercolor=color,
            borderwidth=1.5, borderpad=6,
        )
    fig.update_layout(
        font=dict(family="DM Sans, sans-serif", color="rgba(255,255,255,0.6)", size=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=185,
        margin=dict(l=20, r=20, t=10, b=10),
        xaxis=dict(
            showgrid=False, zeroline=False,
            range=[pd.Timestamp("2018-06-01"), pd.Timestamp("2022-09-01")],
            tickformat="%Y", color="rgba(255,255,255,0.4)",
        ),
        yaxis=dict(visible=False, range=[-1, 1]),
    )
    return fig.to_json()


def _fig_gdp_rate(wdi):
    lbn_gdp = wdi[(wdi["Country Name"] == "Lebanon") & (wdi["Series Code"] == SERIES["gdp"])].copy()
    lbn_gdp["gdp_bn"] = lbn_gdp["Value"] / 1e9
    lbn_fx  = wdi[(wdi["Country Name"] == "Lebanon") & (wdi["Series Code"] == SERIES["official_fx"])].copy()

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=lbn_gdp["Year"], y=lbn_gdp["gdp_bn"], name="GDP (USD bn)",
        line=dict(color=COLORS["crisis_red"], width=2.5), mode="lines+markers",
        marker=dict(size=5),
        hovertemplate="<b>%{x}</b><br>GDP: $%{y:.1f}B<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=lbn_fx["Year"], y=lbn_fx["Value"], name="Official LBP/USD",
        line=dict(color=COLORS["steel_blue"], width=2.5, dash="dot"), mode="lines+markers",
        marker=dict(size=5),
        hovertemplate="<b>%{x}</b><br>Rate: %{y:,.0f} LBP/USD<extra></extra>",
    ), secondary_y=True)

    for date_str, label, color_key, dash in EVENTS:
        yr = pd.Timestamp(date_str).year + (pd.Timestamp(date_str).month - 1) / 12
        fig.add_vline(x=yr, line_dash=dash, line_color=COLORS[color_key], line_width=1.5,
                      annotation_text=label, annotation_position="top left",
                      annotation_font_size=10, annotation_font_color=COLORS[color_key])

    fig.update_yaxes(title_text="GDP (USD billions)", secondary_y=False,
                     tickprefix="$", ticksuffix="B", gridcolor="#EEF1F5")
    fig.update_yaxes(title_text="Official LBP per USD", secondary_y=True,
                     tickformat=",", showgrid=False)
    fig.update_xaxes(title_text="Year", dtick=1, showgrid=False)
    fig.update_layout(**_BASE, height=420, margin=dict(l=60, r=60, t=44, b=48),
                      hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig.to_json()


def _fig_inflation(wdi):
    inf_all = wdi[wdi["Series Code"] == SERIES["inflation"]].copy()
    fig = px.line(
        inf_all.sort_values(["Country Name", "Year"]),
        x="Year", y="Value",
        color="Country Name",
        facet_col="Country Name", facet_col_wrap=3,
        color_discrete_map=COUNTRY_COLORS,
        labels={"Value": "Inflation (%)", "Year": ""},
        markers=True,
    )
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.for_each_annotation(
        lambda a: a.update(font=dict(color=COLORS["crisis_red"], size=12, family="DM Sans, sans-serif"))
        if a.text == "Lebanon"
        else a.update(font=dict(color=COLORS["deep_navy"], size=11, family="DM Sans, sans-serif"))
    )
    for date_str, _, color_key, dash in EVENTS:
        yr = pd.Timestamp(date_str).year + (pd.Timestamp(date_str).month - 1) / 12
        fig.add_vline(x=yr, line_dash=dash, line_color=COLORS[color_key], line_width=1, opacity=0.6)
    fig.update_yaxes(matches=None, showticklabels=True, ticksuffix="%", gridcolor="#EEF1F5")
    fig.update_xaxes(dtick=3, tickangle=-45, showgrid=False)
    fig.update_traces(marker=dict(size=4), line=dict(width=2))
    fig.update_layout(**_BASE, height=500, showlegend=False,
                      margin=dict(l=40, r=20, t=60, b=40))
    return fig.to_json()


def _html_gdp_table(wdi):
    gdp_pc = (
        wdi[wdi["Series Code"] == SERIES["gdp_pc"]]
        .pivot_table(index="Country Name", columns="Year", values="Value")
        .round(0)
    )
    years = [y for y in range(2011, 2025) if y in gdp_pc.columns]
    rows_html = ""
    for country in gdp_pc.index:
        cls = ' class="lbn"' if country == "Lebanon" else ""
        cells = "".join(
            "<td>" + ("&mdash;" if pd.isna(gdp_pc.loc[country, yr]) else "${:,.0f}".format(gdp_pc.loc[country, yr])) + "</td>"
            for yr in years
        )
        rows_html += "<tr" + cls + "><td>" + country + "</td>" + cells + "</tr>\n"
    header = "<th>Country</th>" + "".join("<th>" + str(y) + "</th>" for y in years)
    return (
        '<div class="tbl-wrap">'
        '<table class="data-tbl">'
        "<thead><tr>" + header + "</tr></thead>"
        "<tbody>" + rows_html + "</tbody>"
        "</table></div>"
    )


def _fig_price_index(prices):
    df = (
        prices[prices["commodity"].isin(BASKET)]
        .groupby(["date", "commodity"], as_index=False)["price_index"]
        .mean()
        .sort_values("date")
    )
    commodities = sorted(df["commodity"].unique())
    color_map = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(commodities)}

    fig = px.line(
        df, x="date", y="price_index", color="commodity",
        color_discrete_map=color_map,
        labels={"price_index": "Price Index (2019=100)", "date": "", "commodity": "Commodity"},
    )
    fig.add_hline(y=100, line_dash="dot", line_color=COLORS["deep_navy"], line_width=1.5,
                  annotation_text="2019 baseline", annotation_position="bottom right",
                  annotation_font_size=10)
    for date_str, label, color_key, dash in EVENTS:
        fig.add_vline(x=pd.Timestamp(date_str).timestamp() * 1000,
                      line_dash=dash, line_color=COLORS[color_key], line_width=1.5,
                      annotation_text=label, annotation_position="top right",
                      annotation_font_size=10, annotation_font_color=COLORS[color_key])
    fig.update_layout(**_BASE, height=420, margin=dict(l=52, r=24, t=44, b=52),
                      hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                      yaxis=dict(gridcolor="#EEF1F5"))
    fig.update_xaxes(showgrid=False)
    return fig.to_json()


def _fig_lbp_usd(basket):
    lbp_m = monthly_basket_lbp(basket)
    usd_m = monthly_basket_usd(basket)

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=lbp_m["year_month"], y=lbp_m["price"], name="LBP price",
        line=dict(color=COLORS["crisis_red"], width=2.5),
        hovertemplate="<b>%{x}</b><br>LBP: %{y:,.0f}<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=usd_m["year_month"], y=usd_m["usdprice"], name="USD price",
        line=dict(color=COLORS["steel_blue"], width=2.5, dash="dot"),
        hovertemplate="<b>%{x}</b><br>USD: $%{y:.2f}<extra></extra>",
    ), secondary_y=True)

    for date_str, label, color_key, dash in EVENTS:
        ym = pd.Timestamp(date_str).strftime("%Y-%m")
        fig.add_shape(type="line", x0=ym, x1=ym, y0=0, y1=1,
                      xref="x", yref="paper",
                      line=dict(color=COLORS[color_key], width=1.5,
                                dash="dash" if dash == "dash" else "solid"))
        fig.add_annotation(x=ym, y=1, xref="x", yref="paper", text=label,
                           showarrow=False, xanchor="left", yanchor="top",
                           font=dict(size=10, color=COLORS[color_key], family="DM Sans, sans-serif"),
                           bgcolor="rgba(255,255,255,0.7)")

    fig.update_yaxes(title_text="Average LBP price", secondary_y=False,
                     tickformat=",", gridcolor="#EEF1F5")
    fig.update_yaxes(title_text="Average USD price", secondary_y=True,
                     tickprefix="$", showgrid=False)
    fig.update_xaxes(tickangle=-45, nticks=16, showgrid=False)
    fig.update_layout(**_BASE, height=420, margin=dict(l=60, r=60, t=44, b=60),
                      hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig.to_json()


def _fig_scatter(basket, exrate):
    r, r2 = rate_vs_basket_r_squared(basket, exrate)
    usd_m  = monthly_basket_usd(basket)
    rate_m = monthly_unofficial_rate(exrate)
    sdf    = pd.merge(usd_m, rate_m, on="year_month", suffixes=("_basket", "_rate")).dropna()

    fig = px.scatter(
        sdf, x="price", y="usdprice",
        trendline="ols",
        labels={"price": "Unofficial LBP/USD rate", "usdprice": "Avg basket price (USD)"},
        color_discrete_sequence=[COLORS["steel_blue"]],
        hover_data={"year_month": True, "price": ":.0f", "usdprice": ":.2f"},
    )
    fig.update_traces(selector=dict(mode="markers"),
                      marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color="white")))
    fig.update_traces(selector=dict(mode="lines"),
                      line=dict(color=COLORS["crisis_red"], width=2))
    fig.add_annotation(xref="paper", yref="paper", x=0.05, y=0.95,
                       text="<b>R² = {:.3f}</b>  (r = {:.3f})".format(r2, r),
                       showarrow=False,
                       font=dict(size=14, color=COLORS["deep_navy"], family="DM Sans, sans-serif"),
                       bgcolor="white", bordercolor=COLORS["deep_navy"], borderwidth=1, borderpad=8)
    fig.update_layout(**_BASE, height=420, margin=dict(l=60, r=24, t=40, b=60),
                      xaxis=dict(tickformat=",", gridcolor="#EEF1F5", showgrid=True),
                      yaxis=dict(tickprefix="$", gridcolor="#EEF1F5"))
    return fig.to_json(), r, r2, len(sdf)


# IPC mappings
_IPC_TO_GOV = {
    "Akkar": "Akkar", "Baalbek-El Hermel": "Baalbek-El Hermel",
    "Baalbek": "Baalbek-El Hermel", "El hermel": "Baalbek-El Hermel",
    "Zahie": "Baalbek-El Hermel", "Beirut": "Beirut",
    "Bekaa": "Bekaa", "Rachaya": "Bekaa", "North": "North",
    "El koura": "North", "El batroun": "North", "Bcharre": "North",
    "Zgharta": "North", "South": "South", "El Nabatieh": "El Nabatieh",
    "Bent jbell": "El Nabatieh", "Hasbaya": "El Nabatieh",
    "Jezzine": "El Nabatieh", "Marjaayoun": "El Nabatieh",
    "Mount Lebanon": "Mount Lebanon", "Jbell": "Mount Lebanon",
}

_PHASE_COLS = {
    "Phase 1": ("Phase 1 percentage current", COLORS["ipc_phase_1"]),
    "Phase 2": ("Phase 2 percentage current", COLORS["ipc_phase_2"]),
    "Phase 3": ("Phase 3 percentage current", COLORS["ipc_phase_3"]),
    "Phase 4": ("Phase 4 percentage current", COLORS["ipc_phase_4"]),
    "Phase 5": ("Phase 5 percentage current", COLORS["ipc_phase_5"]),
}


def _fig_choropleth(geo_snap):
    with open(GEOJSON_PATH) as f:
        geojson = json.load(f)

    choro_df = (
        geo_snap.dropna(subset=["gov"])
        .groupby("gov", as_index=False)
        .agg(phase3_pct=("Phase 3+ percentage current", "mean"))
    )
    choro_df["phase3_pct_display"] = (choro_df["phase3_pct"] * 100).round(1)

    ml_row = choro_df[choro_df["gov"] == "Mount Lebanon"]
    if not ml_row.empty:
        kj = ml_row.copy()
        kj["gov"] = "Keserwan-Jbeil"
        choro_df = pd.concat([choro_df, kj], ignore_index=True)

    fig = px.choropleth_map(
        choro_df, geojson=geojson,
        locations="gov", featureidkey="properties.shapeName",
        color="phase3_pct_display",
        color_continuous_scale=[
            [0,   "#C8E6C9"],
            [0.3, COLORS["ipc_phase_3"]],
            [0.6, COLORS["ipc_phase_4"]],
            [1,   COLORS["ipc_phase_5"]],
        ],
        range_color=(0, 60),
        map_style="carto-positron",
        center={"lat": 33.85, "lon": 35.86},
        zoom=7,
        opacity=0.75,
        labels={"phase3_pct_display": "Phase 3+ (%)"},
        hover_name="gov",
        hover_data={"gov": False, "phase3_pct_display": True},
    )
    fig.update_layout(**_BASE, height=440, margin=dict(l=0, r=0, t=0, b=0),
                      coloraxis_colorbar=dict(title="Phase 3+%", ticksuffix="%", len=0.7))
    return fig.to_json()


def _fig_donut(ipc_pop):
    pop_latest = (
        ipc_pop.dropna(subset=["Phase 3+ number current"])
        .sort_values("analysis_date")
        .groupby("Level 1", as_index=False)
        .last()
    )
    ordered = [g for g in POPULATION_GROUPS if g in pop_latest["Level 1"].values]
    pop_latest["Level 1"] = pd.Categorical(pop_latest["Level 1"], categories=ordered, ordered=True)
    pop_latest = pop_latest.sort_values("Level 1")
    colors = [PALETTE[i] for i, g in enumerate(POPULATION_GROUPS) if g in pop_latest["Level 1"].values]

    fig = px.pie(pop_latest, names="Level 1", values="Phase 3+ number current",
                 hole=0.5, color_discrete_sequence=colors)
    fig.update_traces(
        customdata=pd.to_datetime(pop_latest["analysis_date"]).dt.strftime("%b %Y"),
        textposition="outside", textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} people<br>%{percent}<br>Survey: %{customdata}<extra></extra>",
    )
    total = pop_latest["Phase 3+ number current"].sum()
    fig.update_layout(
        **_BASE, height=420, margin=dict(l=20, r=20, t=20, b=20),
        showlegend=False,
        annotations=[dict(
            text="<b>{:.2f}M</b><br>people".format(total / 1e6),
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color=COLORS["deep_navy"], family="DM Sans, sans-serif"),
        )],
    )
    return fig.to_json()


def _fig_ipc_bar(geo_snap):
    bar_df = (
        geo_snap.dropna(subset=["gov"])
        .groupby("gov", as_index=False)
        .agg({col: "mean" for col, _ in _PHASE_COLS.values()})
    )
    bar_df["phase3plus"] = bar_df[[
        "Phase 3 percentage current",
        "Phase 4 percentage current",
        "Phase 5 percentage current",
    ]].sum(axis=1)
    bar_df = bar_df.sort_values("phase3plus", ascending=False)

    fig = go.Figure()
    for phase_name, (col, color) in _PHASE_COLS.items():
        fig.add_trace(go.Bar(
            name=phase_name, x=bar_df["gov"],
            y=(bar_df[col] * 100).round(1),
            marker_color=color, marker_line_width=0,
            hovertemplate="<b>%{x}</b><br>" + phase_name + ": %{y:.1f}%<extra></extra>",
        ))
    fig.update_layout(
        **_BASE, barmode="stack", height=380,
        margin=dict(l=40, r=20, t=44, b=80),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        yaxis=dict(title="% of population", ticksuffix="%", gridcolor="#EEF1F5", range=[0, 100]),
        xaxis=dict(tickangle=-30, showgrid=False),
        hovermode="x unified",
    )
    return fig.to_json()


def _fig_gov_bar(prices, selected_year):
    yr_prices = prices[
        prices["commodity"].isin(BASKET) & (prices["date"].dt.year == selected_year)
    ]
    if yr_prices.empty:
        fig = go.Figure()
        fig.add_annotation(text="No WFP basket data for " + str(selected_year),
                           xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(**_BASE, height=340)
        return fig.to_json()

    gov_price = (
        yr_prices.groupby("admin1", as_index=False)["usdprice"]
        .mean()
        .sort_values("usdprice", ascending=True)
    )
    fig = go.Figure(go.Bar(
        x=gov_price["usdprice"], y=gov_price["admin1"],
        orientation="h", marker_color=PALETTE[3],
        hovertemplate="<b>%{y}</b><br>Avg USD: $%{x:.2f}<extra></extra>",
    ))
    fig.update_layout(
        **_BASE, height=340, margin=dict(l=20, r=40, t=44, b=40),
        xaxis=dict(title="Avg basket price (USD)", tickprefix="$",
                   gridcolor="#EEF1F5", showgrid=True),
        yaxis=dict(showgrid=False),
    )
    return fig.to_json()


# Health constants
_MULTI_CODES = {
    "Stunting prevalence (%)":       "NUTSTUNTINGPREV",
    "Anaemia in children (%)":       "NUTRITION_ANAEMIA_CHILDREN_PREV",
    "Infant mortality (per 1,000)":  "MDG_0000000001",
    "Under-5 mortality (per 1,000)": "MDG_0000000007",
}
_MULTI_COLORS = ["#ff595e", "#ffca3a", "#1982c4", "#6a4c93"]

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

_MENA_PEERS = ["Lebanon", "Saudi Arabia", "Jordan", "Syrian Arab Republic", "Egypt", "World"]
_MENA_COLORS = {
    "Lebanon": "#ff595e", "Saudi Arabia": "#1982c4", "Jordan": "#46dff7",
    "Syrian Arab Republic": "#ffca3a", "Egypt": "#6a4c93", "World": "#af848c",
}


def _btsx(health):
    return health[
        health["DIMENSION (CODE)"].isin(["SEX_BTSX", "HOUSEHOLDWEALTH_TOTL"]) &
        (health["YEAR (DISPLAY)"] >= 2000)
    ].copy()


def _fig_lag(basket, health):
    h = _btsx(health)
    basket_idx = basket_price_index(basket)
    basket_idx["year"] = basket_idx["year_month"].str[:4].astype(int)
    basket_annual = basket_idx.groupby("year", as_index=False)["price_index"].mean()
    basket_annual = basket_annual[basket_annual["year"] >= 2000]

    stunt = (
        h[h["GHO (CODE)"] == "NUTSTUNTINGPREV"]
        [["YEAR (DISPLAY)", "Numeric"]].dropna().sort_values("YEAR (DISPLAY)")
    )
    yr_min = max(int(basket_annual["year"].min()), int(stunt["YEAR (DISPLAY)"].min()))
    yr_max = min(int(basket_annual["year"].max()), int(stunt["YEAR (DISPLAY)"].max()))
    basket_annual = basket_annual[
        (basket_annual["year"] >= yr_min) & (basket_annual["year"] <= yr_max)
    ]
    stunt = stunt[
        (stunt["YEAR (DISPLAY)"] >= yr_min) & (stunt["YEAR (DISPLAY)"] <= yr_max)
    ]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=("Basket Price Index (2019=100)", "Stunting Prevalence (%)"))
    fig.add_trace(go.Scatter(
        x=basket_annual["year"], y=basket_annual["price_index"],
        name="Price Index", line=dict(color="#ff595e", width=2.5),
        fill="tozeroy", fillcolor="rgba(255,89,94,0.08)",
        hovertemplate="<b>%{x}</b><br>Price Index: %{y:.0f}<extra></extra>",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=stunt["YEAR (DISPLAY)"], y=stunt["Numeric"],
        name="Stunting %", line=dict(color="#6a4c93", width=2.5),
        mode="lines+markers", marker=dict(size=6, color="#6a4c93"),
        hovertemplate="<b>%{x}</b><br>Stunting: %{y:.1f}%<extra></extra>",
    ), row=2, col=1)

    for r in [1, 2]:
        fig.add_vrect(x0=2020, x1=2022, fillcolor=COLORS["warning"], opacity=0.08,
                      line_width=0, row=r, col=1)
        for yr in [2020, 2022]:
            fig.add_vline(x=yr, line_dash="dash", line_color=COLORS["warning"],
                          line_width=1, opacity=0.6, row=r, col=1)

    fig.add_annotation(x=2021, y=1, xref="x", yref="paper",
                       text="Crisis window<br>2020-2022", showarrow=False,
                       font=dict(size=10, color=COLORS["warning"], family="DM Sans, sans-serif"),
                       bgcolor="rgba(255,255,255,0.8)")
    fig.update_yaxes(title_text="Price Index", row=1, col=1, gridcolor="#EEF1F5")
    fig.update_yaxes(title_text="Stunting (%)", row=2, col=1, ticksuffix="%", gridcolor="#EEF1F5")
    fig.update_xaxes(title_text="Year", row=2, col=1, dtick=2, showgrid=False)
    fig.update_xaxes(showgrid=False, row=1, col=1)
    fig.update_layout(**_BASE, height=520, margin=dict(l=60, r=24, t=48, b=48),
                      showlegend=False, hovermode="x unified")
    return fig.to_json()


def _fig_small_mult(health):
    h = _btsx(health)
    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=list(_MULTI_CODES.keys()),
                        vertical_spacing=0.14, horizontal_spacing=0.1)
    for (title, code), (row, col), color in zip(
        _MULTI_CODES.items(), [(1, 1), (1, 2), (2, 1), (2, 2)], _MULTI_COLORS
    ):
        df_m = (
            h[h["GHO (CODE)"] == code][["YEAR (DISPLAY)", "Numeric"]]
            .dropna().sort_values("YEAR (DISPLAY)")
        )
        if df_m.empty:
            continue
        fig.add_trace(go.Scatter(
            x=df_m["YEAR (DISPLAY)"], y=df_m["Numeric"],
            mode="lines+markers", line=dict(color=color, width=2),
            marker=dict(size=4), showlegend=False,
            hovertemplate="<b>%{x}</b><br>%{y:.2f}<extra></extra>",
        ), row=row, col=col)
        yr_min_m = int(df_m["YEAR (DISPLAY)"].min())
        yr_max_m = int(df_m["YEAR (DISPLAY)"].max())
        if yr_min_m <= 2020 <= yr_max_m:
            fig.add_vrect(x0=2020, x1=min(2022, yr_max_m),
                          fillcolor=COLORS["warning"], opacity=0.07, line_width=0,
                          row=row, col=col)
    fig.update_xaxes(dtick=5, showgrid=False)
    fig.update_yaxes(gridcolor="#EEF1F5")
    fig.update_layout(**_BASE, height=520, margin=dict(l=40, r=20, t=56, b=40))
    return fig.to_json()


def _fig_dumbbell(health):
    h = _btsx(health)
    rows = []
    for short, code in _DB_CODES.items():
        dfc = (
            h[h["GHO (CODE)"] == code][["YEAR (DISPLAY)", "Numeric"]]
            .dropna().sort_values("YEAR (DISPLAY)")
        )
        if len(dfc) < 2:
            continue
        pre = dfc[dfc["YEAR (DISPLAY)"] <= 2019]
        if pre.empty:
            continue
        base   = pre.iloc[-1]
        latest = dfc.iloc[-1]
        if int(base["YEAR (DISPLAY)"]) == int(latest["YEAR (DISPLAY)"]):
            continue
        pct = float((latest["Numeric"] - base["Numeric"]) / base["Numeric"] * 100)
        rows.append(dict(
            indicator=short,
            val_base=float(base["Numeric"]),
            yr_base=int(base["YEAR (DISPLAY)"]),
            val_latest=float(latest["Numeric"]),
            yr_latest=int(latest["YEAR (DISPLAY)"]),
            pct=pct,
            improved=pct < 0,
        ))

    rows.sort(key=lambda r: r["pct"], reverse=True)
    if not rows:
        fig = go.Figure()
        fig.update_layout(**_BASE, height=360)
        return fig.to_json()

    names = [r["indicator"] for r in rows]
    fig = go.Figure()
    for r in rows:
        lc = "#8ac926" if r["improved"] else "#ff595e"
        fig.add_shape(type="line", x0=0, x1=r["pct"],
                      y0=r["indicator"], y1=r["indicator"],
                      line=dict(color=lc, width=3))
    fig.add_trace(go.Scatter(
        x=[0] * len(rows), y=names, mode="markers",
        marker=dict(color="#BBBBBB", size=13, line=dict(color="white", width=2)),
        name="2019 (baseline)",
        customdata=[[r["val_base"]] for r in rows],
        hovertemplate="<b>%{y}</b><br>2019: %{customdata[0]:.1f}<extra></extra>",
    ))
    imp  = [r for r in rows if r["improved"]]
    wors = [r for r in rows if not r["improved"]]
    if imp:
        fig.add_trace(go.Scatter(
            x=[r["pct"] for r in imp], y=[r["indicator"] for r in imp],
            mode="markers", marker=dict(color="#8ac926", size=13, line=dict(color="white", width=2)),
            name="Improved",
            customdata=[[r["yr_latest"], r["val_latest"], r["pct"]] for r in imp],
            hovertemplate="<b>%{y}</b><br>%{customdata[0]}: %{customdata[1]:.1f}<br>Change: %{customdata[2]:+.1f}%<extra></extra>",
        ))
    if wors:
        fig.add_trace(go.Scatter(
            x=[r["pct"] for r in wors], y=[r["indicator"] for r in wors],
            mode="markers", marker=dict(color="#ff595e", size=13, line=dict(color="white", width=2)),
            name="Worsened",
            customdata=[[r["yr_latest"], r["val_latest"], r["pct"]] for r in wors],
            hovertemplate="<b>%{y}</b><br>%{customdata[0]}: %{customdata[1]:.1f}<br>Change: %{customdata[2]:+.1f}%<extra></extra>",
        ))
    for r in rows:
        lc = "#8ac926" if r["improved"] else "#ff595e"
        fig.add_annotation(
            x=r["pct"], y=r["indicator"],
            text="{:+.0f}%".format(r["pct"]),
            showarrow=False,
            font=dict(size=10, color=lc, family="DM Sans, sans-serif"),
            xshift=16 if r["pct"] >= 0 else -16,
            xanchor="left" if r["pct"] >= 0 else "right",
        )
    fig.add_vline(x=0, line_color="#AAAAAA", line_width=1.5,
                  annotation_text="2019", annotation_position="top",
                  annotation_font_size=11, annotation_font_color="#888888")
    _db_layout = {**_BASE, "plot_bgcolor": "#FAFAFA"}
    fig.update_layout(
        **_db_layout, height=max(360, len(rows) * 52),
        margin=dict(l=20, r=80, t=24, b=40),
        xaxis=dict(title="Percentage Change Since 2019 (%)",
                   gridcolor="#EEF1F5", ticksuffix="%", showgrid=True, zeroline=False),
        yaxis=dict(showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="y",
    )
    return fig.to_json()


def _fig_mena(u5mort):
    u5f = u5mort[u5mort["country"].isin(_MENA_PEERS)].sort_values(["country", "year"])
    fig = go.Figure()
    for country in _MENA_PEERS:
        cdf = u5f[u5f["country"] == country]
        if cdf.empty:
            continue
        is_lbn   = country == "Lebanon"
        is_world = country == "World"
        fig.add_trace(go.Scatter(
            x=cdf["year"], y=cdf["rate"], name=country,
            mode="lines+markers",
            line=dict(
                color=_MENA_COLORS.get(country, "#888"),
                width=3 if is_lbn else 2,
                dash="dash" if is_world else "solid",
            ),
            marker=dict(size=5 if is_lbn else 4),
            hovertemplate="<b>" + country + "</b><br>%{x}: %{y:.1f} per 1,000<extra></extra>",
        ))
    for yr, lbl, y_paper, anchor in [
        (2019, "Banking crisis",  0.97, "right"),
        (2020, "Port explosion",  0.58, "left"),
        (2021, "Subsidy removal", 0.97, "left"),
    ]:
        fig.add_vline(x=yr, line_dash="dash", line_color=COLORS["warning"], line_width=1.5)
        fig.add_annotation(x=yr, y=y_paper, xref="x", yref="paper",
                           text=lbl, showarrow=False,
                           font=dict(size=10, color=COLORS["warning"], family="DM Sans, sans-serif"),
                           xanchor=anchor, yanchor="top",
                           bgcolor="rgba(255,255,255,0.75)")
    fig.update_layout(
        **_BASE, height=440, margin=dict(l=60, r=80, t=24, b=48),
        xaxis=dict(title="Year", dtick=2, showgrid=False),
        yaxis=dict(title="Under-5 mortality (per 1,000 live births)", gridcolor="#EEF1F5"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
    )
    return fig.to_json()


# =============================================================================
# Section renderers
# =============================================================================

def _section_landing(d):
    wdi     = d["wdi"]
    ipc_pop = d["ipc_pop"]
    exrate  = d["exrate"]

    peak_inf = lebanon_peak_inflation(wdi)
    gdp_drop = gdp_contraction(wdi, 2018, 2023)
    phase3   = lebanese_phase3_plus(ipc_pop)
    lbp_rate = latest_unofficial_rate(exrate)

    latest_ipc = ipc_pop["analysis_date"].max().strftime("%b %Y")
    latest_fx  = exrate.loc[exrate["date"].idxmax(), "date"].strftime("%b %Y")

    tl_json = _fig_timeline()

    kpi_defs = [
        ("{:.1f}%".format(peak_inf),  "Peak Annual Inflation",
         "Lebanon consumer prices, peak year", PALETTE[0]),
        ("{:.0%}".format(gdp_drop),   "GDP Contraction 2018-2023",
         "Share of GDP lost in five years", PALETTE[0]),
        ("{:.0%}".format(phase3),     "Lebanese in IPC Phase 3+",
         "Lebanese residents · " + latest_ipc + " snapshot", PALETTE[1]),
        ("{:,.0f}".format(lbp_rate),  "LBP per USD (Unofficial)",
         "Parallel market rate · " + latest_fx, PALETTE[3]),
    ]

    kpi_html = ""
    for val, label, sub, accent in kpi_defs:
        kpi_html += (
            '<div class="kpi-card" style="border-top-color:' + accent + '">'
            '<div class="kpi-label">' + label + '</div>'
            '<div class="kpi-value">' + val + '</div>'
            '<div class="kpi-sub">' + sub + '</div>'
            '</div>'
        )

    return (
        '<div id="s-landing" class="hero">'
        '<div class="hero-kicker">Data Visualization &nbsp;&middot;&nbsp; Spring 2026'
        ' &nbsp;&middot;&nbsp; Reem Marji &amp; Karim Hallal</div>'
        '<h1>Lebanon<br>in <span>Crisis</span></h1>'
        '<p class="hero-sub">'
        'A decade of economic collapse, food insecurity, and deteriorating health outcomes &mdash;'
        ' from the 2019 banking crisis to the Beirut port explosion and subsidy removal.'
        ' Tracking the full humanitarian arc from 2012 to 2026.'
        '</p>'
        '<div class="kpi-row">' + kpi_html + '</div>'
        '<div class="timeline-wrap">' + _plot_tag("timeline", tl_json) + '</div>'
        '</div>'
        '<p style="background:var(--navy);color:rgba(255,255,255,0.2);font-size:10px;'
        'text-align:right;padding:8px 60px 28px;letter-spacing:0.05em">'
        'Sources: WFP VAM &nbsp;&middot;&nbsp; World Bank WDI &nbsp;&middot;&nbsp;'
        ' IPC Global Platform &nbsp;&middot;&nbsp; WHO GHO'
        '</p>'
    )


def _section_macro(d):
    wdi = d["wdi"]
    gdp_json = _fig_gdp_rate(wdi)
    inf_json = _fig_inflation(wdi)
    tbl_html = _html_gdp_table(wdi)

    return (
        '<section id="s-macro">'
        '<div class="section-meta">'
        '<span class="section-tag">Act 1</span>'
        '<span class="section-eyebrow">2011 &ndash; 2024</span>'
        '</div>'
        '<h2 class="section-title">The Macro Shock</h2>'
        '<p class="section-sub">GDP collapsed by over 60%, inflation peaked above 200%, '
        'and the official exchange rate diverged sharply from the black market. '
        "Lebanon's trajectory compared against five regional peers.</p>"
        '<div class="chart-card">'
        '<div class="chart-title">GDP &amp; Official Exchange Rate &mdash; Lebanon</div>'
        '<div class="chart-caption">Left axis: GDP in USD billions &middot; '
        'Right axis: Official LBP per USD (World Bank)</div>'
        + _plot_tag("gdp_rate", gdp_json) +
        '</div>'
        '<div class="chart-card">'
        '<div class="chart-title">Annual Inflation &mdash; Regional Comparison</div>'
        '<div class="chart-caption">Consumer price inflation (% annual). '
        "Lebanon's 2020&ndash;2023 surge dwarfs all regional peers. Syria data ends 2019.</div>"
        + _plot_tag("inflation", inf_json) +
        '</div>'
        '<div class="chart-card">'
        '<div class="chart-title">GDP per Capita (USD) &mdash; Country &times; Year</div>'
        '<div class="chart-caption">Source: World Bank WDI &middot; NY.GDP.PCAP.CD '
        '&middot; Lebanon row highlighted.</div>'
        + tbl_html +
        '</div>'
        '<p class="source-line">Sources: World Bank WDI &middot; FP.CPI.TOTL.ZG '
        '&middot; NY.GDP.MKTP.CD &middot; PA.NUS.FCRF &middot; NY.GDP.PCAP.CD</p>'
        '</section>'
    )


def _section_food(d):
    prices = d["prices"]
    basket = d["basket"]
    exrate = d["exrate"]

    idx_json             = _fig_price_index(prices)
    lbp_usd_json         = _fig_lbp_usd(basket)
    scat_json, r, r2, n  = _fig_scatter(basket, exrate)

    callout = (
        '<div class="callout">'
        '<div class="callout-stat">{:.2f}</div>'.format(r2) +
        '<div class="callout-stat-label">R² &mdash; Correlation strength</div>'
        '<p class="callout-body">'
        'Each dot represents one month of market data. '
        'An R² of <strong>{:.2f}</strong> means the unofficial LBP/USD exchange rate '.format(r2) +
        'explains <strong>{:.0f}%</strong> of the variance in USD basket prices &mdash; '.format(r2 * 100) +
        'confirming that the currency collapse, not just LBP inflation, '
        'drove real purchasing-power loss for Lebanese households.'
        '<br><br>Computed from <strong>{} monthly observations</strong>'.format(n) +
        ' (Pearson r = {:.3f}) over the overlapping date range.'.format(r) +
        '</p></div>'
    )

    return (
        '<section id="s-food">'
        '<div class="section-meta">'
        '<span class="section-tag">Act 2</span>'
        '<span class="section-eyebrow">2012 &ndash; 2026</span>'
        '</div>'
        '<h2 class="section-title">Food Price Transmission</h2>'
        '<p class="section-sub">How Lebanon\'s currency collapse drove staple food prices '
        'beyond reach &mdash; tracked through WFP market data across six basket commodities.</p>'
        '<div class="chart-card">'
        '<div class="chart-title">Commodity Price Index (2019 = 100)</div>'
        '<div class="chart-caption">Monthly average price index per basket commodity. '
        'Dotted line marks the 2019 baseline. Click the legend to isolate individual commodities.</div>'
        + _plot_tag("price_index", idx_json) +
        '</div>'
        '<div class="chart-card">'
        '<div class="chart-title">Basket Price &mdash; LBP vs USD</div>'
        '<div class="chart-caption">Monthly average price of the six-item food basket. '
        'LBP price (left axis) exploded while USD price (right axis) also rose, '
        'showing real purchasing-power loss beyond currency devaluation.</div>'
        + _plot_tag("lbp_usd", lbp_usd_json) +
        '</div>'
        '<div class="g55">'
        '<div class="chart-card" style="margin-bottom:0">'
        '<div class="chart-title">Exchange Rate vs Basket USD Price</div>'
        '<div class="chart-caption">Each dot is one month. '
        'X = unofficial LBP/USD &middot; Y = average basket price in USD.</div>'
        + _plot_tag("scatter", scat_json) +
        '</div>'
        + callout +
        '</div>'
        '<p class="source-line">Sources: WFP VAM Food Price Monitoring '
        '&middot; Unofficial exchange rate from WFP parallel market data</p>'
        '</section>'
    )


def _section_insecurity(d):
    geo     = d["ipc_geo"].copy()
    ipc_pop = d["ipc_pop"]
    prices  = d["prices"]

    geo["gov"] = geo["admin1_normalized"].map(_IPC_TO_GOV)

    latest_date   = geo["analysis_date"].max()
    geo_snap      = geo[geo["analysis_date"] == latest_date].copy()
    snap_label    = latest_date.strftime("%B %Y")
    selected_year = latest_date.year

    choro_json   = _fig_choropleth(geo_snap)
    donut_json   = _fig_donut(ipc_pop)
    ipc_bar_json = _fig_ipc_bar(geo_snap)
    gov_bar_json = _fig_gov_bar(prices, selected_year)

    return (
        '<section id="s-insecurity">'
        '<div class="section-meta">'
        '<span class="section-tag">Act 2 Extended</span>'
        '<span class="section-eyebrow">Snapshot: ' + snap_label + '</span>'
        '</div>'
        '<h2 class="section-title">Who Suffers Most</h2>'
        '<p class="section-sub">IPC food insecurity phases broken down by governorate '
        'and population group. Data shown for the most recent available snapshot '
        '(' + snap_label + ').</p>'
        '<div class="g60">'
        '<div class="chart-card" style="margin-bottom:0">'
        '<div class="chart-title">IPC Phase 3+ by Governorate</div>'
        '<div class="chart-caption">Share of population in acute food insecurity '
        '(Phase 3 or above). Darker = more severe.</div>'
        + _plot_tag("choropleth", choro_json) +
        '</div>'
        '<div class="chart-card" style="margin-bottom:0">'
        '<div class="chart-title">Phase 3+ by Population Group</div>'
        '<div class="chart-caption">Each group at its most recent available survey date. '
        'Hover for exact figures.</div>'
        + _plot_tag("donut", donut_json) +
        '</div>'
        '</div>'
        '<div style="margin-bottom:22px"></div>'
        '<div class="g65">'
        '<div class="chart-card" style="margin-bottom:0">'
        '<div class="chart-title">IPC Phase Distribution by Governorate</div>'
        '<div class="chart-caption">Stacked bars &mdash; % of analysed population '
        'in each IPC phase. Sorted by Phase 3+ share.</div>'
        + _plot_tag("ipc_bar", ipc_bar_json) +
        '</div>'
        '<div class="chart-card" style="margin-bottom:0">'
        '<div class="chart-title">Avg Basket Price by Governorate &mdash; '
        + str(selected_year) + '</div>'
        '<div class="chart-caption">Average USD price of basket commodities per governorate, '
        + str(selected_year) + '.</div>'
        + _plot_tag("gov_bar", gov_bar_json) +
        '</div>'
        '</div>'
        '<p class="source-line">Sources: IPC Global Platform '
        '&middot; WFP VAM Food Price Monitoring</p>'
        '</section>'
    )


def _section_health(d):
    health = d["health"]
    basket = d["basket"]
    u5mort = d["u5mort"]

    lag_json   = _fig_lag(basket, health)
    multi_json = _fig_small_mult(health)
    db_json    = _fig_dumbbell(health)
    mena_json  = _fig_mena(u5mort)

    return (
        '<section id="s-health">'
        '<div class="section-meta">'
        '<span class="section-tag">Act 3</span>'
        '<span class="section-eyebrow">2000 &ndash; 2024</span>'
        '</div>'
        '<h2 class="section-title">The Health Toll</h2>'
        '<p class="section-sub">Stunting, wasting, anaemia, and mortality in Lebanon &mdash; '
        'with a lagged view against food price shocks. The crisis is still unfolding: '
        'nutrition indicators worsen years after the price shock.</p>'
        '<div class="chart-card">'
        '<div class="chart-title">Food Prices vs Stunting Prevalence &mdash; Lag View</div>'
        '<div class="chart-caption">Top: Monthly basket price index (2019=100) &middot; '
        'Bottom: Annual stunting prevalence %. '
        'Shaded band highlights the 2020&ndash;2022 crisis window.</div>'
        + _plot_tag("lag", lag_json) +
        '</div>'
        '<div class="chart-card">'
        '<div class="chart-title">Key Nutrition &amp; Mortality Trends</div>'
        '<div class="chart-caption">Model-based estimates &middot; Both sexes &middot; '
        'Lebanon (LBN) &middot; Data from 2000. Shaded region: 2020&ndash;2022 crisis window.</div>'
        + _plot_tag("small_mult", multi_json) +
        '</div>'
        '<div class="chart-card">'
        '<div class="chart-title">Lebanon Child Health: Before &amp; After the Economic Collapse</div>'
        '<div class="chart-caption">Percentage change in key health indicators between 2019 '
        'and the latest available year. All indicators are &ldquo;lower is better&rdquo; &mdash; '
        'green = improved, red = worsened. Hover for exact values.</div>'
        + _plot_tag("dumbbell", db_json) +
        '</div>'
        '<div class="chart-card">'
        '<div class="chart-title">Regional Under-5 Mortality &mdash; MENA Comparison</div>'
        '<div class="chart-caption">Under-5 mortality rate (per 1,000 live births). '
        'Lebanon highlighted in red &middot; World average dashed &middot; '
        'Source: WHO &middot; 2000&ndash;2023.</div>'
        + _plot_tag("mena", mena_json) +
        '</div>'
        '<p class="source-line">Sources: WHO Global Health Observatory '
        '&middot; UN IGME (via WHO) &middot; Lebanon (LBN)</p>'
        '</section>'
    )


def _footer():
    return (
        '<footer style="background:var(--navy);color:rgba(255,255,255,0.4);'
        'padding:40px 60px;font-size:11px;line-height:1.9;letter-spacing:0.03em">'
        '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:40px;max-width:900px">'
        '<div>'
        '<div style="color:rgba(255,255,255,0.7);font-weight:600;text-transform:uppercase;'
        'letter-spacing:0.1em;font-size:10px;margin-bottom:12px">Data Sources</div>'
        'WFP VAM Food Price Monitoring<br>'
        'World Bank World Development Indicators<br>'
        'IPC Global Platform<br>'
        'WHO Global Health Observatory<br>'
        'UN IGME Child Mortality Estimates'
        '</div>'
        '<div>'
        '<div style="color:rgba(255,255,255,0.7);font-weight:600;text-transform:uppercase;'
        'letter-spacing:0.1em;font-size:10px;margin-bottom:12px">Project</div>'
        'Data Visualization Final Project<br>'
        'Spring 2026<br>'
        'Reem Marji &amp; Karim Hallal'
        '</div>'
        '<div>'
        '<div style="color:rgba(255,255,255,0.7);font-weight:600;text-transform:uppercase;'
        'letter-spacing:0.1em;font-size:10px;margin-bottom:12px">Coverage</div>'
        'Lebanon economic data: 2011&ndash;2024<br>'
        'WFP food prices: 2012&ndash;2026<br>'
        'IPC food security: 2022&ndash;2025<br>'
        'Health indicators: 2000&ndash;2023'
        '</div>'
        '</div>'
        '<div style="margin-top:32px;border-top:1px solid rgba(255,255,255,0.1);'
        'padding-top:20px;color:rgba(255,255,255,0.25)">'
        'Generated with Python + Plotly &middot; All data sourced from public international datasets'
        '</div>'
        '</footer>'
    )


# =============================================================================
# Assembly & entry point
# =============================================================================

def _build_body(d):
    return (
        _section_landing(d)
        + _section_macro(d)
        + _section_food(d)
        + _section_insecurity(d)
        + _section_health(d)
        + _footer()
    )


def write_report(output=None):
    if output is None:
        output = ROOT / "report.html"
    print("Loading data...")
    d = load_all()
    print("Building figures...")
    body = _build_body(d)
    print("Writing HTML...")
    html = build_html(body)
    output.write_text(html, encoding="utf-8")
    kb = output.stat().st_size / 1024
    print("Done: {}  ({:.0f} KB)".format(output, kb))


if __name__ == "__main__":
    write_report()
