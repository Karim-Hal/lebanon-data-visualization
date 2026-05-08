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
    load_u5mort_mena, load_unhcr_refugees, load_wdi, load_wfp_prices,
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
def _ecolor(key):
    """Map EVENTS color_key to the project PALETTE."""
    return PALETTE[0] if key == "crisis_red" else PALETTE[1]

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
        unhcr  = load_unhcr_refugees(),
    )

# =============================================================================
# HTML primitives
# =============================================================================

CSS = (
    ":root{"
    "--navy:#1F3864;--red:#ff595e;--blue:#1982c4;"
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

    ".filter-bar{"
    "background:white;border-radius:8px;padding:14px 18px;"
    "margin-bottom:18px;border:1px solid var(--border);"
    "display:flex;flex-wrap:wrap;gap:14px;align-items:center;"
    "}"
    ".filter-group{display:flex;align-items:center;gap:10px;flex-wrap:wrap}"
    ".filter-label{"
    "font-size:9px;font-weight:700;letter-spacing:0.12em;"
    "text-transform:uppercase;color:var(--muted);white-space:nowrap;"
    "}"
    ".comm-checks{display:flex;flex-wrap:wrap;gap:8px}"
    ".comm-lbl{"
    "font-size:11px;color:var(--navy);cursor:pointer;"
    "display:flex;align-items:center;gap:5px;"
    "padding:4px 10px;border-radius:4px;"
    "border:1px solid var(--border);transition:background .15s;"
    "user-select:none;"
    "}"
    ".comm-lbl.checked{background:var(--card-bg);border-color:var(--navy);font-weight:600}"
    ".comm-lbl input[type=checkbox]{accent-color:var(--navy);margin:0;cursor:pointer}"
    ".flt-select{"
    "font-size:12px;padding:5px 8px;"
    "border:1px solid var(--border);border-radius:4px;"
    "color:var(--navy);background:white;cursor:pointer;"
    "}"
    ".ipc-btns{display:flex;flex-wrap:wrap;gap:6px}"
    ".ipc-btn{"
    "font-size:11px;font-weight:500;padding:5px 12px;"
    "border:1px solid var(--border);border-radius:20px;"
    "background:white;color:var(--muted);cursor:pointer;transition:all .15s;"
    "}"
    ".ipc-btn:hover{border-color:var(--navy);color:var(--navy)}"
    ".ipc-btn.active{background:var(--navy);color:white;border-color:var(--navy)}"
    ".health-pills{display:flex;flex-wrap:wrap;gap:8px}"
    ".health-pill{"
    "font-size:11px;font-weight:500;padding:5px 14px;"
    "border:1.5px solid var(--border);border-radius:20px;"
    "background:white;color:var(--muted);cursor:pointer;transition:all .15s;"
    "}"
    ".health-pill:hover{border-color:var(--navy);color:var(--navy)}"
    ".health-pill.active{background:var(--card-bg);color:var(--navy);border-color:var(--navy);font-weight:600}"

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

INTERACTIVE_JS = (
    "(function(){"
    # Capture initial layouts once Plotly has rendered everything
    "var LAYS={};"
    '["price_index","lbp_usd","ipc_bar","gov_bar"].forEach(function(id){'
    'var el=document.getElementById("plot-"+id);'
    "if(el&&el.layout)LAYS[id]=JSON.parse(JSON.stringify(el.layout));"
    "});"

    # ── Food filters ──────────────────────────────────────────────────────────
    'var fe=document.getElementById("food-data");'
    "if(!fe)return;"
    "var FOOD=JSON.parse(fe.textContent);"
    "function getYrs(){"
    'var a=document.getElementById("yr-min"),b=document.getElementById("yr-max");'
    "return a&&b?[+a.value,+b.value]:[2012,2026];"
    "}"
    "function getComms(){"
    'return Array.from(document.querySelectorAll(".comm-cb:checked")).map(function(c){return c.value;});'
    "}"
    "function updatePriceIndex(){"
    "var comms=getComms(),yrs=getYrs();"
    "var traces=comms.map(function(comm){"
    "var pts=(FOOD.byComm[comm]||[]).filter(function(p){"
    "var y=+p.ym.slice(0,4);return y>=yrs[0]&&y<=yrs[1];"
    "});"
    "return {"
    "x:pts.map(function(p){return p.ym;}),"
    "y:pts.map(function(p){return p.idx;}),"
    'type:"scatter",mode:"lines",name:comm,'
    'line:{color:FOOD.palette[comm]||"#888",width:2},'
    'hovertemplate:"<b>%{x}</b><br>"+comm+": %{y:.1f}<extra></extra>"'
    "};"
    "});"
    'var div=document.getElementById("plot-price_index");'
    "if(div)Plotly.react(div,traces,LAYS.price_index||div.layout);"
    "}"
    "function updateLbpUsd(){"
    "var yrs=getYrs();"
    "function filt(arr){return arr.filter(function(p){var y=+p.ym.slice(0,4);return y>=yrs[0]&&y<=yrs[1];});}"
    "var lbp=filt(FOOD.basket.lbp),usd=filt(FOOD.basket.usd);"
    "var traces=["
    '{x:lbp.map(function(p){return p.ym;}),y:lbp.map(function(p){return p.price;}),'
    'type:"scatter",mode:"lines",name:"LBP price",yaxis:"y",'
    'line:{color:"#C00000",width:2.5},'
    'hovertemplate:"<b>%{x}</b><br>LBP: %{y:,.0f}<extra></extra>"},'
    '{x:usd.map(function(p){return p.ym;}),y:usd.map(function(p){return p.usdprice;}),'
    'type:"scatter",mode:"lines",name:"USD price",yaxis:"y2",'
    'line:{color:"#2E74B5",width:2.5,dash:"dot"},'
    'hovertemplate:"<b>%{x}</b><br>USD: $%{y:.2f}<extra></extra>"}'
    "];"
    'var div=document.getElementById("plot-lbp_usd");'
    "if(div)Plotly.react(div,traces,LAYS.lbp_usd||div.layout);"
    "}"
    "function onFoodChange(){updatePriceIndex();updateLbpUsd();}"
    # Commodity checkbox listeners + checked-class init
    'document.querySelectorAll(".comm-cb").forEach(function(cb){'
    "if(cb.checked)cb.closest(\"label\").classList.add(\"checked\");"
    "cb.addEventListener(\"change\",function(){"
    "cb.closest(\"label\").classList.toggle(\"checked\",cb.checked);"
    "onFoodChange();"
    "});"
    "});"
    # Year range listeners
    '["yr-min","yr-max"].forEach(function(id){'
    'var el=document.getElementById(id);if(el)el.addEventListener("change",onFoodChange);'
    "});"

    # ── IPC snapshot filter ───────────────────────────────────────────────────
    'var ie=document.getElementById("ipc-data");'
    "if(!ie)return;"
    "var IPC=JSON.parse(ie.textContent);"
    "function updateIPC(dateKey){"
    "var data=IPC.byDate[dateKey];if(!data)return;"
    # Update active button and snap label
    'document.querySelectorAll(".ipc-btn").forEach(function(b){'
    'b.classList.toggle("active",b.dataset.date===dateKey);'
    "});"
    'var sl=document.getElementById("ipc-snap-label");'
    "if(sl){"
    'var d=new Date(dateKey+"T00:00:00");'
    'sl.textContent=d.toLocaleDateString("en-US",{month:"long",year:"numeric"});'
    "}"
    # Choropleth: restyle z and locations only (keeps geojson intact)
    'var cd=document.getElementById("plot-choropleth");'
    "if(cd)Plotly.restyle(cd,{z:[data.choro.z],locations:[data.choro.locations]},[0]);"
    # IPC stacked bar
    'var bd=document.getElementById("plot-ipc_bar");'
    "if(bd){"
    "var ipcTraces=data.ipcBar.phases.map(function(ph){"
    'return {type:"bar",name:ph.name,x:data.ipcBar.govs,y:ph.y,'
    'marker:{color:ph.color,line:{width:0}},'
    'hovertemplate:"<b>%{x}</b><br>"+ph.name+": %{y:.1f}%<extra></extra>"};'
    "});"
    "Plotly.react(bd,ipcTraces,LAYS.ipc_bar||bd.layout);"
    "}"
    # Gov basket price bar
    'var gd=document.getElementById("plot-gov_bar");'
    "if(gd){"
    "var govTraces=data.govBar.govs.length?[{"
    'type:"bar",orientation:"h",'
    "x:data.govBar.y,y:data.govBar.govs,"
    'marker:{color:"#1982c4"},'
    'hovertemplate:"<b>%{y}</b><br>Avg USD: $%{x:.2f}<extra></extra>"}]:[];'
    "var gl=JSON.parse(JSON.stringify(LAYS.gov_bar||gd.layout));"
    "Plotly.react(gd,govTraces,gl);"
    # Update gov-bar year label in HTML
    'var gy=document.getElementById("gov-bar-year");'
    "if(gy)gy.textContent=data.year;"
    "}"
    "}"
    # IPC button click listeners
    'document.querySelectorAll(".ipc-btn").forEach(function(btn){'
    'btn.addEventListener("click",function(){updateIPC(btn.dataset.date);});'
    "});"

    # ── Health indicator explorer ─────────────────────────────────────────────
    'var he=document.getElementById("health-data");'
    "if(!he)return;"
    "var HEALTH=JSON.parse(he.textContent);"
    "function updateHealthExplorer(){"
    'var codes=Array.from(document.querySelectorAll(".health-pill.active")).map(function(p){return p.dataset.code;});'
    'var div=document.getElementById("plot-health_explorer");'
    "if(!div)return;"
    "if(!codes.length){"
    'Plotly.react(div,[],{paper_bgcolor:"#FFF",plot_bgcolor:"#FFF",height:300,'
    'font:{family:"DM Sans, sans-serif",color:"#1F3864"},'
    'annotations:[{text:"Select at least one indicator above",'
    'x:0.5,y:0.5,xref:"paper",yref:"paper",'
    'showarrow:false,font:{size:14,color:"#6B7280",family:"DM Sans, sans-serif"}}]});'
    "return;}"
    "var traces=codes.map(function(code){"
    "var ind=HEALTH.indicators[code];if(!ind)return null;"
    "var baseIdx=ind.years.indexOf(2000);"
    "var base=baseIdx>=0?ind.values[baseIdx]:ind.values[0];"
    "var norm=base>0?ind.values.map(function(v){return+(v/base*100).toFixed(2);}):ind.values.slice();"
    'return {x:ind.years,y:norm,type:"scatter",mode:"lines+markers",name:ind.name,'
    'line:{color:ind.color,width:2},marker:{size:5,color:ind.color},'
    'hovertemplate:"<b>%{x}</b><br>"+ind.name+": %{y:.1f} (2000=100)<extra></extra>"};'
    "}).filter(Boolean);"
    "var layout={"
    'paper_bgcolor:"#FFFFFF",plot_bgcolor:"#FFFFFF",'
    'font:{family:"DM Sans, sans-serif",color:"#1F3864",size:12},'
    "height:380,margin:{l:60,r:20,t:20,b:48},"
    'hovermode:"x unified",'
    'legend:{orientation:"h",yanchor:"bottom",y:1.02,xanchor:"left",x:0},'
    'xaxis:{title:"Year",dtick:5,showgrid:false},'
    'yaxis:{title:"Index (2000 = 100)",gridcolor:"#EEF1F5"},'
    'shapes:[{type:"line",x0:0,x1:1,y0:100,y1:100,xref:"paper",yref:"y",'
    'line:{color:"#D0D0D0",width:1.5,dash:"dot"}}]'
    "};"
    "Plotly.react(div,traces,layout,{responsive:true,displaylogo:false,displayModeBar:true});"
    "}"
    'document.querySelectorAll(".health-pill").forEach(function(pill){'
    'pill.addEventListener("click",function(){pill.classList.toggle("active");updateHealthExplorer();});'
    "});"
    "updateHealthExplorer();"

    # ── Stacked bar governorate: commodity checkbox + year filter ─────────────
    'var gbEl=document.getElementById("gov-bar-comms");'
    "if(gbEl){"
    "var gbData=JSON.parse(gbEl.textContent);"
    "var gbComms=gbData.comms;"
    "var gbGovOrder=gbData.govOrder||[];"
    "var gbByYear=gbData.byYear||{};"
    'var gbDiv=document.getElementById("plot-stacked_bar_govs");'
    'var gbYear="2022";'

    # Apply visibility from checkboxes
    "function applyGovBarVis(){"
    "if(!gbDiv)return;"
    'var vis=gbComms.map(function(c){'
    'var cb=document.querySelector(".gov-bar-cb[value=\'"+c+"\']");'
    "return cb?cb.checked:true;"
    "});"
    "Plotly.restyle(gbDiv,{visible:vis});"
    "}"

    # Apply y-values for the selected year
    "function applyGovBarYear(){"
    "if(!gbDiv||!gbComms.length)return;"
    "var yData=gbByYear[gbYear]||{};"
    "var ys=gbComms.map(function(c){"
    "var cd=yData[c]||{};"
    "return gbGovOrder.map(function(g){return cd[g]||0;});"
    "});"
    "var idxs=gbComms.map(function(_,i){return i;});"
    "Plotly.restyle(gbDiv,{y:ys},idxs);"
    "}"

    # Wire checkboxes
    'document.querySelectorAll(".gov-bar-cb").forEach(function(cb){'
    'cb.addEventListener("change",applyGovBarVis);'
    "});"

    # Wire year buttons
    'document.querySelectorAll(".gov-bar-yr-btn").forEach(function(btn){'
    'btn.addEventListener("click",function(){'
    'document.querySelectorAll(".gov-bar-yr-btn").forEach(function(b){b.classList.remove("active");});'
    'btn.classList.add("active");'
    'gbYear=btn.dataset.year;'
    "applyGovBarYear();"
    "});"
    "});"
    "}"

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
        "<script>" + INTERACTIVE_JS + "</script>\n"
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
        line=dict(color=PALETTE[0], width=2.5), mode="lines+markers",
        marker=dict(size=5),
        hovertemplate="<b>%{x}</b><br>GDP: $%{y:.1f}B<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=lbn_fx["Year"], y=lbn_fx["Value"], name="Official LBP/USD",
        line=dict(color=PALETTE[3], width=2.5, dash="dot"), mode="lines+markers",
        marker=dict(size=5),
        hovertemplate="<b>%{x}</b><br>Rate: %{y:,.0f} LBP/USD<extra></extra>",
    ), secondary_y=True)

    _stagger_y = [0.93, 0.72, 0.51]
    for (date_str, label, color_key, dash), y_pos in zip(EVENTS, _stagger_y):
        yr = pd.Timestamp(date_str).year + (pd.Timestamp(date_str).month - 1) / 12
        col = _ecolor(color_key)
        fig.add_vline(x=yr, line_dash=dash, line_color=col, line_width=1.5)
        fig.add_annotation(
            x=yr, y=y_pos, xref="x", yref="paper",
            text="<b>" + label + "</b>",
            showarrow=False,
            font=dict(size=9, color=col, family="DM Sans, sans-serif"),
            bgcolor="white", bordercolor=col, borderwidth=1, borderpad=4,
            xanchor="left", xshift=5,
        )

    fig.update_yaxes(title_text="GDP (USD billions)", secondary_y=False,
                     tickprefix="$", ticksuffix="B", gridcolor="#EEF1F5")
    fig.update_yaxes(title_text="Official LBP per USD", secondary_y=True,
                     tickformat=",", showgrid=False)
    fig.update_xaxes(title_text="Year", dtick=1, showgrid=False)
    fig.update_layout(**_BASE, height=420, margin=dict(l=60, r=60, t=44, b=48),
                      hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return fig.to_json()


def _fig_fx_spread(wdi, exrate):
    """FX divergence: official LBP/USD (annual, WDI) vs unofficial (monthly, WFP).

    Both lines are anchored at 1,508 LBP/USD (the historic peg) so the viewer
    sees them depart from the same origin. The unofficial series is extended back
    to January 2019 with the peg value so the split is visually explicit.
    Crisis window 2020–2022 shaded in amber. Y axis is log scale.
    """
    off = (
        wdi[(wdi["Country Name"] == "Lebanon") & (wdi["Series Code"] == SERIES["official_fx"])]
        [["Year", "Value"]].dropna().sort_values("Year")
    )
    off = off.assign(date=pd.to_datetime(off["Year"].astype(str) + "-01-01"))
    # Limit official line to 2019 onwards for a focused view
    off = off[off["Year"] >= 2019]

    unof = (
        exrate[exrate["commodity"] == "Exchange rate (unofficial)"]
        .groupby("year_month", as_index=False)["price"].mean()
    )
    unof["date"] = pd.to_datetime(unof["year_month"])
    unof = unof.sort_values("date")

    # Anchor the unofficial series at 1,508 starting Jan 2019 so both lines
    # share the same origin and the divergence is visually clear.
    anchor = pd.DataFrame([{"date": pd.Timestamp("2019-01-01"), "price": 1508.0}])
    unof = pd.concat([anchor, unof], ignore_index=True).sort_values("date")

    fig = go.Figure()

    # Shaded crisis window 2020–2022 (same style as health small-multiples)
    fig.add_vrect(
        x0=pd.Timestamp("2020-01-01"),
        x1=pd.Timestamp("2022-12-31"),
        fillcolor=COLORS["warning"],
        opacity=0.10,
        line_width=0,
    )
    fig.add_annotation(
        x=pd.Timestamp("2021-06-01"), y=1, xref="x", yref="paper",
        text="2020–2022 crisis window",
        showarrow=False,
        font=dict(size=9, color=COLORS["warning"], family="DM Sans, sans-serif"),
        yanchor="top",
    )

    fig.add_trace(go.Scatter(
        x=off["date"], y=off["Value"], name="Official rate (WDI)",
        mode="lines+markers",
        line=dict(color=PALETTE[3], width=2, shape="hv"),
        marker=dict(size=5),
        hovertemplate="<b>%{x|%Y}</b><br>Official: %{y:,.0f} LBP/USD<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=unof["date"], y=unof["price"], name="Unofficial rate (WFP)",
        mode="lines",
        line=dict(color=PALETTE[0], width=2.5),
        fill="tonexty",
        fillcolor="rgba(255,89,94,0.10)",
        hovertemplate="<b>%{x|%b %Y}</b><br>Unofficial: %{y:,.0f} LBP/USD<extra></extra>",
    ))

    # Annotation at the shared starting point
    fig.add_annotation(
        x=pd.Timestamp("2019-01-01"), y=1508,
        text="<b>Jan 2019</b><br>1,508 LBP/USD",
        showarrow=True, arrowhead=2, arrowwidth=1.5,
        arrowcolor=PALETTE[3], ax=40, ay=-40,
        font=dict(size=10, color=PALETTE[3], family="DM Sans, sans-serif"),
        bgcolor="white", bordercolor=PALETTE[3], borderwidth=1, borderpad=5,
        xanchor="left",
    )

    # Annotation at April 2023
    apr23_rate = unof[unof["date"] == pd.Timestamp("2023-04-15")]["price"].values
    apr23_y = float(apr23_rate[0]) if len(apr23_rate) else 97814
    fig.add_annotation(
        x=pd.Timestamp("2023-04-15"), y=apr23_y,
        text="<b>Apr 2023</b><br>{:,.0f} LBP/USD".format(apr23_y),
        showarrow=True, arrowhead=2, arrowwidth=1.5,
        arrowcolor=PALETTE[0], ax=-10, ay=-50,
        font=dict(size=10, color=PALETTE[0], family="DM Sans, sans-serif"),
        bgcolor="white", bordercolor=PALETTE[0], borderwidth=1, borderpad=5,
        xanchor="right",
    )

    fig.update_layout(
        **_BASE, height=420, margin=dict(l=70, r=24, t=44, b=48),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(title="Year", showgrid=False, range=[pd.Timestamp("2018-07-01"), pd.Timestamp("2025-01-01")]),
        yaxis=dict(title="LBP per USD (log scale)", type="log", gridcolor="#EEF1F5"),
    )
    return fig.to_json()


def _fig_remittances(wdi):
    """2023 snapshot bar chart of personal remittances as % of GDP.

    For each country, uses the 2023 value if available, otherwise the most
    recent year with data. Countries sorted descending so Lebanon (the
    outlier) sits prominently. Color follows the project's COUNTRY_COLORS
    palette for consistency.
    """
    df = wdi[wdi["Series Code"] == SERIES["remittances"]].copy().dropna(subset=["Value"])

    # Best available year ≤ 2023 per country
    df = df[df["Year"] <= 2023].sort_values("Year")
    snapshot = df.groupby("Country Name", as_index=False).last()[["Country Name", "Value", "Year"]]
    snapshot = snapshot.sort_values("Value", ascending=True)  # ascending so largest bar is at top

    colors = [COUNTRY_COLORS.get(c, "#888") for c in snapshot["Country Name"]]

    fig = go.Figure(go.Bar(
        x=snapshot["Value"],
        y=snapshot["Country Name"],
        orientation="h",
        marker_color=colors,
        customdata=snapshot["Year"],
        hovertemplate=(
            "<b>%{y}</b><br>%{x:.1f}% of GDP"
            "<br><span style='color:#888'>(%{customdata})</span>"
            "<extra></extra>"
        ),
        text=snapshot["Value"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
        textfont=dict(size=11),
    ))

    fig.update_layout(
        **_BASE, height=320,
        margin=dict(l=140, r=60, t=20, b=40),
        xaxis=dict(
            title="Remittances (% of GDP)",
            ticksuffix="%",
            gridcolor="#EEF1F5",
            showgrid=True,
        ),
        yaxis=dict(showgrid=False),
    )
    return fig.to_json()


_SYRIA_INFLATION_FILL = {
    # Independent estimates used to fill gaps in WDI's Syria CPI series.
    # Sources: SCPR annual & monthly CPI bulletins; Central Bank of Syria;
    # SCPR June 2024 monthly bulletin.
    2020: 114.0,
    2021: 110.0,
    2022:  85.0,
    2023: 116.0,
    2024: 108.0,
}


def _fig_inflation_heatmap(wdi):
    """Country × Year heatmap of annual inflation, 2015 onwards.

    Inflation is signed data — negative = deflation, positive = inflation —
    so a diverging colour scale is the principled choice. Green for deflation,
    near-white at zero, red for high inflation. The diverging midpoint is
    locked to 0 by computing the relative position of zero in [zmin, zmax]
    and using it as the white anchor of the colorscale.
    """
    NEG_FLOOR = -10.0   # ensure a visible green band even if no deflation
    POS_CAP   = 300.0   # cap Lebanon/Syria hyperinflation for readability
    inf = wdi[wdi["Series Code"] == SERIES["inflation"]].copy()
    pivot = inf.pivot_table(index="Country Name", columns="Year", values="Value")

    # Fill Syria gaps (WDI stops reporting after 2019 due to the war).
    if "Syrian Arab Republic" in pivot.index:
        for yr, val in _SYRIA_INFLATION_FILL.items():
            if yr not in pivot.columns:
                pivot[yr] = pd.NA
            current = pivot.loc["Syrian Arab Republic", yr]
            if pd.isna(current):
                pivot.loc["Syrian Arab Republic", yr] = val

    years = sorted(y for y in pivot.columns if 2015 <= y <= 2024)
    country_order = ["Lebanon"] + sorted(c for c in pivot.index if c != "Lebanon")
    pivot = pivot.loc[[c for c in country_order if c in pivot.index], years]

    z_vals, text_vals = [], []
    for country in pivot.index:
        row_z, row_t = [], []
        for yr in years:
            v = pivot.loc[country, yr] if yr in pivot.columns else None
            if v is None or (isinstance(v, float) and v != v):
                row_z.append(None)
                row_t.append("")
            else:
                row_z.append(max(NEG_FLOOR, min(float(v), POS_CAP)))
                row_t.append("{:.0f}%".format(float(v)))
        z_vals.append(row_z)
        text_vals.append(row_t)

    flat = [v for row in z_vals for v in row if v is not None]
    z_min = min(min(flat), NEG_FLOOR) if flat else NEG_FLOOR
    z_max = max(max(flat), 1.0)       if flat else POS_CAP
    zero_pos = (-z_min) / (z_max - z_min) if z_max > z_min else 0.5

    # Diverging green→white→red, with white anchored at z=0.
    eps = 1e-3
    colorscale = [
        [0.00,                  "#1a9850"],   # deep green (deflation)
        [max(0.0, zero_pos*0.5), "#91cf60"],  # green
        [max(0.0, zero_pos - eps), "#d9ef8b"],  # light green just before zero
        [zero_pos,              "#ffffbf"],   # neutral at zero
        [min(1.0, zero_pos + (1-zero_pos)*0.20), "#fee08b"],
        [min(1.0, zero_pos + (1-zero_pos)*0.45), "#fdae61"],
        [min(1.0, zero_pos + (1-zero_pos)*0.70), "#f46d43"],
        [1.00,                  "#a50026"],   # deep red (high inflation)
    ]

    fig = go.Figure(go.Heatmap(
        z=z_vals,
        x=[str(y) for y in years],
        y=list(pivot.index),
        text=text_vals,
        texttemplate="%{text}",
        colorscale=colorscale,
        zmin=z_min,
        zmax=z_max,
        zmid=0,
        colorbar=dict(
            title="Inflation %", ticksuffix="%", len=0.7,
            tickvals=[0, 50, 100, 200, 300],
        ),
        hoverongaps=False,
        hovertemplate="<b>%{y}</b><br>%{x}: %{text}<extra></extra>",
        textfont=dict(family="DM Sans, sans-serif", size=10, color="#1F3864"),
    ))
    fig.update_layout(
        **_BASE,
        height=290,
        margin=dict(l=185, r=20, t=10, b=55),
        xaxis=dict(tickangle=-45, showgrid=False, side="bottom"),
        yaxis=dict(showgrid=False, autorange="reversed"),
    )
    return fig.to_json()


def _fig_gdp_pc_line(wdi):
    """GDP per capita line chart (2015 onwards), six countries.

    Line charts beat tables for time-series comparison: the eye reads
    direction and rate of change instantly. Colour follows the project's
    COUNTRY_COLORS map so countries are visually consistent across pages.
    Lebanon is rendered thicker and on top of the z-stack to anchor
    attention on its collapse.
    """
    df = (
        wdi[(wdi["Series Code"] == SERIES["gdp_pc"]) & (wdi["Year"] >= 2015)]
        .dropna(subset=["Value"])
        .sort_values(["Country Name", "Year"])
    )

    # Lebanon last so it renders on top
    country_order = sorted(df["Country Name"].unique(), key=lambda c: c == "Lebanon")

    fig = go.Figure()
    for country in country_order:
        sub = df[df["Country Name"] == country]
        if sub.empty:
            continue
        is_lbn = country == "Lebanon"
        fig.add_trace(go.Scatter(
            x=sub["Year"],
            y=sub["Value"],
            name=country,
            mode="lines+markers",
            line=dict(
                color=COUNTRY_COLORS.get(country, "#888"),
                width=3.5 if is_lbn else 2,
            ),
            marker=dict(size=7 if is_lbn else 5),
            hovertemplate=(
                "<b>" + country + "</b><br>%{x}: $%{y:,.0f}<extra></extra>"
            ),
        ))

    fig.update_layout(
        **_BASE,
        height=420,
        margin=dict(l=70, r=24, t=44, b=48),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        yaxis=dict(
            title="GDP per capita (USD)",
            tickprefix="$",
            tickformat=",",
            gridcolor="#EEF1F5",
        ),
        xaxis=dict(showgrid=False, dtick=1, tickangle=-45),
    )
    return fig.to_json()


def _rebase_price_index(prices):
    """Return prices with price_index filled for commodities missing 2019 data."""
    df = prices.copy()
    for comm in BASKET:
        mask = df["commodity"] == comm
        if not mask.any():
            continue
        if df.loc[mask, "price_index"].isna().all():
            for yr in range(2019, 2028):
                base = df.loc[mask & (df["date"].dt.year == yr), "usdprice"].mean()
                if pd.notna(base) and base > 0:
                    df.loc[mask, "price_index"] = df.loc[mask, "usdprice"] / base * 100
                    break
    return df


def _fig_price_index(prices):
    prices = _rebase_price_index(prices)
    df = (
        prices[
            prices["commodity"].isin(BASKET)
            & (prices["date"] >= pd.Timestamp("2018-01-01"))
            & (prices["date"] <= pd.Timestamp("2023-01-31"))
        ]
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
    _stagger_y = [0.93, 0.72, 0.51]
    for (date_str, label, color_key, dash), y_pos in zip(EVENTS, _stagger_y):
        ts = pd.Timestamp(date_str).timestamp() * 1000
        col = _ecolor(color_key)
        fig.add_vline(x=ts, line_dash=dash, line_color=col, line_width=1.5)
        fig.add_annotation(
            x=ts, y=y_pos, xref="x", yref="paper",
            text="<b>" + label + "</b>",
            showarrow=False,
            font=dict(size=9, color=col, family="DM Sans, sans-serif"),
            bgcolor="white", bordercolor=col, borderwidth=1, borderpad=4,
            xanchor="left", xshift=5,
        )
    fig.update_layout(**_BASE, height=420, margin=dict(l=52, r=24, t=44, b=52),
                      hovermode="x unified",
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                      yaxis=dict(gridcolor="#EEF1F5"))
    fig.update_xaxes(showgrid=False)
    return fig.to_json()


def _fig_lbp_usd(basket):
    lbp_m = monthly_basket_lbp(basket)
    usd_m = monthly_basket_usd(basket)
    # Match the price-index chart's default 2018–2023 window;
    # the shared year-range filter widens it to the full series on demand.
    lbp_m = lbp_m[(lbp_m["year_month"] >= "2018-01") & (lbp_m["year_month"] <= "2023-12")]
    usd_m = usd_m[(usd_m["year_month"] >= "2018-01") & (usd_m["year_month"] <= "2023-12")]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(
        x=lbp_m["year_month"], y=lbp_m["price"], name="LBP price",
        line=dict(color=PALETTE[0], width=2.5),
        hovertemplate="<b>%{x}</b><br>LBP: %{y:,.0f}<extra></extra>",
    ), secondary_y=False)
    fig.add_trace(go.Scatter(
        x=usd_m["year_month"], y=usd_m["usdprice"], name="USD price",
        line=dict(color=PALETTE[3], width=2.5, dash="dot"),
        hovertemplate="<b>%{x}</b><br>USD: $%{y:.2f}<extra></extra>",
    ), secondary_y=True)

    _stagger_y = [0.93, 0.72, 0.51]
    for (date_str, label, color_key, dash), y_pos in zip(EVENTS, _stagger_y):
        ym = pd.Timestamp(date_str).strftime("%Y-%m")
        col = _ecolor(color_key)
        fig.add_shape(type="line", x0=ym, x1=ym, y0=0, y1=1,
                      xref="x", yref="paper",
                      line=dict(color=col, width=1.5,
                                dash="dash" if dash == "dash" else "solid"))
        fig.add_annotation(x=ym, y=y_pos, xref="x", yref="paper",
                           text="<b>" + label + "</b>",
                           showarrow=False, xanchor="left", xshift=5,
                           font=dict(size=9, color=col, family="DM Sans, sans-serif"),
                           bgcolor="white", bordercolor=col, borderwidth=1, borderpad=4)

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
        color_discrete_sequence=[PALETTE[3]],
        hover_data={"year_month": True, "price": ":.0f", "usdprice": ":.2f"},
    )
    fig.update_traces(selector=dict(mode="markers"),
                      marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color="white")))
    fig.update_traces(selector=dict(mode="lines"),
                      line=dict(color=PALETTE[0], width=2))
    fig.add_annotation(xref="paper", yref="paper", x=0.05, y=0.95,
                       text="<b>R² = {:.3f}</b>  (r = {:.3f})".format(r2, r),
                       showarrow=False,
                       font=dict(size=14, color=COLORS["deep_navy"], family="DM Sans, sans-serif"),
                       bgcolor="white", bordercolor=COLORS["deep_navy"], borderwidth=1, borderpad=8)
    fig.update_layout(**_BASE, height=420, margin=dict(l=60, r=24, t=40, b=60),
                      xaxis=dict(tickformat=",", gridcolor="#EEF1F5", showgrid=True),
                      yaxis=dict(tickprefix="$", gridcolor="#EEF1F5"))
    return fig.to_json(), r, r2, len(sdf)


