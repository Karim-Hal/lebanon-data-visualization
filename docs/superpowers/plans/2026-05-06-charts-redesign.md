# Charts Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the chart redesign per `docs/superpowers/specs/2026-05-06-charts-redesign-design.md` — adding 9 new charts, removing 3 redundant ones, and modifying 2, including ingestion of two new datasets (remittances, UNHCR refugees).

**Architecture:** Single-file generator pattern preserved (`generate_report.py`). New chart builders are added as `_fig_*` functions; new data is loaded via `src/data_loader.py`. No new third-party dependencies. Existing 5-section structure unchanged.

**Tech Stack:** Python 3, pandas, plotly, scipy (already used), assertion-based sanity checks (existing project convention — no pytest).

**Note on testing:** This project has no pytest infrastructure; the existing convention is `scripts/sanity_check.py` (assertion-based). For data tasks, this plan extends `sanity_check.py`. For chart tasks, it adds a new `scripts/chart_smoke.py` that asserts each new figure produces valid Plotly JSON with the expected trace count and shape. Visual correctness is verified by regenerating `report.html` and inspecting in a browser.

**Note on commits:** Commit steps are listed for guidance but defer to the user's preference at execution time.

---

## File map

**Modified:**
- `generate_report.py` — add new `_fig_*` builders, remove 3, modify 2, update section renderers
- `src/data_loader.py` — add `load_remittances()` and `load_unhcr_refugees()` helpers
- `src/config.py` — add `BASKET_CATEGORIES` mapping and extend `SERIES` dict
- `data/wdi_long.csv` — append remittances rows for 6 countries
- `scripts/sanity_check.py` — add checks for remittances + UNHCR data

**Created:**
- `data/unhcr_refugees_lebanon.csv` — new file
- `scripts/chart_smoke.py` — new lightweight chart-smoke runner

---

## Task 1: Acquire remittances data

**Files:**
- Modify: `data/wdi_long.csv`
- Modify: `src/config.py`
- Modify: `scripts/sanity_check.py`

- [ ] **Step 1.1: Download remittances data from World Bank**

Open https://data.worldbank.org/indicator/BX.TRF.PWKR.DT.GD.ZS in a browser. Click "Download → CSV". The download contains a CSV with all countries; we need 6 specific rows.

Alternative (preferred — direct API):
```bash
curl "https://api.worldbank.org/v2/country/LBN;JOR;EGY;SYR;SAU;ARE/indicator/BX.TRF.PWKR.DT.GD.ZS?format=json&per_page=1000&date=2000:2024" -o /tmp/remittances.json
```

- [ ] **Step 1.2: Append remittance rows to `data/wdi_long.csv`**

The existing CSV columns are: `Country Name, Country Code, Series Name, Series Code, YearLabel, Value, Year`.

Write a one-time helper script and run it (then delete the script):

```python
# tmp_append_remittances.py
import json
import pandas as pd

with open("/tmp/remittances.json") as f:
    payload = json.load(f)

# WB API returns [metadata, [rows]]
rows = payload[1]
out = []
for r in rows:
    if r["value"] is None:
        continue
    out.append({
        "Country Name": r["country"]["value"],
        "Country Code": r["countryiso3code"],
        "Series Name": "Personal remittances, received (% of GDP)",
        "Series Code": "BX.TRF.PWKR.DT.GD.ZS",
        "YearLabel": f'{r["date"]} [YR{r["date"]}]',
        "Value": float(r["value"]),
        "Year": int(r["date"]),
    })

# Country-name normalization to match existing wdi_long.csv naming
NAME_MAP = {
    "Egypt, Arab Rep.": "Egypt, Arab Rep.",
    "Egypt": "Egypt, Arab Rep.",
    "Syrian Arab Republic": "Syrian Arab Republic",
}
df_new = pd.DataFrame(out)
df_new["Country Name"] = df_new["Country Name"].replace(NAME_MAP)

df_existing = pd.read_csv("data/wdi_long.csv")
df_combined = pd.concat([df_existing, df_new], ignore_index=True)
df_combined.to_csv("data/wdi_long.csv", index=False)
print(f"Added {len(df_new)} remittance rows.")
```

Run: `python tmp_append_remittances.py`
Expected output: `Added 60+ remittance rows.` (years × countries)
Then delete `tmp_append_remittances.py`.

- [ ] **Step 1.3: Add `remittances` to `SERIES` in `src/config.py`**

Modify `src/config.py` lines 83-88:

```python
SERIES = {
    "inflation":    "FP.CPI.TOTL.ZG",
    "gdp":          "NY.GDP.MKTP.CD",
    "gdp_pc":       "NY.GDP.PCAP.CD",
    "official_fx":  "PA.NUS.FCRF",
    "remittances":  "BX.TRF.PWKR.DT.GD.ZS",
}
```

- [ ] **Step 1.4: Add sanity check for remittances**

Append to `scripts/sanity_check.py` (after the existing `WDI_SERIES = {...}` definition, append the new code at the bottom of the WDI check function or as a new check function):

```python
def check_remittances():
    path = DATA / "wdi_long.csv"
    df = pd.read_csv(path)
    rem = df[df["Series Code"] == "BX.TRF.PWKR.DT.GD.ZS"]
    assert not rem.empty, "Remittance series BX.TRF.PWKR.DT.GD.ZS missing from wdi_long.csv"
    countries = set(rem["Country Name"].unique())
    assert "Lebanon" in countries, f"Lebanon missing from remittance rows. Found: {countries}"
    lbn = rem[rem["Country Name"] == "Lebanon"]
    assert lbn["Year"].between(2010, 2024).any(), "No Lebanon remittance values in 2010-2024 range"
```

Then register it in the `if __name__ == "__main__":` block:
```python
run("remittances", check_remittances)
```

- [ ] **Step 1.5: Run sanity check**

Run: `python scripts/sanity_check.py`
Expected: `remittances` row shows ✅ PASS.

- [ ] **Step 1.6: Commit**

```bash
git add data/wdi_long.csv src/config.py scripts/sanity_check.py
git commit -m "data: add World Bank remittances series (BX.TRF.PWKR.DT.GD.ZS) for 6 MENA countries"
```

---

## Task 2: Acquire UNHCR refugee data

**Files:**
- Create: `data/unhcr_refugees_lebanon.csv`
- Modify: `src/data_loader.py`
- Modify: `scripts/sanity_check.py`

- [ ] **Step 2.1: Locate the latest UNHCR Lebanon governorate snapshot**

Open https://data.unhcr.org/en/country/lbn — look under "Documents" or "Statistics" for the latest "Registered Syrian Refugees by Governorate" infographic or CSV. As of writing, the latest figures are typically published as a quarterly snapshot.

If a CSV download is available, save it to `/tmp/unhcr_raw.csv`.

If only an infographic is available, transcribe values manually. Lebanon's eight governorates are: `Akkar`, `Baalbek-El Hermel`, `Beirut`, `Bekaa`, `El Nabatieh`, `Mount Lebanon`, `North`, `South`. UNHCR may publish at a different administrative granularity (e.g., merged Beirut + Mount Lebanon); aggregate as needed.

