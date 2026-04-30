"""Lebanon Crisis Dashboard — HTML Report Generator.
Run: python generate_report.py  →  writes report.html
"""

# ── Streamlit stub (must come before any src/ import) ────────────────────────
import sys
from types import ModuleType
_st = ModuleType("streamlit")
_st.cache_data = lambda f: f          # identity: no caching, no crash
sys.modules["streamlit"] = _st

# ── Standard library ─────────────────────────────────────────────────────────
import json
from pathlib import Path

# ── Third-party ──────────────────────────────────────────────────────────────
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import pearsonr

# ── Project ───────────────────────────────────────────────────────────────────
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

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT         = Path(__file__).parent
ASSETS       = ROOT / "assets"
GEOJSON_PATH = ASSETS / "geoBoundaries-LBN-ADM1_simplified.geojson"

# ── Global Plotly style ───────────────────────────────────────────────────────
_BASE = dict(
    font=dict(family="DM Sans, sans-serif", color="#1F3864", size=12),
    paper_bgcolor="#FFFFFF",
    plot_bgcolor="#FFFFFF",
)

def _style(fig, height=420, margin=None):
    """Apply project-wide Plotly cosmetics to any figure."""
    m = margin or dict(l=52, r=24, t=40, b=52)
    fig.update_layout(**_BASE, height=height, margin=m)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#EEF1F5")
    return fig

# ── Data loading ──────────────────────────────────────────────────────────────
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

# ── Figure/section builders — filled in Tasks 2–6 ────────────────────────────

# ── HTML primitives ───────────────────────────────────────────────────────────
CSS = """
:root{
  --navy:#1F3864;--red:#C00000;--blue:#2E74B5;
  --bg:#F4F6F9;--white:#FFFFFF;--card-bg:#EBF3FB;
  --muted:#6B7280;--border:#D5DCE8;
  --shadow:0 2px 10px rgba(31,56,100,0.08);
}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:'DM Sans',sans-serif;background:var(--bg);color:var(--navy)}

/* NAV */
nav{
  position:fixed;top:0;left:0;right:0;z-index:100;
  height:54px;background:var(--navy);
  display:flex;align-items:center;justify-content:space-between;
  padding:0 48px;box-shadow:0 1px 16px rgba(0,0,0,0.22);
}
.brand{
  font-family:'DM Serif Display',serif;font-size:17px;
  color:white;letter-spacing:-0.01em;white-space:nowrap;
}
nav ul{list-style:none;display:flex;gap:28px}
nav ul li a{
  font-size:11px;font-weight:600;letter-spacing:0.09em;
  text-transform:uppercase;color:rgba(255,255,255,0.55);
  text-decoration:none;
  padding-bottom:2px;border-bottom:2px solid transparent;
  transition:color .2s,border-color .2s;
}
nav ul li a:hover{color:white}
nav ul li a.active{color:white;border-bottom-color:var(--red)}

/* HERO */
#s-landing{
  background:var(--navy);
  padding:106px 60px 72px;
  color:white;
}
.hero-kicker{
  font-size:10px;font-weight:700;letter-spacing:0.2em;
  text-transform:uppercase;color:rgba(255,255,255,0.4);
  margin-bottom:18px;
}
.hero h1{
  font-family:'DM Serif Display',serif;
  font-size:62px;font-weight:400;line-height:1.04;
  letter-spacing:-0.025em;margin-bottom:20px;
}
.hero h1 span{color:#ff595e}
.hero-sub{
  font-size:16px;color:rgba(255,255,255,0.65);
  max-width:620px;line-height:1.75;margin-bottom:52px;
}
.kpi-row{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;margin-bottom:48px}
.kpi-card{
  background:rgba(255,255,255,0.07);
  border:1px solid rgba(255,255,255,0.1);
  border-top:3px solid;border-radius:8px;padding:22px 20px;
}
.kpi-label{
  font-size:9px;font-weight:700;letter-spacing:0.14em;
  text-transform:uppercase;color:rgba(255,255,255,0.45);margin-bottom:14px;
}
.kpi-value{
  font-size:42px;font-weight:700;line-height:1;
  letter-spacing:-0.02em;color:white;
}
.kpi-sub{font-size:11px;color:rgba(255,255,255,0.35);margin-top:8px;line-height:1.4}
.timeline-wrap{background:rgba(255,255,255,0.04);border-radius:8px;padding:16px 16px 4px}

/* SECTIONS */
section{padding:72px 60px}
section:nth-of-type(even){background:var(--white)}
section:nth-of-type(odd){background:var(--bg)}
.section-meta{display:flex;align-items:center;gap:14px;margin-bottom:10px}
.section-tag{
  font-size:10px;font-weight:700;letter-spacing:0.12em;
  text-transform:uppercase;color:var(--muted);
  border:1px solid var(--border);border-radius:20px;padding:3px 12px;
}
.section-eyebrow{font-size:10px;font-weight:600;color:var(--muted);letter-spacing:0.08em;text-transform:uppercase}
h2.section-title{
  font-family:'DM Serif Display',serif;
  font-size:36px;font-weight:400;color:var(--navy);
  letter-spacing:-0.01em;margin-bottom:8px;
}
.section-sub{
  font-size:14px;color:var(--muted);margin-bottom:44px;
  max-width:680px;line-height:1.65;
}

/* CHART CARDS */
.chart-card{
  background:white;border-radius:10px;
  box-shadow:var(--shadow);padding:22px 22px 12px;margin-bottom:22px;
}
.chart-title{font-size:13px;font-weight:600;color:var(--navy);margin-bottom:3px}
.chart-caption{font-size:11px;color:var(--muted);margin-bottom:14px;line-height:1.5}
.plot-container{width:100%}

/* GRID LAYOUTS */
.g2{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-bottom:22px}
.g55{display:grid;grid-template-columns:55fr 45fr;gap:22px;margin-bottom:22px}
.g60{display:grid;grid-template-columns:60fr 40fr;gap:22px;margin-bottom:22px}
.g65{display:grid;grid-template-columns:65fr 35fr;gap:22px;margin-bottom:22px}

/* CALLOUT CARD */
.callout{
  background:var(--card-bg);border-left:4px solid var(--blue);
  border-radius:0 10px 10px 0;padding:28px 24px;
  display:flex;flex-direction:column;justify-content:center;
}
.callout-stat{
  font-size:54px;font-weight:700;color:var(--navy);
  letter-spacing:-0.03em;line-height:1;
}
.callout-stat-label{
  font-size:10px;font-weight:700;letter-spacing:0.12em;
  text-transform:uppercase;color:var(--muted);margin-top:8px;margin-bottom:18px;
}
.callout-body{font-size:13px;color:#374151;line-height:1.7}

/* DATA TABLE */
.tbl-wrap{overflow-x:auto}
table.data-tbl{width:100%;border-collapse:collapse;font-size:12px}
table.data-tbl th{
  background:var(--navy);color:white;padding:9px 12px;
  font-weight:600;text-align:right;font-size:10px;letter-spacing:0.05em;
  text-transform:uppercase;white-space:nowrap;
}
table.data-tbl th:first-child{text-align:left}
table.data-tbl td{
  padding:7px 12px;text-align:right;
  border-bottom:1px solid var(--border);
}
table.data-tbl td:first-child{text-align:left;font-weight:500}
table.data-tbl tr.lbn td{background:var(--card-bg);color:var(--red);font-weight:700}

/* SOURCE LINE */
.source-line{
  font-size:10px;color:var(--muted);margin-top:36px;
  padding-top:16px;border-top:1px solid var(--border);
}

/* SCROLLBAR */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
"""