def _fig_treemap(prices):
    """Treemap of price increase since 2019, grouped by food category.

    Area = % price increase (normalized — so absolute price level doesn't
    distort tile size). Chicken being inherently expensive doesn't make its
    tile bigger; only *how much* it rose since 2019 determines the area.
    Color follows the same sequential scale (amber → deep red) so the
    heaviest-hit commodities are both biggest AND darkest.
    """
    from src.config import BASKET_CATEGORIES

    prices = _rebase_price_index(prices)
    df = (
        prices[prices["commodity"].isin(BASKET)]
        .dropna(subset=["price_index"])
        .sort_values("date")
        .groupby("commodity", as_index=False)
        .last()
    )
    df["category"]   = df["commodity"].map(BASKET_CATEGORIES).fillna("Other")
    df["short"]      = df["commodity"].str.split("(").str[0].str.strip()
    df["pct_change"] = (df["price_index"] - 100).clip(lower=1).round(0).astype(int)

    color_max = max(500, int(df["pct_change"].max() or 500))

    fig = px.treemap(
        df,
        path=[px.Constant("Basket"), "category", "commodity"],
        values="pct_change",          # area ∝ % rise since 2019
        color="pct_change",           # color encodes same metric
        color_continuous_scale=[
            [0.0,  "#fff3cd"],        # pale amber (lowest rise)
            [0.35, PALETTE[1]],       # amber
            [0.65, PALETTE[0]],       # coral red
            [1.0,  COLORS["crisis_red"]],  # deep red (worst)
        ],
        range_color=(0, color_max),
        custom_data=["short", "pct_change"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>+%{customdata[1]}%",
        textfont=dict(family="DM Sans, sans-serif", size=13, color="#1F3864"),
        marker_line_width=2,
        marker_line_color="white",
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Price rise since 2019: <b>+%{customdata[1]}%</b>"
            "<extra></extra>"
        ),
    )
    fig.update_layout(
        **_BASE,
        height=400,
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_colorbar=dict(title="% rise since 2019", ticksuffix="%", len=0.7),
    )
    return fig.to_json()