- [ ] **Step 2.2: Create `data/unhcr_refugees_lebanon.csv`**

Schema (must match `admin1_normalized` from `ipc_geo`):
```csv
governorate,registered_refugees,as_of_date
Akkar,<n>,YYYY-MM-DD
Baalbek-El Hermel,<n>,YYYY-MM-DD
Beirut,<n>,YYYY-MM-DD
Bekaa,<n>,YYYY-MM-DD
El Nabatieh,<n>,YYYY-MM-DD
Mount Lebanon,<n>,YYYY-MM-DD
North,<n>,YYYY-MM-DD
South,<n>,YYYY-MM-DD
```

All 8 rows required. `as_of_date` is the same value across all rows (the snapshot date).

- [ ] **Step 2.3: Add `load_unhcr_refugees()` to `src/data_loader.py`**

Add after `load_u5mort_mena()`:

```python
@st.cache_data
def load_unhcr_refugees() -> pd.DataFrame:
    df = pd.read_csv(DATA / "unhcr_refugees_lebanon.csv", parse_dates=["as_of_date"])
    df["registered_refugees"] = pd.to_numeric(df["registered_refugees"], errors="coerce").astype("Int64")
    return df
```

- [ ] **Step 2.4: Add sanity check for UNHCR**

Append to `scripts/sanity_check.py`:

```python
def check_unhcr():
    path = DATA / "unhcr_refugees_lebanon.csv"
    assert path.exists(), f"File not found: {path}"
    df = pd.read_csv(path, parse_dates=["as_of_date"])
    govs = set(df["governorate"].unique())
    assert govs == ADMIN1_NORMALIZED, (
        f"UNHCR governorates do not match IPC admin1_normalized. "
        f"Missing: {ADMIN1_NORMALIZED - govs}. Extra: {govs - ADMIN1_NORMALIZED}."
    )
    assert df["registered_refugees"].notna().all(), "UNHCR rows have missing counts"
    age_days = (pd.Timestamp.today() - df["as_of_date"].max()).days
    assert age_days < 365 * 3, f"UNHCR snapshot is older than 3 years (age: {age_days} days)"
```

Register: `run("unhcr_refugees", check_unhcr)`

- [ ] **Step 2.5: Run sanity check**

Run: `python scripts/sanity_check.py`
Expected: `unhcr_refugees` shows ✅ PASS.

- [ ] **Step 2.6: Commit**

```bash
git add data/unhcr_refugees_lebanon.csv src/data_loader.py scripts/sanity_check.py
git commit -m "data: add UNHCR Syrian refugees by Lebanese governorate"
```

---

## Task 3: Add `BASKET_CATEGORIES` mapping to config

**Files:**
- Modify: `src/config.py`

- [ ] **Step 3.1: Add `BASKET_CATEGORIES` after `BASKET`**

Insert in `src/config.py` after line 67:

```python
# ---------------------------------------------------------------------------
# Basket commodity → category mapping (for Treemap B)
# ---------------------------------------------------------------------------
BASKET_CATEGORIES = {
    "Bread (pita)":                  "Cereals",
    "Wheat flour":                   "Cereals",
    "Rice (imported, Egyptian)":     "Cereals",
    "Eggs":                          "Dairy & Eggs",
    "Meat (chicken, whole, frozen)": "Proteins",
    "Oil (sunflower)":               "Oils",
}
```

- [ ] **Step 3.2: Commit**

```bash
git add src/config.py
git commit -m "config: add BASKET_CATEGORIES mapping for treemap"
```

---

## Task 4: Bootstrap chart-smoke test runner

**Files:**
- Create: `scripts/chart_smoke.py`

- [ ] **Step 4.1: Create lightweight smoke runner**

```python
# scripts/chart_smoke.py
"""Lightweight smoke check for new chart figure builders.
Asserts each function returns valid Plotly JSON with expected structure.
Run: python scripts/chart_smoke.py
"""
import json
import sys
import traceback
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Stub streamlit before any src imports
from types import ModuleType
_st = ModuleType("streamlit")
_st.cache_data = lambda f: f
sys.modules["streamlit"] = _st

results = {}


def smoke(name, fn):
    try:
        fn()
        results[name] = ("✅", "PASS", "")
    except AssertionError as e:
        results[name] = ("❌", "FAIL", str(e))
    except Exception as e:
        results[name] = ("❌", "ERROR", f"{type(e).__name__}: {e}")
        traceback.print_exc()


def assert_valid_plotly_json(fig_json, expected_min_traces=1, label=""):
    obj = json.loads(fig_json)
    assert "data" in obj and "layout" in obj, f"{label}: missing data/layout"
    assert len(obj["data"]) >= expected_min_traces, (
        f"{label}: expected >= {expected_min_traces} traces, got {len(obj['data'])}"
    )


# Tests get registered here as new chart builders are added.

if __name__ == "__main__":
    if not results:
        print("(no smoke tests registered yet)")
        sys.exit(0)

    print(f"\n{'='*64}\nCHART SMOKE RESULTS\n{'='*64}")
    for name, (icon, status, msg) in results.items():
        print(f"{icon} {name:<32} {status}  {msg}")
    n_fail = sum(1 for _, s, _ in results.values() if s != "PASS")
    sys.exit(0 if n_fail == 0 else 1)
```

- [ ] **Step 4.2: Run it (no tests yet, should exit 0)**

Run: `python scripts/chart_smoke.py`
Expected: `(no smoke tests registered yet)` and exit code 0.

- [ ] **Step 4.3: Commit**

```bash
git add scripts/chart_smoke.py
git commit -m "test: bootstrap chart smoke runner"
```

---

## Task 5: Treemap B — Food Prices (Category → Commodity)

**Files:**
- Modify: `generate_report.py:823-873` (replace `_fig_treemap`)
- Modify: `scripts/chart_smoke.py`

- [ ] **Step 5.1: Replace `_fig_treemap` with category-based version**

In `generate_report.py`, find `def _fig_treemap(prices):` (around line 823) and replace the entire function body with:

```python
def _fig_treemap(prices):
    """Treemap of monthly basket cost share.
    Hierarchy: Category -> Commodity. Tile area = monthly cost contribution
    (equal-weighted basket: 1 unit per commodity x current USD price).
    Color = % change in price index since 2019.
    """
    from src.config import BASKET_CATEGORIES

    prices = _rebase_price_index(prices)
    df = (
        prices[prices["commodity"].isin(BASKET)]
        .dropna(subset=["price_index", "usdprice"])
        .sort_values("date")
        .groupby("commodity", as_index=False)
        .last()
    )
    df["category"]    = df["commodity"].map(BASKET_CATEGORIES).fillna("Other")
    df["short"]       = df["commodity"].str.split("(").str[0].str.strip()
    df["pct_change"]  = (df["price_index"] - 100).round(0).astype(int)
    # Equal-weighted basket: cost share proportional to current USD price
    df["cost_share"]  = df["usdprice"]

    fig = px.treemap(
        df,
        path=[px.Constant("Basket"), "category", "commodity"],
        values="cost_share",
        color="pct_change",
        color_continuous_scale=[
            [0.0, COLORS["card_bg"]],
            [0.5, PALETTE[1]],
            [1.0, COLORS["crisis_red"]],
        ],
        range_color=(0, max(300, int(df["pct_change"].max() or 0))),
        custom_data=["short", "price_index", "pct_change", "usdprice"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>+%{customdata[2]}% since 2019",
        textfont=dict(family="DM Sans, sans-serif", size=12, color="#FFFFFF"),
        marker_line_width=2,
        marker_line_color="white",
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Inflation since 2019: <b>+%{customdata[2]}%</b><br>"
            "Latest USD price: $%{customdata[3]:.2f}<br>"
            "Price index: %{customdata[1]:.0f} (2019=100)<extra></extra>"
        ),
    )
    fig.update_layout(
        **_BASE,
        height=380,
        margin=dict(l=10, r=10, t=10, b=10),
        coloraxis_colorbar=dict(title="% Δ since 2019", ticksuffix="%", len=0.7),
    )
    return fig.to_json()
```

- [ ] **Step 5.2: Update Food Prices section caption to reflect new chart**

In `generate_report.py`, find the Food Prices section's treemap card (around line 1733) and replace its caption block:

```python
'<div class="chart-card">'
'<div class="chart-title">Basket Cost Share &amp; Inflation</div>'
'<div class="chart-caption">Each tile represents one basket commodity, '
'grouped by food category. Tile area is proportional to current USD price '
'(equal-weighted basket). Colour shows percentage change in price index since 2019. '
'Larger tiles cost more today; redder tiles inflated more.</div>'
+ _plot_tag("treemap", treemap_json) +
'</div>'
```

- [ ] **Step 5.3: Add smoke check**

In `scripts/chart_smoke.py`, before the `if __name__ == "__main__":` block:

```python
def t_treemap_b():
    from generate_report import _fig_treemap
    from src.data_loader import load_wfp_prices
    j = _fig_treemap(load_wfp_prices())
    assert_valid_plotly_json(j, expected_min_traces=1, label="treemap_b")
    obj = json.loads(j)
    # Treemap = single trace
    assert obj["data"][0]["type"] == "treemap", "treemap_b: not a treemap"
    # Path includes 3 levels (root + category + commodity)
    labels = obj["data"][0].get("labels", [])
    assert len(labels) >= 6 + 4 + 1, f"treemap_b: too few tiles ({len(labels)})"

smoke("treemap_b", t_treemap_b)
```

- [ ] **Step 5.4: Run smoke + regenerate report**

Run: `python scripts/chart_smoke.py`
Expected: `treemap_b ✅ PASS`

Run: `python generate_report.py`
Expected: report.html written; open in browser and verify the Food Prices treemap shows category groupings (Cereals / Proteins / Dairy & Eggs / Oils) with commodities nested under each.

- [ ] **Step 5.5: Commit**

```bash
git add generate_report.py scripts/chart_smoke.py
git commit -m "feat(food): replace treemap with Category->Commodity cost-share view"
```

---

## Task 6: Shrink donut to companion size (M1)

**Files:**
- Modify: `generate_report.py` (function `_fig_donut`, layout call only)
- Modify: `generate_report.py` (Food Insecurity section renderer, layout grid)

This task only resizes the donut. It will be repositioned next to the population-group time series in Task 11. For now, keep it in its current slot but at smaller size.

- [ ] **Step 6.1: Reduce donut height**

In `generate_report.py`, in `_fig_donut`, change `height=420` to `height=240` and set `margin=dict(l=10, r=10, t=10, b=10)`.

Update the inner annotation font from `size=14` to `size=12`.

- [ ] **Step 6.2: Regenerate report and verify**

Run: `python generate_report.py`
Open report.html, scroll to Food Insecurity. Confirm donut is roughly half its previous height and still readable.

- [ ] **Step 6.3: Commit**

```bash
git add generate_report.py
git commit -m "ui(insecurity): shrink population-group donut to companion size"
```

---

## Task 7: Enhance GDP per capita table (M2)

**Files:**
- Modify: `generate_report.py:673-695` (function `_html_gdp_table`)

- [ ] **Step 7.1: Replace table builder with heatmap-style coloring + sparklines**

Replace `_html_gdp_table` entirely:

```python
def _html_gdp_table(wdi):
    gdp_pc = (
        wdi[wdi["Series Code"] == SERIES["gdp_pc"]]
        .pivot_table(index="Country Name", columns="Year", values="Value")
        .round(0)
    )
    years = [y for y in range(2011, 2025) if y in gdp_pc.columns]
    gdp_pc = gdp_pc[years]

    # Color scale: per-row min-max
    def cell_bg(v, vmin, vmax):
        if pd.isna(v) or vmax == vmin:
            return "transparent"
        # Higher = paler (light blue), lower = white. Lebanon row keeps its red highlight.
        t = (v - vmin) / (vmax - vmin)
        # Steel-blue with alpha proportional to t
        a = 0.05 + t * 0.30
        return f"rgba(46, 116, 181, {a:.2f})"

    def sparkline_svg(values, width=80, height=22):
        vals = [v for v in values if pd.notna(v)]
        if len(vals) < 2:
            return ""
        vmin, vmax = min(vals), max(vals)
        rng = max(vmax - vmin, 1e-9)
        n = len(values)
        pts = []
        for i, v in enumerate(values):
            if pd.isna(v):
                continue
            x = (i / (n - 1)) * (width - 2) + 1
            y = height - 1 - ((v - vmin) / rng) * (height - 2)
            pts.append(f"{x:.1f},{y:.1f}")
        path = "M" + " L".join(pts)
        last_v = next((v for v in reversed(values) if pd.notna(v)), None)
        last_color = "#ff595e" if last_v is not None and last_v < (vmin + rng * 0.5) else "#1982c4"
        return (
            f'<svg width="{width}" height="{height}" style="vertical-align:middle">'
            f'<path d="{path}" stroke="{last_color}" stroke-width="1.5" fill="none"/>'
            f'</svg>'
        )

    rows_html = ""
    for country in gdp_pc.index:
        cls = ' class="lbn"' if country == "Lebanon" else ""
        row_vals = [gdp_pc.loc[country, yr] for yr in years]
        vmin = min(v for v in row_vals if pd.notna(v))
        vmax = max(v for v in row_vals if pd.notna(v))
        cells = ""
        for v in row_vals:
            if pd.isna(v):
                cells += "<td>&mdash;</td>"
            else:
                bg = cell_bg(v, vmin, vmax)
                cells += f'<td style="background:{bg}">${v:,.0f}</td>'
        spark = sparkline_svg(row_vals)
        rows_html += (
            f'<tr{cls}><td>{country}</td>{cells}'
            f'<td style="text-align:center">{spark}</td></tr>\n'
        )
    header = (
        "<th>Country</th>"
        + "".join("<th>" + str(y) + "</th>" for y in years)
        + "<th>Trend</th>"
    )
    return (
        '<div class="tbl-wrap">'
        '<table class="data-tbl">'
        "<thead><tr>" + header + "</tr></thead>"
        "<tbody>" + rows_html + "</tbody>"
        "</table></div>"
    )
```