NAV_HTML = """
<nav>
  <span class="brand">Lebanon in Crisis</span>
  <ul>
    <li><a href="#s-landing">Overview</a></li>
    <li><a href="#s-macro">Macro Shock</a></li>
    <li><a href="#s-food">Food Prices</a></li>
    <li><a href="#s-insecurity">Food Insecurity</a></li>
    <li><a href="#s-health">Health Toll</a></li>
  </ul>
</nav>
"""

NAV_JS = """
(function(){
  const sections = document.querySelectorAll('#s-landing,section[id]');
  const links    = document.querySelectorAll('nav ul li a');
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if(e.isIntersecting){
        links.forEach(l => l.classList.remove('active'));
        const a = document.querySelector('nav ul li a[href="#'+e.target.id+'"]');
        if(a) a.classList.add('active');
      }
    });
  },{threshold:0.25});
  sections.forEach(s => obs.observe(s));
})();
"""

PLOTLY_RENDER_JS = """
(function(){
  const cfg={responsive:true,displayModeBar:true,displaylogo:false,
             modeBarButtonsToRemove:['lasso2d','select2d','toImage']};
  document.querySelectorAll('script[type="application/json"][data-plot]').forEach(el=>{
    const fig=JSON.parse(el.textContent);
    const div=document.getElementById(el.dataset.plot);
    if(div) Plotly.newPlot(div,fig.data,fig.layout,cfg);
  });
})();
"""

def _plot_tag(fig_id: str, fig_json: str) -> str:
    return (
        f'<script type="application/json" data-plot="plot-{fig_id}">{fig_json}</script>\n'
        f'<div id="plot-{fig_id}" class="plot-container"></div>'
    )

def build_html(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Lebanon in Crisis — Data Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&display=swap" rel="stylesheet"/>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>{CSS}</style>
</head>
<body>
{NAV_HTML}
{body}
<script>{NAV_JS}</script>
<script>{PLOTLY_RENDER_JS}</script>
</body>
</html>"""


# ── Section stubs (replaced task by task) ────────────────────────────────────
def _section_landing(d): return "<!-- landing -->"
def _section_macro(d):   return "<!-- macro -->"
def _section_food(d):    return "<!-- food -->"
def _section_insecurity(d): return "<!-- insecurity -->"
def _section_health(d):  return "<!-- health -->"
def _footer():           return ""


def _build_body(d: dict) -> str:
    return (
        _section_landing(d)
        + _section_macro(d)
        + _section_food(d)
        + _section_insecurity(d)
        + _section_health(d)
        + _footer()
    )


# ── Entry point ───────────────────────────────────────────────────────────────
def write_report(output: Path = ROOT / "report.html"):
    print("Loading data…")
    d = load_all()
    print("Building figures…")
    body = _build_body(d)
    print("Writing HTML…")
    html = build_html(body)
    output.write_text(html, encoding="utf-8")
    kb = output.stat().st_size / 1024
    print(f"Done: {output}  ({kb:.0f} KB)")


if __name__ == "__main__":
    write_report()