def _fig_price_discrepancy(basket, wdi):
    """USD basket price at the official peg vs. the market rate — the hidden food price gap.

    Lebanon maintained an official peg of ~1,507 LBP/USD for decades while the
    parallel market rate collapsed to 90,000+. Dividing the same LBP market basket
    price by each rate produces two very different USD figures:

    • At the official rate: the basket appears enormously expensive in USD because
      LBP prices rose in the market but the denominator (official rate) barely moved.
    • At the market rate:  the basket is cheaper in USD but still rose — confirming
      real purchasing-power loss beyond just the currency collapse.

    The gap between these two lines is the magnitude of the official-rate illusion.
    WFP's `usdprice` column uses the market/parallel rate, not the official peg.
    """
    lbp_m = monthly_basket_lbp(basket)

    # Official annual rate (WDI PA.NUS.FCRF) → broadcast to each month in the year
    offrate_df = (
        wdi[(wdi["Country Name"] == "Lebanon") & (wdi["Series Code"] == SERIES["official_fx"])]
        [["Year", "Value"]].dropna().sort_values("Year")
    )
    official_by_ym: dict = {}
    for _, row in offrate_df.iterrows():
        yr = int(row["Year"])
        for m in range(1, 13):
            official_by_ym[f"{yr:04d}-{m:02d}"] = float(row["Value"])

    lbp_m["official_rate"] = lbp_m["year_month"].map(official_by_ym)
    lbp_m = lbp_m.dropna(subset=["official_rate", "price"])
    lbp_m["usd_official"] = lbp_m["price"] / lbp_m["official_rate"]

    # Market USD price from basket data
    usd_m = monthly_basket_usd(basket)
    df = pd.merge(lbp_m[["year_month", "usd_official"]], usd_m, on="year_month")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["year_month"], y=df["usd_official"],
        name="At official rate (gov peg)",
        line=dict(color=PALETTE[0], width=2.5, dash="dot"),
        hovertemplate="<b>%{x}</b><br>Official rate: $%{y:.2f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["year_month"], y=df["usdprice"],
        name="At market rate (reality)",
        line=dict(color=PALETTE[3], width=2.5),
        hovertemplate="<b>%{x}</b><br>Market rate: $%{y:.2f}<extra></extra>",
    ))

    # Shade the gap between the two lines
    fig.add_trace(go.Scatter(
        x=list(df["year_month"]) + list(df["year_month"])[::-1],
        y=list(df["usd_official"]) + list(df["usdprice"])[::-1],
        fill="toself",
        fillcolor="rgba(255,89,94,0.08)",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip",
    ))

    # Event markers
    for date_str, label, color_key, dash in EVENTS:
        ts = pd.Timestamp(date_str)
        ym = ts.strftime("%Y-%m")
        if ym in df["year_month"].values:
            col = _ecolor(color_key)
            fig.add_shape(
                type="line", x0=ym, x1=ym, y0=0, y1=1,
                xref="x", yref="paper",
                line=dict(color=col, width=1.5, dash="dash" if dash == "dash" else "solid"),
            )
            fig.add_annotation(
                x=ym, y=0.97, xref="x", yref="paper",
                text=label, showarrow=False, xanchor="left", xshift=5,
                font=dict(size=9, color=col, family="DM Sans, sans-serif"),
                bgcolor="white", bordercolor=col, borderwidth=1, borderpad=4,
            )

    fig.update_layout(
        **_BASE, height=420,
        margin=dict(l=70, r=24, t=44, b=60),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        yaxis=dict(title="Avg basket price (USD)", tickprefix="$", gridcolor="#EEF1F5"),
        xaxis=dict(tickangle=-45, nticks=16, showgrid=False),
    )
    return fig.to_json()