- [ ] **Step 7.2: Regenerate report and verify**

Run: `python generate_report.py`
Open report.html, scroll to bottom of Macro Shock section. Confirm:
- Numeric cells have varying background tint (deeper = higher GDP per capita within that row)
- A "Trend" column on the right shows a small inline SVG sparkline per country
- Lebanon row keeps its red `lbn` styling

- [ ] **Step 7.3: Commit**

```bash
git add generate_report.py
git commit -m "ui(macro): GDP per capita table — heatmap cells + sparkline column"
```

---

## Task 8: A2 — FX spread filled-area chart (Macro Shock)

**Files:**
- Modify: `generate_report.py` (add `_fig_fx_spread`, wire into Macro section)
- Modify: `scripts/chart_smoke.py`

- [ ] **Step 8.1: Add `_fig_fx_spread`**

Add to `generate_report.py`, after `_fig_gdp_rate` (around line 583):

```python
def _fig_fx_spread(wdi, exrate):
    """FX divergence: official LBP/USD (annual, WDI) vs unofficial (monthly, WFP).
    Y axis is log scale because the gap is multiplicative (~50x at peak).
    """
    off = (
        wdi[(wdi["Country Name"] == "Lebanon") & (wdi["Series Code"] == SERIES["official_fx"])]
        [["Year", "Value"]].dropna().sort_values("Year")
    )
    off = off.assign(date=pd.to_datetime(off["Year"].astype(str) + "-01-01"))

    unof = (
        exrate[exrate["commodity"] == "Exchange rate (unofficial)"]
        .groupby("year_month", as_index=False)["price"].mean()
    )
    unof["date"] = pd.to_datetime(unof["year_month"])
    unof = unof.sort_values("date")

    fig = go.Figure()
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
    for date_str, label, color_key, dash in EVENTS:
        col = _ecolor(color_key)
        fig.add_vline(x=pd.Timestamp(date_str), line_dash=dash, line_color=col, line_width=1.2, opacity=0.7)

    fig.update_layout(
        **_BASE, height=420, margin=dict(l=70, r=24, t=44, b=48),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(title="Year", showgrid=False),
        yaxis=dict(title="LBP per USD (log scale)", type="log", gridcolor="#EEF1F5"),
    )
    return fig.to_json()
```

- [ ] **Step 8.2: Wire into Macro Shock section**

In `_section_macro` (around line 1588), after the `gdp_rate` chart-card and before `inflation`, add:

```python
spread_json = _fig_fx_spread(wdi, d["exrate"])
```

Add `_fig_fx_spread` call inputs to `_section_macro`'s parameter use; since `d` is passed in, change `wdi = d["wdi"]` to also bind `exrate = d["exrate"]`.

Insert this card in the section HTML between gdp_rate card and inflation card:

```python
'<div class="chart-card">'
'<div class="chart-title">Official vs Unofficial Exchange Rate &mdash; The "Two Lebanons"</div>'
'<div class="chart-caption">Y axis is logarithmic so the gap is readable across the full range. '
'The shaded gap between the two lines <strong>is</strong> the crisis &mdash; '
'at its peak, market traders charged ~50x the official rate.</div>'
+ _plot_tag("fx_spread", spread_json) +
'</div>'
```

- [ ] **Step 8.3: Add smoke check**

In `scripts/chart_smoke.py`:

```python
def t_fx_spread():
    from generate_report import _fig_fx_spread
    from src.data_loader import load_wdi, load_exchange_rate
    j = _fig_fx_spread(load_wdi(), load_exchange_rate())
    assert_valid_plotly_json(j, expected_min_traces=2, label="fx_spread")
    obj = json.loads(j)
    assert obj["layout"]["yaxis"].get("type") == "log", "fx_spread: y-axis is not log"

smoke("fx_spread", t_fx_spread)
```

- [ ] **Step 8.4: Run smoke + regenerate**

Run: `python scripts/chart_smoke.py`
Expected: `fx_spread ✅ PASS`

Run: `python generate_report.py`
Open report.html, verify the FX spread chart appears immediately after GDP+Rate in Macro Shock with log Y-axis and visible filled gap.

- [ ] **Step 8.5: Commit**

```bash
git add generate_report.py scripts/chart_smoke.py
git commit -m "feat(macro): add FX spread filled-area chart (official vs unofficial LBP/USD)"
```

---

## Task 9: A3 — Remittances chart (Macro Shock)

**Files:**
- Modify: `generate_report.py` (add `_fig_remittances`, wire into Macro section)
- Modify: `scripts/chart_smoke.py`

- [ ] **Step 9.1: Add `_fig_remittances`**

Add to `generate_report.py` after `_fig_fx_spread`:

```python
def _fig_remittances(wdi):
    df = wdi[wdi["Series Code"] == SERIES["remittances"]].copy()
    df = df.sort_values(["Country Name", "Year"])

    fig = px.line(
        df, x="Year", y="Value", color="Country Name",
        color_discrete_map=COUNTRY_COLORS,
        labels={"Value": "Remittances (% of GDP)", "Year": "", "Country Name": "Country"},
        markers=True,
    )
    for tr in fig.data:
        is_lbn = tr.name == "Lebanon"
        tr.update(line=dict(width=3 if is_lbn else 2),
                  marker=dict(size=5 if is_lbn else 4),
                  hovertemplate=(
                      "<b>" + tr.name + "</b><br>%{x}: %{y:.1f}%<extra></extra>"
                  ))
    fig.update_layout(
        **_BASE, height=380, margin=dict(l=60, r=24, t=44, b=48),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        yaxis=dict(ticksuffix="%", gridcolor="#EEF1F5"),
        xaxis=dict(showgrid=False, dtick=2),
    )
    return fig.to_json()
```

- [ ] **Step 9.2: Compute Lebanon's latest remittance value for the callout**

In `_section_macro`, compute:

```python
rem_lbn = wdi[(wdi["Country Name"] == "Lebanon") & (wdi["Series Code"] == SERIES["remittances"])]
if not rem_lbn.empty:
    rem_latest_row = rem_lbn.sort_values("Year").iloc[-1]
    rem_latest_pct = float(rem_latest_row["Value"])
    rem_latest_year = int(rem_latest_row["Year"])
else:
    rem_latest_pct, rem_latest_year = 0.0, 0
```

- [ ] **Step 9.3: Wire chart-card into Macro Shock section**

Add this card to `_section_macro`, after the FX spread card (between `fx_spread` and `inflation_heatmap`):