# ---------------------------------------------------------------------------
# Regional food price builders (2022 snapshot) — stacked bar, choropleth,
# and district-level treemap drawn from WFP market survey data.
# ---------------------------------------------------------------------------

# Distinct categorical palette for 24 commodities.
import plotly.colors as _pc
_COMM_PALETTE = (
    _pc.qualitative.D3
    + _pc.qualitative.G10
    + _pc.qualitative.Pastel
)

# Commodities present in ALL 8 governorates in 2022 (pre-validated).
_GOVS_COMMON_COMMS = [
    "Beans (white)", "Bread (pita)", "Bulgur (brown)", "Cabbage",
    "Cheese (picon)", "Chickpeas", "Cucumbers (greenhouse)", "Eggs",
    "Fish (sardine, canned)", "Fish (tuna, canned)", "Lentils",
    "Lentils (green)", "Lentils (red)", "Lettuce", "Meat (beef, canned)",
    "Milk (powder)", "Oil (sunflower)", "Pasta (spaghetti)",
    "Rice (imported, Egyptian)", "Salt", "Sugar (white)", "Tea",
    "Tomatoes (paste)", "Wheat flour",
]

# The 15 commodities shown in the reference image — default selection.
_GOVS_DEFAULT_COMMS = {
    "Beans (white)", "Bread (pita)", "Bulgur (brown)", "Cabbage",
    "Cheese (picon)", "Chickpeas", "Lentils", "Milk (powder)",
    "Oil (sunflower)", "Pasta (spaghetti)", "Rice (imported, Egyptian)",
    "Salt", "Sugar (white)", "Tomatoes (paste)", "Wheat flour",
}

# Short display names for commodity labels.
def _short_comm(name: str) -> str:
    return name.split("(")[0].strip()


# Package sizes as surveyed by WFP in 2022.
# Shown in legend and tooltips so viewers know prices are per-package, not per-kg.
_COMM_UNITS: dict = {
    "Beans (white)":              "900 g",
    "Bread (pita)":               "800 g",
    "Bulgur (brown)":             "900 g",
    "Cabbage":                    "1 kg",
    "Cheese (picon)":             "160 g",
    "Chickpeas":                  "900 g",
    "Cucumbers (greenhouse)":     "1 kg",
    "Eggs":                       "30 pcs",
    "Fish (sardine, canned)":     "125 g",
    "Fish (tuna, canned)":        "185 g",
    "Lentils":                    "900 g",
    "Lentils (green)":            "1 kg",
    "Lentils (red)":              "1 kg",
    "Lettuce":                    "1 head",
    "Meat (beef, canned)":        "200 g",
    "Milk (powder)":              "750 g",
    "Oil (sunflower)":            "5 L",
    "Pasta (spaghetti)":          "500 g",
    "Rice (imported, Egyptian)":  "900 g",
    "Salt":                       "700 g",
    "Sugar (white)":              "5 kg",
    "Tea":                        "160 g",
    "Tomatoes (paste)":           "660 g",
    "Wheat flour":                "900 g",
}


def _fig_stacked_bar_govs(prices, gov_order):
    """Stacked bar: average LBP price per commodity per governorate, 2022.

    gov_order is pre-computed in _section_food so the same ordering is embedded
    in both the figure x-axis and the multi-year JS data blob.
    """
    df22 = prices[
        (prices["date"].dt.year == 2022) &
        (prices["commodity"].isin(_GOVS_COMMON_COMMS))
    ].dropna(subset=["price"])

    bar = (
        df22.groupby(["admin1", "commodity"], as_index=False)["price"]
        .mean()
        .assign(price=lambda x: x["price"].round(0))
    )

    color_map = {c: _COMM_PALETTE[i % len(_COMM_PALETTE)]
                 for i, c in enumerate(_GOVS_COMMON_COMMS)}

    fig = go.Figure()
    for comm in _GOVS_COMMON_COMMS:
        sub = bar[bar["commodity"] == comm].set_index("admin1").reindex(gov_order)
        unit = _COMM_UNITS.get(comm, "")
        short = _short_comm(comm)
        fig.add_trace(go.Bar(
            name=f"{short} ({unit})",
            x=gov_order,
            y=sub["price"].values,
            marker_color=color_map[comm],
            visible=True if comm in _GOVS_DEFAULT_COMMS else "legendonly",
            hovertemplate=(
                "<b>%{x}</b><br>"
                + short + f" <span style='color:#888'>per {unit}</span>"
                + ": %{y:,.0f} LBP<extra></extra>"
            ),
        ))

    fig.update_layout(
        **_BASE,
        barmode="stack",
        height=500,
        margin=dict(l=60, r=220, t=20, b=60),
        legend=dict(orientation="v", x=1.01, y=1, font=dict(size=10)),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            title="Avg price (LBP)",
            gridcolor="#EEF1F5",
            tickformat=",",
        ),
        hovermode="x unified",
    )
    return fig.to_json()


def _fig_food_price_choropleth(prices):
    """Choropleth of Lebanese governorates coloured by average commodity
    price in USD (2022). Sequential single-hue scale — darker = pricier.
    """
    with open(GEOJSON_PATH) as f:
        geojson = json.load(f)

    df22 = prices[prices["date"].dt.year == 2022].dropna(subset=["usdprice"])
    gov_avg = (
        df22.groupby("admin1", as_index=False)["usdprice"]
        .mean()
        .rename(columns={"admin1": "gov", "usdprice": "avg_usd"})
    )
    gov_avg["avg_usd"] = gov_avg["avg_usd"].round(2)

    # Mirror Mount Lebanon value to Keserwan-Jbeil (GeoJSON has it as a separate feature)
    ml = gov_avg[gov_avg["gov"] == "Mount Lebanon"]
    if not ml.empty:
        kj = ml.copy()
        kj["gov"] = "Keserwan-Jbeil"
        gov_avg = pd.concat([gov_avg, kj], ignore_index=True)

    fig = px.choropleth_map(
        gov_avg,
        geojson=geojson,
        locations="gov",
        featureidkey="properties.shapeName",
        color="avg_usd",
        color_continuous_scale=[
            [0.0, "#EBF3FB"],
            [0.4, PALETTE[3]],
            [0.7, PALETTE[4]],
            [1.0, COLORS["deep_navy"]],
        ],
        map_style="carto-positron",
        center={"lat": 33.85, "lon": 35.86},
        zoom=7,
        opacity=0.80,
        labels={"avg_usd": "Avg price (USD)"},
        hover_name="gov",
        hover_data={"gov": False, "avg_usd": ":.2f"},
    )
    fig.update_layout(
        height=440,
        margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title="Avg USD", tickprefix="$", len=0.7),
    )
    return fig.to_json()


def _fig_price_treemap_districts(prices):
    """Treemap: Governorate → District, sized by avg commodity price in USD (2022).

    No sequential colorscale. Each governorate gets one distinct categorical
    color from the project palette; its districts inherit that same color.
    The outer 'Lebanon' wrapper is removed so governorates are the top level.
    """
    df22 = prices[prices["date"].dt.year == 2022].dropna(subset=["usdprice"])
    dist = (
        df22.groupby(["admin1", "admin2"], as_index=False)["usdprice"]
        .mean()
        .rename(columns={"usdprice": "avg_usd"})
    )
    dist["avg_usd"] = dist["avg_usd"].round(2)

    govs = sorted(dist["admin1"].unique())
    gov_color_map = {gov: PALETTE[i % len(PALETTE)] for i, gov in enumerate(govs)}
    # color column = governorate so districts inherit their parent's color
    dist["gov_color"] = dist["admin1"]

    fig = px.treemap(
        dist,
        path=["admin1", "admin2"],   # no outer Lebanon layer
        values="avg_usd",
        color="gov_color",
        color_discrete_map=gov_color_map,
        custom_data=["admin1", "admin2", "avg_usd"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>$%{value:.2f}",
        textfont=dict(family="DM Sans, sans-serif", size=12, color="white"),
        marker_line_width=2,
        marker_line_color="white",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Avg commodity price: <b>$%{value:.2f}</b>"
            "<extra></extra>"
        ),
    )
    fig.update_layout(
        **_BASE,
        height=560,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        coloraxis_showscale=False,
    )
    return fig.to_json()


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


def _fig_unhcr_choropleth(unhcr):
    with open(GEOJSON_PATH) as f:
        geojson = json.load(f)

    df = unhcr.copy()
    ml = df[df["governorate"] == "Mount Lebanon"]
    if not ml.empty:
        kj = ml.copy()
        kj["governorate"] = "Keserwan-Jbeil"
        df = pd.concat([df, kj], ignore_index=True)

    as_of = pd.to_datetime(unhcr["as_of_date"]).max().strftime("%b %Y")

    fig = px.choropleth_map(
        df, geojson=geojson,
        locations="governorate", featureidkey="properties.shapeName",
        color="registered_refugees",
        color_continuous_scale=[
            [0.0, COLORS["card_bg"]],
            [0.5, PALETTE[3]],
            [1.0, PALETTE[0]],
        ],
        map_style="carto-positron",
        center={"lat": 33.85, "lon": 35.86},
        zoom=7, opacity=0.78,
        labels={"registered_refugees": "Refugees"},
        hover_name="governorate",
        hover_data={"governorate": False, "registered_refugees": ":,"},
    )
    fig.update_layout(
        **_BASE, height=440, margin=dict(l=0, r=0, t=0, b=0),
        coloraxis_colorbar=dict(title="Refugees<br>(" + as_of + ")", tickformat=",", len=0.7),
    )
    return fig.to_json()


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
            [0,   PALETTE[2]],
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
            font=dict(size=15, color=COLORS["deep_navy"], family="DM Sans, sans-serif"),
        )],
    )
    return fig.to_json()


def _fig_pop_group_time(ipc_pop):
    """Phase 3+ % over time per population group."""
    df = ipc_pop.dropna(subset=["Phase 3+ percentage current", "analysis_date"]).copy()
    df = df[df["Level 1"].isin(POPULATION_GROUPS)]
    df["pct"] = (df["Phase 3+ percentage current"] * 100).round(1)
    df["headcount"] = df["Phase 3+ number current"].fillna(0)
    df = df.sort_values(["Level 1", "analysis_date"])

    fig = go.Figure()
    for i, group in enumerate(POPULATION_GROUPS):
        sub = df[df["Level 1"] == group]
        if sub.empty:
            continue
        color = PALETTE[i % len(PALETTE)]
        fig.add_trace(go.Scatter(
            x=sub["analysis_date"], y=sub["pct"],
            mode="lines+markers",
            name=group,
            line=dict(color=color, width=2.5),
            marker=dict(size=[max(6, min(18, (h ** 0.5) / 10)) for h in sub["headcount"]],
                        color=color,
                        line=dict(color="white", width=1)),
            customdata=sub["headcount"],
            hovertemplate=(
                "<b>" + group + "</b><br>%{x|%b %Y}<br>"
                "Phase 3+: %{y:.1f}%<br>People: %{customdata:,.0f}<extra></extra>"
            ),
        ))
    fig.update_layout(
        **_BASE, height=360, margin=dict(l=60, r=24, t=24, b=48),
        hovermode="closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(title="Phase 3+ (%)", ticksuffix="%", gridcolor="#EEF1F5"),
    )
    return fig.to_json()