```python
'<div class="chart-card">'
'<div class="chart-title">Personal Remittances &mdash; % of GDP</div>'
'<div class="chart-caption">In ' + str(rem_latest_year) + ', remittances equalled '
'<strong>' + "{:.1f}%".format(rem_latest_pct) + '</strong> of Lebanon\'s GDP &mdash; '
'among the highest in the world. The diaspora is what kept Lebanon from total collapse.</div>'
+ _plot_tag("remittances", _fig_remittances(wdi)) +
'</div>'
```

- [ ] **Step 9.4: Add smoke check**

```python
def t_remittances():
    from generate_report import _fig_remittances
    from src.data_loader import load_wdi
    j = _fig_remittances(load_wdi())
    assert_valid_plotly_json(j, expected_min_traces=1, label="remittances")
    obj = json.loads(j)
    countries = {tr["name"] for tr in obj["data"]}
    assert "Lebanon" in countries, f"remittances: Lebanon trace missing. Got: {countries}"

smoke("remittances", t_remittances)
```

- [ ] **Step 9.5: Run smoke + regenerate**

Run: `python scripts/chart_smoke.py`
Expected: `remittances ✅ PASS`

Run: `python generate_report.py`
Verify in browser.

- [ ] **Step 9.6: Commit**

```bash
git add generate_report.py scripts/chart_smoke.py
git commit -m "feat(macro): add remittances %-of-GDP comparison chart"
```

---

## Task 10: A4 — Inflation ridgeline + R1 removal (Macro Shock)

**Files:**
- Modify: `generate_report.py` (add `_fig_inflation_ridge`, remove `_fig_inflation` invocation)
- Modify: `scripts/chart_smoke.py`

- [ ] **Step 10.1: Add `_fig_inflation_ridge`**

Add to `generate_report.py` (after `_fig_inflation`):

```python
def _fig_inflation_ridge(wdi):
    """Stacked offset violins approximating a ridgeline.
    One ridge per country; Lebanon at top in crisis red. X = inflation %, capped 300%.
    """
    inf = wdi[wdi["Series Code"] == SERIES["inflation"]].copy()
    inf["Value"] = inf["Value"].clip(upper=300)

    countries = ["Lebanon"] + [c for c in COUNTRY_COLORS if c != "Lebanon"]
    countries = [c for c in countries if c in inf["Country Name"].unique()]

    fig = go.Figure()
    for i, country in enumerate(reversed(countries)):
        sub = inf[inf["Country Name"] == country]
        if sub.empty:
            continue
        col = COUNTRY_COLORS.get(country, "#888")
        fig.add_trace(go.Violin(
            x=sub["Value"], name=country,
            orientation="h",
            side="positive",
            width=2.4,
            points=False,
            line=dict(color=col, width=1.5),
            fillcolor=col,
            opacity=0.45,
            hovertemplate=(
                "<b>" + country + "</b><br>Inflation: %{x:.1f}%<extra></extra>"
            ),
            spanmode="hard",
        ))
    fig.add_vline(x=0, line_color="#888", line_width=1, line_dash="dot")
    fig.update_layout(
        **_BASE, height=360, margin=dict(l=160, r=24, t=24, b=48),
        showlegend=False,
        violinmode="overlay",
        xaxis=dict(title="Annual inflation (%, capped at 300%)",
                   ticksuffix="%", gridcolor="#EEF1F5",
                   range=[-20, 320]),
        yaxis=dict(showgrid=False),
    )
    return fig.to_json()
```

- [ ] **Step 10.2: Replace invocation in `_section_macro`**

In `_section_macro`, remove the line `inf_json = _fig_inflation(wdi)` and replace with:

```python
ridge_json = _fig_inflation_ridge(wdi)
```

Then in the section HTML, replace the inflation small-multiples card with:

```python
'<div class="chart-card">'
'<div class="chart-title">Inflation Distribution &mdash; Country Comparison</div>'
'<div class="chart-caption">Each ridge shows the distribution of annual inflation rates '
'observed for that country (2011&ndash;2024, capped at 300% for readability). '
"Lebanon's right tail dwarfs every regional peer in one frame.</div>"
+ _plot_tag("inflation_ridge", ridge_json) +
'</div>'
```