def _fig_treemap_insecurity(geo_snap, ipc_pop):
    """Treemap of Phase 3+ headcount: Governorate -> Population Group.

    Combines two independent IPC surveys:
      - geo_snap: per-governorate phase rates  (population NOT broken by group)
      - ipc_pop:  per-group phase rates        (NOT broken by governorate)

    Approximation: assume the latest national group composition holds uniformly
    in every governorate. Tile area = (gov_phase3plus_pop) * (group_share_at_national).
    Color = group's national Phase 3+ rate.
    Caption MUST disclose this assumption.
    """
    gov_df = (
        geo_snap.dropna(subset=["gov"])
        .groupby("gov", as_index=False)
        .agg(p3_pct=("Phase 3+ percentage current", "mean"),
             pop=("Population analyzed current", "mean"))
    )
    gov_df["p3_pop"] = gov_df["p3_pct"] * gov_df["pop"]

    pop_latest = (
        ipc_pop.dropna(subset=["Phase 3+ number current"])
        .sort_values("analysis_date")
        .groupby("Level 1", as_index=False)
        .last()
    )
    grp_total = pop_latest["Phase 3+ number current"].sum()
    if grp_total <= 0 or gov_df.empty:
        fig = go.Figure()
        fig.update_layout(**_BASE, height=320,
                          annotations=[dict(text="Insufficient IPC data",
                                            x=0.5, y=0.5, xref="paper", yref="paper",
                                            showarrow=False)])
        return fig.to_json()

    pop_latest = pop_latest.assign(
        share=pop_latest["Phase 3+ number current"] / grp_total,
        rate=pop_latest["Phase 3+ percentage current"],
    )

    rows = []
    for _, g in gov_df.iterrows():
        for _, p in pop_latest.iterrows():
            rows.append({
                "gov":   g["gov"],
                "group": p["Level 1"],
                "p3_pop": float(g["p3_pop"]) * float(p["share"]),
                "rate":  float(p["rate"]),
            })
    cross = pd.DataFrame(rows)
    cross = cross[cross["p3_pop"] > 0]

    fig = px.treemap(
        cross,
        path=[px.Constant("Lebanon"), "gov", "group"],
        values="p3_pop",
        color="rate",
        color_continuous_scale=[
            [0.0, COLORS["card_bg"]],
            [0.5, COLORS["ipc_phase_3"]],
            [1.0, COLORS["ipc_phase_5"]],
        ],
        range_color=(0, 1),
        custom_data=["p3_pop", "rate"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>~%{customdata[0]:,.0f}",
        textfont=dict(family="DM Sans, sans-serif", size=11, color="#FFFFFF"),
        marker_line_width=2, marker_line_color="white",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Phase 3+ headcount (est.): %{customdata[0]:,.0f}<br>"
            "Group Phase 3+ rate: %{customdata[1]:.0%}<extra></extra>"
        ),
    )
    fig.update_layout(
        **_BASE, height=400, margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_colorbar=dict(title="Phase 3+ rate", tickformat=".0%", len=0.7),
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
        fig.add_vrect(x0=2020, x1=2022, fillcolor=PALETTE[1], opacity=0.08,
                      line_width=0, row=r, col=1)
        for yr in [2020, 2022]:
            fig.add_vline(x=yr, line_dash="dash", line_color=PALETTE[1],
                          line_width=1, opacity=0.6, row=r, col=1)

    fig.add_annotation(x=2021, y=1, xref="x", yref="paper",
                       text="Crisis window<br>2020-2022", showarrow=False,
                       font=dict(size=10, color=PALETTE[1], family="DM Sans, sans-serif"),
                       bgcolor="rgba(255,255,255,0.8)")
    fig.update_yaxes(title_text="Price Index", row=1, col=1, gridcolor="#EEF1F5")
    fig.update_yaxes(title_text="Stunting (%)", row=2, col=1, ticksuffix="%", gridcolor="#EEF1F5")
    fig.update_xaxes(title_text="Year", row=2, col=1, dtick=2, showgrid=False)
    fig.update_xaxes(showgrid=False, row=1, col=1)
    fig.update_layout(**_BASE, height=520, margin=dict(l=60, r=24, t=48, b=48),
                      showlegend=False, hovermode="x unified")
    return fig.to_json()


def _fig_small_multiples(health):
    """2×2 grid: Stunting, Anaemia, Infant mortality, Under-5 mortality.
    Shaded crisis window 2020-2022. Data from 2000.
    """
    h = _btsx(health)
    h = h[h["YEAR (DISPLAY)"] >= 2000]

    MULTI_CODES = [
        ("Stunting prevalence (%)",       "NUTSTUNTINGPREV",                "#ff595e"),
        ("Anaemia in children (%)",       "NUTRITION_ANAEMIA_CHILDREN_PREV","#ffca3a"),
        ("Infant mortality (per 1,000)",  "MDG_0000000001",                 "#1982c4"),
        ("Under-5 mortality (per 1,000)", "MDG_0000000007",                 "#6a4c93"),
    ]

    from plotly.subplots import make_subplots as _msp
    fig = _msp(
        rows=2, cols=2,
        subplot_titles=[t for t, _, _ in MULTI_CODES],
        vertical_spacing=0.14,
        horizontal_spacing=0.10,
    )
    for (title, code, color), (row, col) in zip(MULTI_CODES, [(1,1),(1,2),(2,1),(2,2)]):
        df_m = (
            h[h["GHO (CODE)"] == code][["YEAR (DISPLAY)", "Numeric"]]
            .dropna().sort_values("YEAR (DISPLAY)")
        )
        if df_m.empty:
            continue
        fig.add_trace(go.Scatter(
            x=df_m["YEAR (DISPLAY)"], y=df_m["Numeric"],
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=4),
            showlegend=False,
            hovertemplate="<b>%{x}</b><br>%{y:.2f}<extra></extra>",
        ), row=row, col=col)
        yr_min_m = int(df_m["YEAR (DISPLAY)"].min())
        yr_max_m = int(df_m["YEAR (DISPLAY)"].max())
        if yr_min_m <= 2020 <= yr_max_m:
            fig.add_vrect(
                x0=2020, x1=min(2022, yr_max_m),
                fillcolor=COLORS["warning"], opacity=0.07,
                line_width=0, row=row, col=col,
            )
    fig.update_xaxes(dtick=5, showgrid=False)
    fig.update_yaxes(gridcolor="#EEF1F5")
    fig.update_layout(
        **_BASE, height=520,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig.to_json()


def _fig_slope(health):
    """Slope chart: each indicator has two points (2019 vs latest year),
    color-coded by direction (green = improved, red = worsened).
    """
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
        rows.append(dict(
            indicator=short,
            v_pre=float(base["Numeric"]),
            y_pre=int(base["YEAR (DISPLAY)"]),
            v_post=float(latest["Numeric"]),
            y_post=int(latest["YEAR (DISPLAY)"]),
        ))
    if not rows:
        fig = go.Figure(); fig.update_layout(**_BASE, height=360)
        return fig.to_json()

    fig = go.Figure()
    for r in rows:
        improved = r["v_post"] < r["v_pre"]
        col = "#8ac926" if improved else "#ff595e"
        fig.add_trace(go.Scatter(
            x=[r["y_pre"], r["y_post"]],
            y=[r["v_pre"], r["v_post"]],
            mode="lines+markers+text",
            name=r["indicator"],
            line=dict(color=col, width=2.2),
            marker=dict(size=8, color=col, line=dict(color="white", width=1)),
            text=["", r["indicator"]],
            textposition="middle right",
            textfont=dict(family="DM Sans, sans-serif", size=11, color=col),
            hovertemplate=(
                "<b>" + r["indicator"] + "</b><br>"
                "%{x}: %{y:.1f}<extra></extra>"
            ),
            showlegend=False,
        ))
    fig.update_layout(
        **_BASE, height=440, margin=dict(l=60, r=160, t=24, b=48),
        xaxis=dict(title="", showgrid=False, tickmode="array",
                   tickvals=[min(r["y_pre"] for r in rows),
                             max(r["y_post"] for r in rows)],
                   ticktext=[str(min(r["y_pre"] for r in rows)),
                             str(max(r["y_post"] for r in rows))]),
        yaxis=dict(title="Indicator value", gridcolor="#EEF1F5"),
        hovermode="closest",
    )
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
        fig.add_vline(x=yr, line_dash="dash", line_color=PALETTE[1], line_width=1.5)
        fig.add_annotation(x=yr, y=y_paper, xref="x", yref="paper",
                           text=lbl, showarrow=False,
                           font=dict(size=10, color=PALETTE[1], family="DM Sans, sans-serif"),
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
# Health indicator registry (used by data builder + section renderer)
# =============================================================================

_ALL_HEALTH_INDICATORS = [
    ("Stunting (%)",           "NUTSTUNTINGPREV",                    "#ff595e"),
    ("Anaemia – Children","NUTRITION_ANAEMIA_CHILDREN_PREV",    "#ffca3a"),
    ("Infant Mortality",       "MDG_0000000001",                     "#1982c4"),
    ("Under-5 Mortality",      "MDG_0000000007",                     "#6a4c93"),
    ("Wasting (%)",            "NUTRITION_WH_2",                     "#8ac926"),
    ("Underweight (%)",        "NUTRITION_WA_2",                     "#46dff7"),
    ("Neonatal Mortality",     "WHOSIS_000003",                      "#ff89a6"),
]
_INITIAL_ACTIVE = {"NUTSTUNTINGPREV", "NUTRITION_ANAEMIA_CHILDREN_PREV",
                   "MDG_0000000001", "MDG_0000000007"}


# =============================================================================
# Raw-data builders (embed JSON for JS-driven filters)
# =============================================================================

def _build_food_data(prices, basket):
    prices = _rebase_price_index(prices)
    df = (
        prices[prices["commodity"].isin(BASKET)]
        .groupby(["date", "commodity"], as_index=False)["price_index"]
        .mean()
        .sort_values("date")
    )
    df["ym"] = df["date"].dt.strftime("%Y-%m")

    commodities = sorted(BASKET)
    palette = {c: PALETTE[i % len(PALETTE)] for i, c in enumerate(commodities)}

    by_comm = {}
    for comm in BASKET:
        sub = df[df["commodity"] == comm][["ym", "price_index"]].dropna()
        by_comm[comm] = [
            {"ym": row["ym"], "idx": round(float(row["price_index"]), 2)}
            for _, row in sub.iterrows()
        ]

    all_years = sorted(int(y) for y in df["date"].dt.year.unique())

    lbp_m = monthly_basket_lbp(basket)
    usd_m = monthly_basket_usd(basket)
    lbp_data = [{"ym": r["year_month"], "price": round(float(r["price"]), 2)}
                for _, r in lbp_m.iterrows()]
    usd_data = [{"ym": r["year_month"], "usdprice": round(float(r["usdprice"]), 4)}
                for _, r in usd_m.iterrows()]

    return json.dumps({
        "commodities": commodities,
        "palette": palette,
        "byComm": by_comm,
        "basket": {"lbp": lbp_data, "usd": usd_data},
        "years": all_years,
    })


def _build_ipc_data(ipc_geo, prices):
    geo = ipc_geo.copy()
    geo["gov"] = geo["admin1_normalized"].map(_IPC_TO_GOV)

    unique_dates = sorted(geo["analysis_date"].dt.strftime("%Y-%m-%d").unique())
    by_date = {}

    for date_str in unique_dates:
        date_ts = pd.Timestamp(date_str)
        snap = geo[geo["analysis_date"] == date_ts].copy()

        # Choropleth: gov -> phase3+ pct
        choro_df = (
            snap.dropna(subset=["gov"])
            .groupby("gov", as_index=False)
            .agg(phase3_pct=("Phase 3+ percentage current", "mean"))
        )
        choro_df["z"] = (choro_df["phase3_pct"] * 100).round(1)
        ml_row = choro_df[choro_df["gov"] == "Mount Lebanon"]
        if not ml_row.empty:
            kj = ml_row.copy(); kj["gov"] = "Keserwan-Jbeil"
            choro_df = pd.concat([choro_df, kj], ignore_index=True)

        # IPC bar: stacked phases per gov
        agg_cols = {col: "mean" for col, _ in _PHASE_COLS.values()}
        bar_df = (
            snap.dropna(subset=["gov"])
            .groupby("gov", as_index=False)
            .agg(agg_cols)
        )
        bar_df["phase3plus"] = bar_df[[
            "Phase 3 percentage current",
            "Phase 4 percentage current",
            "Phase 5 percentage current",
        ]].sum(axis=1)
        bar_df = bar_df.sort_values("phase3plus", ascending=False)

        phases = [
            {"name": pname, "color": color,
             "y": [round(float(v) * 100, 1) for v in bar_df[col].fillna(0)]}
            for pname, (col, color) in _PHASE_COLS.items()
        ]

        # Gov basket bar for this year
        yr = date_ts.year
        yr_p = prices[prices["commodity"].isin(BASKET) & (prices["date"].dt.year == yr)]
        if not yr_p.empty:
            gp = yr_p.groupby("admin1")["usdprice"].mean().reset_index()
            gp = gp.sort_values("usdprice", ascending=True)
            gov_bar = {"govs": gp["admin1"].tolist(),
                       "y": [round(float(v), 2) for v in gp["usdprice"]]}
        else:
            gov_bar = {"govs": [], "y": []}

        def _clean(v):
            return None if (v is None or (isinstance(v, float) and (v != v))) else v

        by_date[date_str] = {
            "choro": {
                "locations": choro_df["gov"].tolist(),
                "z": [_clean(v) for v in choro_df["z"].tolist()],
            },
            "ipcBar": {"govs": bar_df["gov"].tolist(), "phases": phases},
            "govBar": gov_bar,
            "year": yr,
        }

    return json.dumps({"dates": unique_dates, "byDate": by_date})


def _build_health_data(health):
    h = _btsx(health)
    indicators = {}
    for name, code, color in _ALL_HEALTH_INDICATORS:
        dfc = (
            h[h["GHO (CODE)"] == code][["YEAR (DISPLAY)", "Numeric"]]
            .dropna()
            .groupby("YEAR (DISPLAY)", as_index=False)["Numeric"].mean()
            .sort_values("YEAR (DISPLAY)")
        )
        if dfc.empty:
            continue
        indicators[code] = {
            "name": name, "color": color,
            "years": [int(y) for y in dfc["YEAR (DISPLAY)"]],
            "values": [round(float(v), 3) for v in dfc["Numeric"]],
        }
    return json.dumps({"indicators": indicators})


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
    exrate = d["exrate"]
    spread_json = _fig_fx_spread(wdi, exrate)
    rem_lbn = wdi[(wdi["Country Name"] == "Lebanon") & (wdi["Series Code"] == SERIES["remittances"])]
    if not rem_lbn.empty:
        rem_latest_row = rem_lbn.sort_values("Year").iloc[-1]
        rem_latest_pct = float(rem_latest_row["Value"])
        rem_latest_year = int(rem_latest_row["Year"])
    else:
        rem_latest_pct, rem_latest_year = 0.0, 0
    remittances_json = _fig_remittances(wdi)
    gdp_json   = _fig_gdp_rate(wdi)
    heat_json  = _fig_inflation_heatmap(wdi)
    gdp_pc_json = _fig_gdp_pc_line(wdi)

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
        '<div class="g2">'
        '<div class="chart-card" style="margin-bottom:0">'
        '<div class="chart-title">GDP &amp; Official Exchange Rate &mdash; Lebanon</div>'
        '<div class="chart-caption">Left axis: GDP in USD billions &middot; '
        'Right axis: Official LBP per USD (World Bank)</div>'
        + _plot_tag("gdp_rate", gdp_json) +
        '</div>'
        '<div class="chart-card" style="margin-bottom:0">'
        '<div class="chart-title">Official vs Unofficial Exchange Rate &mdash; The "Two Lebanons"</div>'
        '<div class="chart-caption">Y axis is logarithmic so the gap is readable across the full range. '
        'The shaded gap between the two lines <strong>is</strong> the crisis &mdash; '
        'at its peak, market traders charged ~50x the official rate.</div>'
        + _plot_tag("fx_spread", spread_json) +
        '</div>'
        '</div>'
        '<div class="chart-card">'
        '<div class="chart-title">Personal Remittances &mdash; % of GDP</div>'
        '<div class="chart-caption">In ' + str(rem_latest_year) + ', remittances equalled '
        '<strong>' + "{:.1f}%".format(rem_latest_pct) + '</strong> of Lebanon\'s GDP &mdash; '
        'among the highest in the world. The diaspora is what kept Lebanon from total collapse.</div>'
        + _plot_tag("remittances", remittances_json) +
        '</div>'
        '<div class="chart-card">'
        '<div class="chart-title">Inflation Heatmap &mdash; Country &times; Year</div>'
        '<div class="chart-caption">Each cell shows the annual inflation rate from 2015 onwards. '
        'A diverging green&ndash;to&ndash;red scale anchors at 0%: green = deflation, '
        'near&ndash;white = stable, red = high inflation (capped at 300% so Lebanon&rsquo;s 221% '
        'peak reads clearly). Hover for exact values.</div>'
        + _plot_tag("inflation_heatmap", heat_json) +
        '</div>'
        '<div class="chart-card">'
        '<div class="chart-title">GDP per Capita &mdash; Country Comparison</div>'
        '<div class="chart-caption">Annual GDP per capita in USD, 2015 onwards. '
        "Lebanon's collapse from ~$8k to under $4k stands out against peer trajectories. "
        'Country colours follow the project palette and stay consistent across all charts. '
        'Source: World Bank WDI &middot; NY.GDP.PCAP.CD.</div>'
        + _plot_tag("gdp_pc", gdp_pc_json) +
        '</div>'
        '<p class="source-line">Sources: World Bank WDI &middot; FP.CPI.TOTL.ZG '
        '&middot; NY.GDP.MKTP.CD &middot; PA.NUS.FCRF &middot; NY.GDP.PCAP.CD</p>'
        '</section>'
    )


def _section_food(d):
    prices = d["prices"]
    basket = d["basket"]
    exrate = d["exrate"]
    wdi    = d["wdi"]

    idx_json             = _fig_price_index(prices)
    discrepancy_json     = _fig_price_discrepancy(basket, wdi)
    scat_json, r, r2, n  = _fig_scatter(basket, exrate)
    food_choro_json      = _fig_food_price_choropleth(prices)
    dist_treemap_json    = _fig_price_treemap_districts(prices)
    food_json            = _build_food_data(prices, basket)

    # --- Stacked bar: governorate order + multi-year data -------------------
    _df22_bar = prices[
        (prices["date"].dt.year == 2022) &
        (prices["commodity"].isin(_GOVS_COMMON_COMMS))
    ].dropna(subset=["price"])
    _bar22 = _df22_bar.groupby(["admin1", "commodity"], as_index=False)["price"].mean()
    gov_order = (
        _bar22[_bar22["commodity"].isin(_GOVS_DEFAULT_COMMS)]
        .groupby("admin1")["price"].sum()
        .sort_values(ascending=False).index.tolist()
    )
    for _g in sorted(_bar22["admin1"].unique()):
        if _g not in gov_order:
            gov_order.append(_g)

    by_year: dict = {}
    for _yr in range(2018, 2025):
        _yrdf = prices[
            (prices["date"].dt.year == _yr) &
            (prices["commodity"].isin(_GOVS_COMMON_COMMS))
        ].dropna(subset=["price"])
        _grp = _yrdf.groupby(["commodity", "admin1"])["price"].mean()
        _yrdata: dict = {}
        for _c in _GOVS_COMMON_COMMS:
            _yrdata[_c] = {
                _g: (round(float(_grp.get((_c, _g), 0) or 0))
                     if (_c, _g) in _grp.index else 0)
                for _g in gov_order
            }
        by_year[str(_yr)] = _yrdata

    gov_bar_data = {
        "comms": _GOVS_COMMON_COMMS,
        "govOrder": gov_order,
        "byYear": by_year,
    }
    stacked_bar_json = _fig_stacked_bar_govs(prices, gov_order)

    # Year range options — default span 2018-2023 (matches the price-index chart)
    all_years = sorted(int(y) for y in
                       prices[prices["commodity"].isin(BASKET)]["date"].dt.year.unique())
    default_min = 2018 if 2018 in all_years else all_years[0]
    default_max = 2023 if 2023 in all_years else all_years[-1]
    yr_min_opts = "".join(
        '<option value="' + str(y) + '"' + (' selected' if y == default_min else '') + '>'
        + str(y) + '</option>' for y in all_years)
    yr_max_opts = "".join(
        '<option value="' + str(y) + '"' + (' selected' if y == default_max else '') + '>'
        + str(y) + '</option>' for y in all_years)

    # Commodity checkboxes
    comm_checks = ""
    for comm in sorted(BASKET):
        short = comm.split("(")[0].strip() if "(" in comm else comm
        comm_checks += (
            '<label class="comm-lbl">'
            '<input type="checkbox" class="comm-cb" value="' + comm + '" checked> '
            + short + '</label>'
        )

    filter_bar = (
        '<div class="filter-bar">'
        '<div class="filter-group">'
        '<span class="filter-label">Commodities</span>'
        '<div class="comm-checks">' + comm_checks + '</div>'
        '</div>'
        '<div class="filter-group">'
        '<span class="filter-label">Year Range</span>'
        '<select id="yr-min" class="flt-select">' + yr_min_opts + '</select>'
        '<span style="font-size:11px;color:var(--muted)">to</span>'
        '<select id="yr-max" class="flt-select">' + yr_max_opts + '</select>'
        '</div>'
        '</div>'
    )

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
        '<script type="application/json" id="food-data">' + food_json + '</script>'
        '<div class="section-meta">'
        '<span class="section-tag">Act 2</span>'
        '<span class="section-eyebrow">2012 &ndash; 2026</span>'
        '</div>'
        '<h2 class="section-title">Food Price Transmission</h2>'
        '<p class="section-sub">How Lebanon\'s currency collapse drove staple food prices '
        'beyond reach &mdash; tracked through WFP market data across six basket commodities.</p>'
        '<div class="chart-card">'
        '<div class="chart-title">Food Prices Relative to 2019 &mdash; How Far They&rsquo;ve Climbed</div>'
        '<div class="chart-caption">Each line shows the monthly price of a basket commodity '
        'normalized so its 2019 average equals 100. A reading of <strong>500</strong> means the '
        'commodity costs 5&times; its 2019 level; <strong>200</strong> means it has doubled. '
        'Default view covers 2018&ndash;2023 &mdash; widen the range below to explore the full WFP series.</div>'
        + filter_bar +
        _plot_tag("price_index", idx_json) +
        '</div>'
        '<div class="chart-card">'
        '<div class="chart-title">The Hidden Food Price Gap &mdash; Official Rate vs Market Reality</div>'
        '<div class="chart-caption">The same LBP basket price divided by two different exchange rates tells '
        'opposite stories. At the official peg (dotted), the basket appeared enormously expensive in USD '
        'because LBP market prices surged while the denominator barely moved. At the market rate (solid), '
        'the USD cost also rose &mdash; confirming real purchasing-power loss beyond just currency devaluation. '
        'WFP&rsquo;s reported USD prices use the parallel market rate.</div>'
        + _plot_tag("discrepancy", discrepancy_json) +
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
        '<div class="chart-card">'
        '<script type="application/json" id="gov-bar-comms">'
        + json.dumps(gov_bar_data) +
        '</script>'
        '<div class="chart-title">Food Prices by Governorate &amp; Commodity</div>'
        '<div class="chart-caption">Average LBP price per commodity per governorate for the selected year. '
        'Each commodity is priced at its <strong>standard package size</strong> (shown in legend) &mdash; '
        'oil is 5 L, sugar is 5 kg, tea is 160 g, canned beef is 200 g. '
        'Bars reflect each item on its own scale; use the chart to compare each commodity <em>across regions</em>.</div>'
        '<div class="filter-bar" style="margin-bottom:6px">'
        '<span class="filter-label">Year</span>'
        '<div style="display:flex;gap:4px;flex-wrap:wrap">'
        + "".join(
            '<button class="ipc-btn gov-bar-yr-btn' + (' active' if yr == 2022 else '') + '" '
            'data-year="' + str(yr) + '" style="font-size:11px;padding:4px 10px">'
            + str(yr) + '</button>'
            for yr in range(2018, 2025)
        )
        + '</div></div>'
        '<div class="filter-bar" style="flex-wrap:wrap;row-gap:6px">'
        '<span class="filter-label">Commodities</span>'
        + "".join(
            '<label class="comm-lbl' + (' checked' if c in _GOVS_DEFAULT_COMMS else '') + '" '
            'style="font-size:11px;padding:3px 8px" title="per ' + _COMM_UNITS.get(c,'') + '">'
            '<input type="checkbox" class="gov-bar-cb" value="' + c + '"'
            + (' checked' if c in _GOVS_DEFAULT_COMMS else '') + '> '
            + _short_comm(c)
            + ' <span style="font-size:9px;color:#888">(' + _COMM_UNITS.get(c,'') + ')</span>'
            + '</label>'
            for c in _GOVS_COMMON_COMMS
        )
        + '</div>'
        + _plot_tag("stacked_bar_govs", stacked_bar_json) +
        '</div>'
        '<div class="chart-card">'
        '<div class="chart-title">Average Commodity Price by Governorate &mdash; 2022</div>'
        '<div class="chart-caption">Average USD price across all commodities surveyed by WFP in 2022. '
        'Darker = pricier governorate.</div>'
        + _plot_tag("food_choro", food_choro_json) +
        '</div>'
        '<div class="chart-card">'
        '<div class="chart-title">Average Commodity Price by District &mdash; 2022</div>'
        '<div class="chart-caption">26 districts nested inside 8 governorates. '
        'Tile area encodes average USD price across all commodities in 2022 &mdash; '
        'larger tile = pricier district. Each governorate has its own distinct colour; '
        'districts within it share that colour.</div>'
        + _plot_tag("dist_treemap", dist_treemap_json) +
        '</div>'
        '<p class="source-line">Sources: WFP VAM Food Price Monitoring '
        '&middot; Unofficial exchange rate from WFP parallel market data</p>'
        '</section>'
    )


def _section_insecurity(d):
    geo     = d["ipc_geo"].copy()
    ipc_pop = d["ipc_pop"]
    prices  = d["prices"]
    unhcr   = d["unhcr"]

    geo["gov"] = geo["admin1_normalized"].map(_IPC_TO_GOV)

    latest_date   = geo["analysis_date"].max()
    geo_snap      = geo[geo["analysis_date"] == latest_date].copy()
    snap_label    = latest_date.strftime("%B %Y")
    selected_year = latest_date.year

    choro_json    = _fig_choropleth(geo_snap)
    donut_json    = _fig_donut(ipc_pop)
    ipc_bar_json  = _fig_ipc_bar(geo_snap)
    gov_bar_json  = _fig_gov_bar(prices, selected_year)
    treemap_a_json = _fig_treemap_insecurity(geo_snap, ipc_pop)
    unhcr_json    = _fig_unhcr_choropleth(unhcr)
    ipc_data_json = _build_ipc_data(d["ipc_geo"], prices)

    unique_dates = sorted(d["ipc_geo"]["analysis_date"].unique())
    date_buttons = ""
    for dt in unique_dates:
        ts = pd.Timestamp(dt)
        date_str = ts.strftime("%Y-%m-%d")
        label    = ts.strftime("%b %Y")
        active   = ts == latest_date
        date_buttons += (
            '<button class="ipc-btn' + (' active' if active else '') + '" '
            'data-date="' + date_str + '">' + label + '</button>'
        )

    ipc_filter = (
        '<div class="filter-bar">'
        '<div class="filter-group">'
        '<span class="filter-label">Snapshot Date</span>'
        '<div class="ipc-btns">' + date_buttons + '</div>'
        '</div>'
        '<span style="font-size:11px;color:var(--muted)">'
        'Showing: <b id="ipc-snap-label">' + snap_label + '</b>'
        '</span>'
        '</div>'
    )

    return (
        '<section id="s-insecurity">'
        '<script type="application/json" id="ipc-data">' + ipc_data_json + '</script>'
        '<div class="section-meta">'
        '<span class="section-tag">Act 2 Extended</span>'
        '<span class="section-eyebrow">Snapshot: ' + snap_label + '</span>'
        '</div>'
        '<h2 class="section-title">Who Suffers Most</h2>'
        '<p class="section-sub">IPC food insecurity phases broken down by governorate, '
        'population group, and over time. Select a snapshot date to update charts that '
        'support filtering.</p>'
        + ipc_filter +
        # Row 1: IPC choropleth | UNHCR refugees choropleth
        '<div class="g2">'
        '<div class="chart-card" style="margin-bottom:0">'
        '<div class="chart-title">IPC Phase 3+ by Governorate</div>'
        '<div class="chart-caption">Share of population in acute food insecurity. '
        'Darker = more severe.</div>'
        + _plot_tag("choropleth", choro_json) +
        '</div>'
        '<div class="chart-card" style="margin-bottom:0">'
        '<div class="chart-title">Registered Syrian Refugees by Governorate</div>'
        '<div class="chart-caption">Lebanon hosts the world\'s highest per-capita refugee '
        'population. Source: UNHCR Lebanon Operational Data (demo estimates).</div>'
        + _plot_tag("unhcr_choropleth", unhcr_json) +
        '</div>'
        '</div>'
        '<div style="margin-bottom:22px"></div>'
        # Row 2: Treemap A | Donut (standalone, full-height)
        '<div class="g2">'
        '<div class="chart-card" style="margin-bottom:0">'
        '<div class="chart-title">Phase 3+ Headcount &mdash; Governorate &times; Group</div>'
        '<div class="chart-caption">Treemap of estimated Phase 3+ population. '
        'Tile area is proportional to absolute number of people. '
        '<em>Note:</em> assumes latest national group composition applies uniformly '
        'across governorates (the IPC surveys are independent).</div>'
        + _plot_tag("treemap_a", treemap_a_json) +
        '</div>'
        '<div class="chart-card" style="margin-bottom:0">'
        '<div class="chart-title">Phase 3+ by Population Group</div>'
        '<div class="chart-caption">Share of people in acute food insecurity (IPC Phase 3+) '
        'by population group, at the most recent available survey per group. '
        'Hover for headcounts and exact survey date.</div>'
        + _plot_tag("donut", donut_json) +
        '</div>'
        '</div>'
        '<div style="margin-bottom:22px"></div>'
        # Row 3: IPC stacked bar
        '<div class="chart-card">'
        '<div class="chart-title">IPC Phase Distribution by Governorate</div>'
        '<div class="chart-caption">Stacked bars &mdash; % of analysed population '
        'in each IPC phase. Sorted by Phase 3+ share.</div>'
        + _plot_tag("ipc_bar", ipc_bar_json) +
        '</div>'
        # Row 4: Gov basket bar
        '<div class="chart-card">'
        '<div class="chart-title">Avg Basket Price by Governorate &mdash; '
        '<span id="gov-bar-year">' + str(selected_year) + '</span></div>'
        '<div class="chart-caption">Average USD price of basket commodities per governorate.</div>'
        + _plot_tag("gov_bar", gov_bar_json) +
        '</div>'
        '<p class="source-line">Sources: IPC Global Platform '
        '&middot; WFP VAM Food Price Monitoring</p>'
        '</section>'
    )