The original inflation small-multiples chart-card is now removed. Leave `_fig_inflation` defined for now (we'll delete the dead function in Task 17).

- [ ] **Step 10.3: Add smoke check**

```python
def t_inflation_ridge():
    from generate_report import _fig_inflation_ridge
    from src.data_loader import load_wdi
    j = _fig_inflation_ridge(load_wdi())
    assert_valid_plotly_json(j, expected_min_traces=3, label="inflation_ridge")
    obj = json.loads(j)
    types = {tr["type"] for tr in obj["data"]}
    assert "violin" in types, f"inflation_ridge: expected violin traces. Got: {types}"

smoke("inflation_ridge", t_inflation_ridge)
```

- [ ] **Step 10.4: Run smoke + regenerate**

Run: `python scripts/chart_smoke.py`
Expected: `inflation_ridge ✅ PASS`

Run: `python generate_report.py`
Confirm Macro Shock section now has a ridgeline chart instead of the 6-panel small multiples.

- [ ] **Step 10.5: Commit**

```bash
git add generate_report.py scripts/chart_smoke.py
git commit -m "feat(macro): replace inflation small multiples with country ridgeline"
```

---

## Task 11: A6 — Treemap A (Food Insecurity, Gov → Population Group)

**Files:**
- Modify: `generate_report.py` (add `_fig_treemap_insecurity`, wire into Food Insecurity section)
- Modify: `scripts/chart_smoke.py`

- [ ] **Step 11.1: Add `_fig_treemap_insecurity`**

Add to `generate_report.py` (in the Food Insecurity helpers area, e.g., near `_fig_donut`):

```python
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
    # Per-gov Phase 3+ population estimate (current snapshot)
    gov_df = (
        geo_snap.dropna(subset=["gov"])
        .groupby("gov", as_index=False)
        .agg(p3_pct=("Phase 3+ percentage current", "mean"),
             pop=("Population analyzed current", "mean"))
    )
    gov_df["p3_pop"] = gov_df["p3_pct"] * gov_df["pop"]

    # Latest population-group breakdown
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

    # Cross-product gov x group
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
```

- [ ] **Step 11.2: Wire into Food Insecurity section**

In `_section_insecurity`, after computing `ipc_bar_json` etc., add:

```python
treemap_a_json = _fig_treemap_insecurity(geo_snap, ipc_pop)
```

The Food Insecurity Row 2 will be set in Task 13 (when adding the population-group time series). For now, add the treemap as its own card temporarily after the existing Row 1:

```python
'<div class="chart-card">'
'<div class="chart-title">Phase 3+ Headcount by Governorate &amp; Population Group</div>'
'<div class="chart-caption">Treemap of estimated Phase 3+ population. '
'Tile area is proportional to the absolute number of people. '
'<em>Note:</em> the IPC governorate and population-group surveys are independent; '
'this chart assumes the latest national group composition applies uniformly '
'across governorates.</div>'
+ _plot_tag("treemap_a", treemap_a_json) +
'</div>'
```

(Layout will be re-organized in Task 13.)

- [ ] **Step 11.3: Add smoke check**

```python
def t_treemap_insecurity():
    from generate_report import _fig_treemap_insecurity, _IPC_TO_GOV
    from src.data_loader import load_ipc_geo, load_ipc_population_groups
    geo = load_ipc_geo().copy()
    geo["gov"] = geo["admin1_normalized"].map(_IPC_TO_GOV)
    snap = geo[geo["analysis_date"] == geo["analysis_date"].max()]
    j = _fig_treemap_insecurity(snap, load_ipc_population_groups())
    assert_valid_plotly_json(j, expected_min_traces=1, label="treemap_a")
    obj = json.loads(j)
    assert obj["data"][0].get("type") == "treemap", "treemap_a: not a treemap"

smoke("treemap_a", t_treemap_insecurity)
```

- [ ] **Step 11.4: Run smoke + regenerate**

Run: `python scripts/chart_smoke.py`
Expected: all smoke tests PASS.
Run: `python generate_report.py`
Verify Food Insecurity section now has a treemap showing gov → group with headcount-sized tiles.

- [ ] **Step 11.5: Commit**

```bash
git add generate_report.py scripts/chart_smoke.py
git commit -m "feat(insecurity): add treemap of Phase 3+ headcount by gov x group"
```

---

## Task 12: A7 — Population-group inequality time series (Food Insecurity)

**Files:**
- Modify: `generate_report.py` (add `_fig_pop_group_time`, integrate with M1 donut)
- Modify: `scripts/chart_smoke.py`

- [ ] **Step 12.1: Add `_fig_pop_group_time`**

Add to `generate_report.py` near `_fig_donut`:

```python
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
```

- [ ] **Step 12.2: Re-organize Food Insecurity section to two-column rows**

Replace the existing `_section_insecurity` body construction. The target layout:

- Row 1 (g2): IPC choropleth | UNHCR choropleth (UNHCR placeholder until Task 14)
- Row 2 (g2): Treemap A | (Population-group time series + small donut stacked)
- Row 3: IPC stacked bar
- Row 4: Gov basket bar

For now (Task 12), without UNHCR yet, set Row 1 = `g2(choropleth, donut)` so we don't have a hole. We'll move things in Task 14 once UNHCR exists.

In `_section_insecurity`, build the section HTML as:

```python
poptime_json = _fig_pop_group_time(ipc_pop)
# treemap_a_json already computed in Task 11

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
    # Row 1: IPC choropleth | (UNHCR placeholder = donut for now, replaced in Task 14)
    '<div class="g2">'
    '<div class="chart-card" style="margin-bottom:0">'
    '<div class="chart-title">IPC Phase 3+ by Governorate</div>'
    '<div class="chart-caption">Share of population in acute food insecurity. '
    'Darker = more severe.</div>'
    + _plot_tag("choropleth", choro_json) +
    '</div>'
    '<div class="chart-card" style="margin-bottom:0">'
    '<div class="chart-title">Phase 3+ Population Composition (Latest)</div>'
    '<div class="chart-caption">Population-group breakdown at most recent snapshot.</div>'
    + _plot_tag("donut", donut_json) +
    '</div>'
    '</div>'
    '<div style="margin-bottom:22px"></div>'
    # Row 2: Treemap A | Population-group time series
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
    '<div class="chart-title">Phase 3+ Trend by Population Group</div>'
    '<div class="chart-caption">Each line tracks Phase 3+ over time. '
    'Marker size scales with absolute headcount in that snapshot.</div>'
    + _plot_tag("pop_group_time", poptime_json) +
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
```

- [ ] **Step 12.3: Add smoke check**

```python
def t_pop_group_time():
    from generate_report import _fig_pop_group_time
    from src.data_loader import load_ipc_population_groups
    j = _fig_pop_group_time(load_ipc_population_groups())
    assert_valid_plotly_json(j, expected_min_traces=2, label="pop_group_time")

smoke("pop_group_time", t_pop_group_time)
```

- [ ] **Step 12.4: Run smoke + regenerate**

Run: `python scripts/chart_smoke.py`
Run: `python generate_report.py`
Verify Food Insecurity has the new 4-row structure with the time series alongside the treemap.

- [ ] **Step 12.5: Commit**

```bash
git add generate_report.py scripts/chart_smoke.py
git commit -m "feat(insecurity): add population-group Phase 3+ time series + reorganize section"
```

---

## Task 13: A8 — UNHCR Syrian refugees by governorate (companion choropleth)

**Files:**
- Modify: `generate_report.py` (add `_fig_unhcr_choropleth`, wire into Row 1)
- Modify: `scripts/chart_smoke.py`

- [ ] **Step 13.1: Add `_fig_unhcr_choropleth`**

Add to `generate_report.py` near `_fig_choropleth`:

```python
def _fig_unhcr_choropleth(unhcr):
    with open(GEOJSON_PATH) as f:
        geojson = json.load(f)

    df = unhcr.copy()
    # Mount Lebanon dual-naming workaround (matches IPC choropleth)
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
```

- [ ] **Step 13.2: Replace donut placeholder in Row 1 with UNHCR choropleth**

In `_section_insecurity`, add to data loads:
```python
unhcr = d["unhcr"]
unhcr_json = _fig_unhcr_choropleth(unhcr)
```

Replace the donut card in Row 1 (added in Task 12) with:
```python
'<div class="chart-card" style="margin-bottom:0">'
'<div class="chart-title">Registered Syrian Refugees by Governorate</div>'
'<div class="chart-caption">Lebanon hosts the world\'s highest per-capita refugee '
'population. Source: UNHCR Lebanon Operational Data.</div>'
+ _plot_tag("unhcr_choropleth", unhcr_json) +
'</div>'
```

Also move the donut into Row 2 underneath the population-group time series (small companion). Update Row 2's right column:
```python
'<div class="chart-card" style="margin-bottom:0">'
'<div class="chart-title">Phase 3+ Trend by Population Group</div>'
'<div class="chart-caption">Each line tracks Phase 3+ over time. '
'Marker size scales with absolute headcount in that snapshot.</div>'
+ _plot_tag("pop_group_time", poptime_json) +
'<div style="margin-top:14px;border-top:1px solid var(--border);padding-top:12px">'
'<div style="font-size:11px;color:var(--muted);font-weight:600;'
'text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px">'
'Latest snapshot composition</div>'
+ _plot_tag("donut", donut_json) +
'</div>'
'</div>'
```

- [ ] **Step 13.3: Add `unhcr` to `load_all()` in `generate_report.py`**

```python
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
```

Add the import at top: `from src.data_loader import (..., load_unhcr_refugees)`.

- [ ] **Step 13.4: Add smoke check**

```python
def t_unhcr_choropleth():
    from generate_report import _fig_unhcr_choropleth
    from src.data_loader import load_unhcr_refugees
    j = _fig_unhcr_choropleth(load_unhcr_refugees())
    assert_valid_plotly_json(j, expected_min_traces=1, label="unhcr_choropleth")

smoke("unhcr_choropleth", t_unhcr_choropleth)
```

- [ ] **Step 13.5: Run smoke + regenerate**

Run: `python scripts/chart_smoke.py`
Run: `python generate_report.py`
Verify Food Insecurity Row 1 = IPC choropleth + UNHCR choropleth side by side; Row 2 = treemap + (time series with companion donut underneath).

- [ ] **Step 13.6: Commit**

```bash
git add generate_report.py scripts/chart_smoke.py
git commit -m "feat(insecurity): add UNHCR refugees choropleth + restructure layout"
```

---

## Task 14: A9 — Slope chart + R2 removal (Health Toll)

**Files:**
- Modify: `generate_report.py` (add `_fig_slope`, replace small-multiples invocation)
- Modify: `scripts/chart_smoke.py`

- [ ] **Step 14.1: Add `_fig_slope`**

Add to `generate_report.py` near `_fig_dumbbell`:

```python
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
```

- [ ] **Step 14.2: Replace small-multiples invocation in `_section_health`**

In `_section_health`, remove `multi_json = _fig_small_mult(health)` and replace with:

```python
slope_json = _fig_slope(health)
```

In the section HTML, replace the "Key Nutrition & Mortality Trends" card with:

```python
'<div class="chart-card">'
'<div class="chart-title">Health Indicators &mdash; 2019 vs Latest</div>'
'<div class="chart-caption">Slope chart of each indicator from its 2019 baseline '
'to the most recent reading. <span style="color:#8ac926;font-weight:600">Green</span> '
'= improved (lower-is-better), <span style="color:#ff595e;font-weight:600">red</span> '
'= worsened.</div>'
+ _plot_tag("slope", slope_json) +
'</div>'
```

The 2x2 small-multiples card is now removed. Leave `_fig_small_mult` defined for now (cleaned up in Task 17).

- [ ] **Step 14.3: Add smoke check**

```python
def t_slope():
    from generate_report import _fig_slope
    from src.data_loader import load_health
    j = _fig_slope(load_health())
    assert_valid_plotly_json(j, expected_min_traces=2, label="slope")

smoke("slope", t_slope)
```

- [ ] **Step 14.4: Run smoke + regenerate**

Run: `python scripts/chart_smoke.py`
Run: `python generate_report.py`
Verify Health Toll section: slope chart replaces the 4-panel small multiples.

- [ ] **Step 14.5: Commit**

```bash
git add generate_report.py scripts/chart_smoke.py
git commit -m "feat(health): replace 4-panel small multiples with slope chart"
```

---

## Task 15: R3 — Remove radar chart (Health Toll)

**Files:**
- Modify: `generate_report.py` (`_section_health` — remove radar card)

- [ ] **Step 15.1: Remove radar from `_section_health`**

In `_section_health`, remove `radar_json = _fig_radar(health)` and remove the entire `<div class="chart-card">...radar...</div>` block (the "Health Profile Radar" card).

Leave `_fig_radar` defined for now (cleaned up in Task 17).

- [ ] **Step 15.2: Regenerate and verify**

Run: `python generate_report.py`
Confirm Health Toll no longer contains the radar card. Section flow should be: explorer → lag → slope → dumbbell → MENA.

- [ ] **Step 15.3: Commit**

```bash
git add generate_report.py
git commit -m "feat(health): remove radar chart (redundant with dumbbell)"
```

---

## Task 16: A1 — Sankey thesis chart (Landing)

**Files:**
- Modify: `generate_report.py` (add `_fig_sankey`, wire into Landing)
- Modify: `scripts/chart_smoke.py`

- [ ] **Step 16.1: Add `_fig_sankey`**

Add to `generate_report.py` near `_fig_timeline`:

```python
def _fig_sankey(ipc_geo, ipc_pop):
    """3-column Sankey: Population Group -> IPC Phase -> Governorate.

    Two independent IPC surveys feed this: ipc_pop has group x phase,
    ipc_geo has gov x phase. We scale the right-side flows so that the
    total flow into each phase node equals the total flow out of it.
    """
    geo = ipc_geo.copy()
    geo["gov"] = geo["admin1_normalized"].map(_IPC_TO_GOV)
    geo_snap = geo[geo["analysis_date"] == geo["analysis_date"].max()]

    pop_latest = (
        ipc_pop.dropna(subset=["Phase 1 number current"])
        .sort_values("analysis_date")
        .groupby("Level 1", as_index=False)
        .last()
    )

    groups = [g for g in POPULATION_GROUPS if g in pop_latest["Level 1"].values]
    phases = ["Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5"]
    govs = sorted(geo_snap["gov"].dropna().unique())

    nodes = groups + phases + govs
    idx = {n: i for i, n in enumerate(nodes)}

    sources, targets, values, link_colors = [], [], [], []

    # Group -> Phase
    grp_phase_totals = {p: 0.0 for p in phases}
    for _, row in pop_latest.iterrows():
        if row["Level 1"] not in groups:
            continue
        for i, p in enumerate(phases, start=1):
            n = row.get(f"Phase {i} number current", 0) or 0
            if n <= 0:
                continue
            sources.append(idx[row["Level 1"]])
            targets.append(idx[p])
            values.append(float(n))
            link_colors.append(COLORS[f"ipc_phase_{i}"] + "55")
            grp_phase_totals[p] += float(n)

    # Phase -> Gov, scaled so phase outflow equals phase inflow
    geo_agg = (
        geo_snap.dropna(subset=["gov"])
        .groupby("gov")
        .agg({f"Phase {i} percentage current": "mean" for i in range(1, 6)})
        .reset_index()
    )
    pop_total_per_gov = (
        geo_snap.groupby("gov")["Population analyzed current"].mean().to_dict()
    )

    for i, p in enumerate(phases, start=1):
        col = f"Phase {i} percentage current"
        gov_pop = []
        for _, row in geo_agg.iterrows():
            pop = pop_total_per_gov.get(row["gov"], 0) or 0
            gov_pop.append((row["gov"], row[col] * pop))
        total_in_phase = sum(v for _, v in gov_pop) or 1.0
        target_total = grp_phase_totals[p]
        if target_total <= 0:
            continue
        for gov_name, pop_in_phase in gov_pop:
            if pop_in_phase <= 0:
                continue
            scaled = pop_in_phase / total_in_phase * target_total
            sources.append(idx[p])
            targets.append(idx[gov_name])
            values.append(scaled)
            link_colors.append(COLORS[f"ipc_phase_{i}"] + "44")

    # Node colors
    node_colors = (
        [PALETTE[i % len(PALETTE)] for i, _ in enumerate(groups)]
        + [COLORS[f"ipc_phase_{i}"] for i in range(1, 6)]
        + ["#888888"] * len(govs)
    )

    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(
            label=nodes,
            color=node_colors,
            pad=14, thickness=14,
            line=dict(color="rgba(255,255,255,0.5)", width=0.5),
            hovertemplate="<b>%{label}</b><br>%{value:,.0f}<extra></extra>",
        ),
        link=dict(
            source=sources, target=targets, value=values, color=link_colors,
            hovertemplate=(
                "<b>%{source.label} → %{target.label}</b><br>"
                "%{value:,.0f} people<extra></extra>"
            ),
        ),
    ))
    fig.update_layout(
        font=dict(family="DM Sans, sans-serif", color="rgba(255,255,255,0.85)", size=11),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=440,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig.to_json()
```

- [ ] **Step 16.2: Wire into Landing section**

In `_section_landing`, add a new block at the bottom of the hero (just before the closing `</div>` of `id="s-landing"`):

```python
sankey_json = _fig_sankey(d["ipc_geo"], d["ipc_pop"])
```

Append to the landing markup before the trailing source line `<p>`:

```python
'<div style="background:rgba(255,255,255,0.04);border-radius:8px;'
'padding:18px;margin-top:32px">'
'<div style="font-size:10px;font-weight:700;letter-spacing:0.14em;'
'text-transform:uppercase;color:rgba(255,255,255,0.45);margin-bottom:8px">'
'Narrative arc &mdash; Population, food insecurity, geography</div>'
'<div style="font-size:13px;color:rgba(255,255,255,0.7);'
'margin-bottom:14px;line-height:1.6">'
'How Lebanon\'s population sorts by IPC phase, and where each phase concentrates '
'geographically. Hover any flow for exact headcounts.</div>'
+ _plot_tag("sankey", sankey_json) +
'</div>'
```

- [ ] **Step 16.3: Add smoke check**

```python
def t_sankey():
    from generate_report import _fig_sankey
    from src.data_loader import load_ipc_geo, load_ipc_population_groups
    j = _fig_sankey(load_ipc_geo(), load_ipc_population_groups())
    assert_valid_plotly_json(j, expected_min_traces=1, label="sankey")
    obj = json.loads(j)
    assert obj["data"][0]["type"] == "sankey", "sankey: not a sankey"
    nodes = obj["data"][0]["node"]["label"]
    # 4 groups + 5 phases + 8 govs = 17 nodes (allow some flex if Others is missing)
    assert len(nodes) >= 13, f"sankey: too few nodes ({len(nodes)})"

smoke("sankey", t_sankey)
```

- [ ] **Step 16.4: Run smoke + regenerate**

Run: `python scripts/chart_smoke.py`
Run: `python generate_report.py`
Verify Landing now shows the Sankey beneath the timeline. Hover should reveal flows from groups → phases → governorates with sensible numbers.

- [ ] **Step 16.5: Commit**

```bash
git add generate_report.py scripts/chart_smoke.py
git commit -m "feat(landing): add narrative-arc sankey (Group -> Phase -> Governorate)"
```

---

## Task 17: Dead-code cleanup

**Files:**
- Modify: `generate_report.py`

- [ ] **Step 17.1: Remove unused figure builders**

Delete these now-orphan functions from `generate_report.py`:

- `_fig_inflation` (replaced by `_fig_inflation_ridge` in Task 10)
- `_fig_small_mult` (replaced by `_fig_slope` in Task 14)
- `_fig_radar` (removed in Task 15)
- The `_RADAR_CODES` dict inside `_fig_radar` if it's local (verify no external uses)
- The `_MULTI_CODES` and `_MULTI_COLORS` constants if no longer referenced (grep before removing)

- [ ] **Step 17.2: Verify nothing else broke**

Run: `python scripts/chart_smoke.py`
Run: `python scripts/sanity_check.py`
Run: `python generate_report.py`
Open report.html and visually confirm all sections render without empty cards or layout glitches.

- [ ] **Step 17.3: Commit**

```bash
git add generate_report.py
git commit -m "refactor: remove orphan figure builders (inflation small-multiples, radar, health small-multiples)"
```

---

## Task 18: Final acceptance verification

**Files:** none

- [ ] **Step 18.1: Run full sanity check**

Run: `python scripts/sanity_check.py`
Expected: all rows ✅ PASS including `remittances` and `unhcr_refugees`.

- [ ] **Step 18.2: Run full chart smoke**

Run: `python scripts/chart_smoke.py`
Expected: all of: `treemap_b`, `fx_spread`, `remittances`, `inflation_ridge`, `treemap_a`, `pop_group_time`, `unhcr_choropleth`, `slope`, `sankey` show ✅ PASS.

- [ ] **Step 18.3: Acceptance walkthrough**

Open `report.html` in a browser and verify each item against the spec acceptance criteria (§7):

- [ ] Page nav still has 5 anchors (Landing / Macro / Food / Insecurity / Health).
- [ ] Landing: KPIs + timeline + Sankey at bottom.
- [ ] Macro Shock: GDP+Rate, FX spread, Remittances, Inflation heatmap, Inflation ridgeline, Enhanced GDP-pc table — in that order.
- [ ] Food Prices: 4 charts; treemap shows Category → Commodity tiles.
- [ ] Food Insecurity: Row 1 (IPC choropleth | UNHCR choropleth), Row 2 (Treemap A | time-series + small donut), Row 3 (IPC stacked bar), Row 4 (Gov basket bar).
- [ ] Health Toll: Indicator explorer, Lag dual-panel, Slope chart, Dumbbell, MENA — no radar, no 4-panel small multiples.
- [ ] All hover tooltips render with sensible values.
- [ ] No console errors in the browser devtools.

- [ ] **Step 18.4: Commit checkpoint (if any tweaks were needed)**

```bash
git status
# If changes:
git add -A
git commit -m "polish: acceptance pass tweaks"
```

---

## Self-Review

**Spec coverage:** Each spec section maps to a task:
- §2 A1 Sankey → Task 16
- §2 A2 FX spread → Task 8
- §2 A3 Remittances → Tasks 1 + 9
- §2 A4 Inflation ridgeline → Task 10
- §2 A5 Treemap B → Tasks 3 + 5
- §2 A6 Treemap A → Task 11
- §2 A7 Pop-group time series → Task 12
- §2 A8 UNHCR choropleth → Tasks 2 + 13
- §2 A9 Slope chart → Task 14
- §2 R1 (inflation small mult) → Tasks 10 + 17
- §2 R2 (health small mult) → Tasks 14 + 17
- §2 R3 (radar) → Tasks 15 + 17
- §2 M1 (small donut) → Tasks 6 + 13
- §2 M2 (enhanced table) → Task 7
- §5 Data acquisition → Tasks 1, 2
- §7 Acceptance criteria → Task 18

**Placeholder scan:** No "TBD" / "TODO" / "implement later" anywhere. Every step has either a concrete code block or a precise verification action.

**Type consistency:** All function names referenced match their definitions (`_fig_fx_spread`, `_fig_remittances`, `_fig_inflation_ridge`, `_fig_treemap_insecurity`, `_fig_pop_group_time`, `_fig_unhcr_choropleth`, `_fig_slope`, `_fig_sankey`, `load_unhcr_refugees`). The chart-id keys passed to `_plot_tag` (`fx_spread`, `remittances`, `inflation_ridge`, `treemap_a`, `pop_group_time`, `unhcr_choropleth`, `slope`, `sankey`) are consistent across all references.