def _section_health(d):
    health = d["health"]
    basket = d["basket"]
    u5mort = d["u5mort"]

    lag_json      = _fig_lag(basket, health)
    small_json    = _fig_small_multiples(health)
    db_json       = _fig_dumbbell(health)
    mena_json     = _fig_mena(u5mort)
    health_json   = _build_health_data(health)

    # Indicator pills
    h = _btsx(health)
    pills = ""
    for name, code, color in _ALL_HEALTH_INDICATORS:
        has_data = not h[h["GHO (CODE)"] == code]["Numeric"].dropna().empty
        if not has_data:
            continue
        active = code in _INITIAL_ACTIVE
        pills += (
            '<button class="health-pill' + (' active' if active else '') + '" '
            'data-code="' + code + '" '
            'style="' + ('border-color:' + color + ';background:' + color + '18;color:var(--navy);' if active else '') + '">'
            + name + '</button>'
        )

    explorer_filter = (
        '<div class="filter-bar">'
        '<span class="filter-label">Indicators (toggle to compare)</span>'
        '<div class="health-pills">' + pills + '</div>'
        '</div>'
    )

    return (
        '<section id="s-health">'
        '<script type="application/json" id="health-data">' + health_json + '</script>'
        '<div class="section-meta">'
        '<span class="section-tag">Act 3</span>'
        '<span class="section-eyebrow">2000 &ndash; 2024</span>'
        '</div>'
        '<h2 class="section-title">The Health Toll</h2>'
        '<p class="section-sub">Stunting, wasting, anaemia, and mortality in Lebanon &mdash; '
        'with a lagged view against food price shocks. The crisis is still unfolding: '
        'nutrition indicators worsen years after the price shock.</p>'
        '<div class="chart-card">'
        '<div class="chart-title">Health Indicator Explorer</div>'
        '<div class="chart-caption">All indicators normalized to 2000&nbsp;=&nbsp;100 for side-by-side '
        'comparison. Toggle the pills to show or hide indicators.</div>'
        + explorer_filter +
        '<div id="plot-health_explorer" class="plot-container" style="min-height:380px"></div>'
        '</div>'
        '<div class="chart-card">'
        '<div class="chart-title">Key Nutrition &amp; Mortality Trends</div>'
        '<div class="chart-caption">Model-based estimates &middot; Both sexes &middot; '
        'Lebanon (LBN) &middot; Data from 2000. Shaded region: 2020&ndash;2022 crisis window.</div>'
        + _plot_tag("small_multiples", small_json) +
        '</div>'
        '<div class="chart-card">'
        '<div class="chart-title">Food Prices vs Stunting Prevalence &mdash; Lag View</div>'
        '<div class="chart-caption">Top: Monthly basket price index (2019=100) &middot; '
        'Bottom: Annual stunting prevalence %. '
        'Shaded band highlights the 2020&ndash;2022 crisis window.</div>'
        + _plot_tag("lag", lag_json) +
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
