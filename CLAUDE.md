# Lebanon Crisis Dashboard — Streamlit Implementation

> **Project:** Data Visualization Final Project — Spring 2026
> **Authors:** Reem Marji & Karim Hallal
> **Stack:** Python + Streamlit + Plotly + Pandas
> **Original plan:** Power BI (see `lebanon_dashboard_report__1_.docx`). This file is the authoritative spec for the Streamlit port — when the docx and this file disagree, **follow this file.**

---

## 1. Purpose & Narrative

An interactive dashboard telling the story of Lebanon's multi-crisis trajectory (2012–2026): economic collapse → currency devaluation → food price transmission → food insecurity → child malnutrition. The dashboard follows a five-page narrative:

- **Page 0 — Landing:** Headline KPI cards + crisis timeline.
- **Page 1 — The Macro Shock (Act 1):** GDP, inflation, exchange rate across Lebanon and 5 regional peers.
- **Page 2 — Food Price Transmission (Act 2):** WFP commodity prices, basket index (2019=100), LBP/USD relationship.
- **Page 3 — Who Suffers Most (Act 2 Extended):** IPC food insecurity by governorate + population group.
- **Page 4 — The Health Toll (Act 3):** Stunting, wasting, anaemia, mortality with lagged overlay against food prices.

---

## 2. Project Structure

```
lebanon-dashboard/
├── CLAUDE.md                   ← this file
├── requirements.txt
├── README.md
├── app.py                      ← Streamlit entry point + sidebar nav
├── data/
│   ├── ipc_population_groups.csv
│   ├── ipc_geo.csv
│   ├── wfp_food_prices_clean.csv
│   ├── wfp_exchange_rate.csv
│   ├── wdi_long.csv
│   └── health_filtered.csv
├── assets/
│   └── lebanon_governorates.geojson   ← needed for choropleth; see §6.3
├── src/
│   ├── __init__.py
│   ├── config.py               ← colors, fonts, constants, event dates
│   ├── data_loader.py          ← cached loaders + sanity checks
│   ├── metrics.py              ← computed measures (basket index, GDP contraction, etc.)
│   └── charts.py               ← reusable Plotly chart builders
├── pages/
│   ├── 1_🏠_Landing.py
│   ├── 2_📉_Macro_Shock.py
│   ├── 3_🛒_Food_Prices.py
│   ├── 4_🗺️_Food_Insecurity.py
│   └── 5_🏥_Health_Toll.py
└── scripts/
    └── sanity_check.py         ← run once after cloning to verify data
```

Use Streamlit's **multipage app** pattern (files in `pages/` auto-register). The emoji + number prefix controls sidebar ordering.

---

## 3. Environment & Dependencies

```txt
# requirements.txt
streamlit>=1.37
pandas>=2.2
numpy>=1.26
plotly>=5.22
scipy>=1.13               # for pearsonr in scatter R²
openpyxl>=3.1             # if re-running any Excel reads
pyarrow>=16               # speeds up st.cache_data
```

Install: `pip install -r requirements.txt`
Run locally: `streamlit run app.py`

---

## 4. Skills to Reference

Claude Code supports Anthropic's Skills system (folders under `~/.claude/skills/` or a project-level `.claude/skills/` directory). **For this project, the single most useful skill is `frontend-design`** — it contains design-quality guidance that translates well to Streamlit/Plotly layouts (spacing, hierarchy, avoiding generic-AI aesthetics, color discipline).

### Skills to install

The `frontend-design` skill ships with Claude Code's public skills bundle. Check whether it's already available:

```bash
ls ~/.claude/skills/ 2>/dev/null
ls .claude/skills/ 2>/dev/null
```

If you don't see `frontend-design`, install it from Anthropic's public skills repo:

```bash
# from the project root
mkdir -p .claude/skills
cd .claude/skills
git clone https://github.com/anthropics/skills.git anthropic-skills
# then reference it in conversations, e.g. "use the frontend-design skill"
```

(If that repo URL has changed, search `anthropics skills github` — as of April 2026 Anthropic maintains a public skills repo; the frontend-design skill lives in its `public/` folder.)

**How to invoke during a session:** just tell Claude Code early in the conversation, e.g. *"Use the frontend-design skill for all visual styling decisions in this project."* Claude Code will read the SKILL.md before generating UI code.

### Skills NOT needed for this project

- `docx`, `pptx`, `xlsx`, `pdf` — we're not producing Office docs.
- `pdf-reading`, `file-reading` — we're reading CSVs, which pandas handles natively.
- `skill-creator` — only relevant if the user wants to build their own reusable skill from this project later.

---

## 5. Data Sanity Check (RUN FIRST)

**Before writing any app code**, run `scripts/sanity_check.py` to verify the six CSVs are preprocessed as the docx plan specifies. If any assertion fails, fix the data before proceeding — do NOT work around bad data in the app layer.

The checks below map 1-to-1 to the preprocessing steps in §3 of the docx plan.

### What the sanity check verifies

**`wfp_food_prices_clean.csv`** (from plan §3.1)
- `date` column parses as datetime.
- `pricetype` has **only** `'Retail'`.
- `category` does **not** contain `'non-food'`.
- `commodity` does **not** contain `'Exchange rate (unofficial)'`.
- Columns `baseline_usd` and `price_index` exist.
- For any 2019 row of a basket commodity, `price_index` ≈ 100 (±10 to allow monthly variance; the *annual mean* must round to 100).
- Basket items all present: `Bread (pita)`, `Rice (imported, Egyptian)`, `Oil (sunflower)`, `Eggs`, `Meat (chicken, whole, frozen)`, `Wheat flour`.

**`wfp_exchange_rate.csv`** (from plan §3.1)
- All rows have `commodity == 'Exchange rate (unofficial)'`.
- `date` parses as datetime, spans at least 2019 → 2024.
- `price` column is numeric and positive.

**`wdi_long.csv`** (from plan §3.2)
- Exactly these 6 countries in `Country Name`: `Lebanon`, `Jordan`, `Egypt, Arab Rep.`, `Syrian Arab Republic`, `Saudi Arabia`, `United Arab Emirates`.
- `Year` is integer.
- `Value` is numeric, no `'..'` strings, no NaN.
- Contains at least these `Series Code`s: `FP.CPI.TOTL.ZG` (inflation), `NY.GDP.MKTP.CD` (GDP), `PA.NUS.FCRF` (official exchange rate).
- Lebanon 2023 inflation row exists and ~221.3% (landing page KPI sanity).

**`ipc_geo.csv`** (from plan §3.3)
- No row has `Level 1` in the population-group list (`Lebanese residents`, `Syrian refugees`, `Palestinian Refugees`, `Newly displaced Syrian`, `Others`).
- Column `admin1_normalized` exists.
- Column `analysis_date` parses as datetime; covers Sep 2022 → Oct 2025.
- Normalized names are a subset of: `Akkar`, `Baalbek-El Hermel`, `Beirut`, `Bekaa`, `El Nabatieh`, `Mount Lebanon`, `North`, `South`.

**`ipc_population_groups.csv`** (from plan §3.3)
- Every row's `Level 1` is in the population-group list.
- `analysis_date` parses as datetime.
- Contains `'Lebanese residents'` in the most recent snapshot (needed for landing KPI).

**`health_filtered.csv`** (from plan §3.4)
- All rows have `COUNTRY (CODE) == 'LBN'`.
- Sex dimension is deduplicated: any row where `DIMENSION (TYPE) == 'SEX'` must have `DIMENSION (CODE) == 'SEX_BTSX'`.
- `GHO (DISPLAY)` values match at least one of the nutrition/mortality keywords.
- `YEAR (DISPLAY)` is integer.
- `Numeric` column exists and is numeric.

### Additional preprocessing Claude Code should add if missing

These weren't in the original plan but improve the Streamlit experience:

1. **Monthly aggregation helper column** on `wfp_food_prices_clean.csv`: a `year_month` string (`YYYY-MM`) to simplify monthly groupbys in charts. Add in the data loader, not as a new CSV.
2. **Governorate-name alignment check** between `wfp_food_prices_clean` (`admin1`) and `ipc_geo` (`admin1_normalized`). If any governorate appears in one but not the other, print a warning — don't crash.
3. **Scatter R² precomputation** (plan §5.6 leaves this as a placeholder): in `src/metrics.py`, compute Pearson R between monthly avg unofficial LBP/USD rate and monthly avg basket USD price, expose as `get_rate_vs_basket_r_squared()`. Don't hardcode 0.94.
4. **Inflation unit check** on `wdi_long.csv`: `FP.CPI.TOTL.ZG` is already a percentage — don't multiply by 100 anywhere in the app. Document this explicitly in `src/metrics.py` where the card is computed.

### Implementing the sanity check

The script should use `assert` statements with descriptive messages and print a ✅/❌ summary table at the end. Example skeleton:

```python
# scripts/sanity_check.py
import pandas as pd
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"

def check_wfp_prices():
    df = pd.read_csv(DATA / "wfp_food_prices_clean.csv", parse_dates=["date"])
    assert (df["pricetype"] == "Retail").all(), "Non-retail rows leaked in"
    assert "non-food" not in df["category"].unique(), "non-food not filtered"
    assert "Exchange rate (unofficial)" not in df["commodity"].unique()
    assert {"baseline_usd", "price_index"}.issubset(df.columns)
    # ... continue
    return True

# run all checks, collect pass/fail, print table
```

---

## 6. Page-by-Page Build Spec

All page specs below are **ports of §4 of the docx plan** — Power BI visuals mapped to Plotly/Streamlit equivalents.

### 6.0 Shared conventions

- **All charts use Plotly** (`plotly.express` for quick, `plotly.graph_objects` for composite/dual-axis).
- **Cache aggressively:** use `@st.cache_data` on every function in `data_loader.py` and `metrics.py`.
- **Layout:** use `st.columns()` for KPI rows. Default to wide layout: `st.set_page_config(layout="wide")` in each page.
- **Event markers** (vertical lines): Oct 2019 (banking crisis), Aug 2020 (port explosion), Mar 2021 (subsidy removal). Add via `fig.add_vline(x=..., line_dash="dash", annotation_text=...)`. Define dates once in `src/config.py`.
- **Never use `st.metric` for anything where formatting matters** — build custom HTML cards using `st.markdown(..., unsafe_allow_html=True)` or use `st.metric` only for simple numbers. Currency and percentages often need custom formatting.

### 6.1 Page 0 — Landing

Four KPI cards in a single `st.columns(4)` row, then a crisis-timeline block below.

| Card | Source | Computation |
|------|--------|-------------|
| Peak Annual Inflation | `wdi_long` | `max(Value)` where Country=Lebanon & Series=`FP.CPI.TOTL.ZG`. Format `{:.1f}%`. |
| GDP Contraction 2018→2023 | `wdi_long` | `(gdp_2018 - gdp_2023) / gdp_2018`. Format `{:.0%}`. Lebanon, `NY.GDP.MKTP.CD`. |
| Lebanese in IPC Phase 3+ | `ipc_population_groups` | Phase 3+ % for `Lebanese residents` at most recent `analysis_date`. Format `{:.0%}`. |
| LBP per USD (Unofficial) | `wfp_exchange_rate` | Most recent `price`. Format `{:,.0f}`. |

Timeline: horizontal sequence of three annotated events (Oct 2019, Aug 2020, Mar 2021) as a Plotly scatter-on-a-line, or as styled markdown boxes using `st.columns(3)`.

### 6.2 Page 1 — Macro Shock

1. **GDP + Exchange Rate dual-axis line** — Lebanon only. Use `make_subplots(specs=[[{"secondary_y": True}]])`. GDP (`NY.GDP.MKTP.CD`) on left, official rate (`PA.NUS.FCRF`) on right. Add three event vlines.
2. **Inflation small multiples** — `plotly.express.line(..., facet_col="Country Name", facet_col_wrap=3)`. All 6 countries, shared Y, Lebanon line in `CRISIS_RED`.
3. **GDP per capita table** — `st.dataframe` with `NY.GDP.PCAP.CD` pivoted country × year.

### 6.3 Page 2 — Food Prices

1. **Commodity index multi-line** — filter basket items, X=`date`, Y=`price_index`, color=`commodity`. Dotted horizontal line at 100.
2. **LBP vs USD basket dual-line** — compute monthly avg LBP price and USD price across basket items, plot on dual Y axes.
3. **Exchange rate scatter** — merge `wfp_food_prices_clean` (monthly avg USD basket) with `wfp_exchange_rate` (monthly avg). Plotly scatter with `trendline="ols"` (needs `statsmodels`). Annotate with R² computed in `metrics.py`.
4. **Slicers:** `st.multiselect` for commodity, `st.slider` for date range.

### 6.4 Page 3 — Food Insecurity

1. **Price by governorate bar** — join `wfp_food_prices_clean` to markets (if `admin1` is already in the prices CSV, no join needed; if not, document this gap in the loader). Most recent 12 months, sorted descending.
2. **IPC choropleth** — **requires a Lebanon governorate GeoJSON in `assets/lebanon_governorates.geojson`**. Use `px.choropleth_mapbox` or `px.choropleth`. Feature key should match `admin1_normalized`. A reliable source is the HDX Lebanon admin boundaries dataset — download once, commit to the repo.
3. **IPC date slicer** — `st.select_slider` over the unique `analysis_date` snapshots.
4. **IPC phase stacked bar** — X=`admin1_normalized`, stacked Y = Phase 1/2/3/4/5 counts (or %), legend = phase. Colors per plan §6.1 (Amber/Orange/Red for 3/4/5).
5. **Population group donut** — `px.pie(..., hole=0.5)` over `ipc_population_groups` at latest `analysis_date`.

### 6.5 Page 4 — Health Toll

1. **Dual-panel lag timeline** — two stacked `px.line` charts sharing X range. Top: basket `price_index`. Bottom: stunting prevalence. Use `plotly.subplots.make_subplots(rows=2, shared_xaxes=True)`. Add a shaded rectangle over 2020–2022 to highlight the lag window.
2. **Nutrition small multiples** — filter `health_filtered` to stunting, wasting, anaemia (children + women), infant mortality. `px.line(..., facet_col="GHO (DISPLAY)", facet_col_wrap=2)`.
3. **MENA scatter** — the docx plan notes the health file is Lebanon-only. For regional under-5 mortality (`SH.DYN.MORT`), pull from `wdi_long` instead if available there. If the indicator isn't in the WDI export, flag this clearly in the page as a known limitation — **do not fabricate data.**
4. **Indicator slicer:** `st.selectbox` over `GHO (DISPLAY)`.

---

## 7. Design Tokens (port of docx §6)

Centralize in `src/config.py`:

```python
COLORS = {
    "crisis_red":    "#C00000",   # Lebanon lines, urgent KPIs
    "deep_navy":     "#1F3864",   # headers, axis titles
    "steel_blue":    "#2E74B5",   # neutral peers (Jordan, Saudi)
    "teal":          "#1F7A8C",   # stable peers (UAE)
    "warning":       "#E36C09",   # event markers
    "ipc_phase_3":   "#FFC000",
    "ipc_phase_4":   "#E36C09",
    "ipc_phase_5":   "#C00000",
    "bg":            "#F8F9FA",
    "card_bg":       "#EBF3FB",
}

EVENTS = [
    ("2019-10-01", "Banking crisis & protests", "warning", "dash"),
    ("2020-08-04", "Beirut port explosion",     "crisis_red", "solid"),
    ("2021-03-01", "Subsidy removal",           "warning", "dash"),
]

BASKET = [
    "Bread (pita)", "Rice (imported, Egyptian)", "Oil (sunflower)",
    "Eggs", "Meat (chicken, whole, frozen)", "Wheat flour",
]

POPULATION_GROUPS = [
    "Lebanese residents", "Syrian refugees", "Palestinian Refugees",
    "Newly displaced Syrian", "Others",
]
```

### Custom accent palette

Ten-color project palette stored as `PALETTE` in `src/config.py`. Use for chart series, indicator lines, and peer-country differentiation. The `COLORS` dict above remains authoritative for semantic/structural colors (headers, event markers, IPC phases).

| Hex | Name | Preferred use |
|-----|------|---------------|
| `#ff595e` | Coral red | Lebanon highlight, worsened/crisis indicators |
| `#ffca3a` | Amber | Syria, anaemia, secondary warnings |
| `#8ac926` | Green | Improvement, positive trend |
| `#1982c4` | Blue | Saudi Arabia, infant mortality, neutral series |
| `#6a4c93` | Dark purple | Egypt, under-5 mortality, deep analytical |
| `#46dff7` | Cyan | Jordan, light secondary series |
| `#a99df2` | Lavender | Tertiary indicator series |
| `#ff89a6` | Pink | Quaternary indicator series |
| `#af848c` | Muted rose | World reference lines, background series |
| `#7f6aa3` | Medium purple | Additional indicator series |

Typography: default Plotly font `family="Segoe UI, sans-serif"`, set via `plotly.io.templates`.

---

## 8. Measure Translations (DAX → Python)

The docx §5 DAX measures are ported to pure-pandas functions in `src/metrics.py`. Key mappings:

| DAX Measure | Python function |
|-------------|-----------------|
| `[Avg Basket Price USD]` | `avg_basket_usd(df, date_range=None)` |
| `[Basket Price Index]` | `basket_price_index(df)` → returns DataFrame with monthly index |
| `[Lebanon Peak Inflation]` | `lebanon_peak_inflation(wdi)` |
| `[GDP Contraction]` | `gdp_contraction(wdi, start=2018, end=2023)` |
| `[Lebanese Phase 3+ %]` | `lebanese_phase3_plus(ipc_pop)` |
| `[Unofficial Rate LBP/USD]` | `monthly_unofficial_rate(exrate)` |
| `[Scatter R2 Label]` | `rate_vs_basket_r_squared(prices, exrate)` ← **actually computed**, not hardcoded |

Each function takes a DataFrame and returns a scalar or small DataFrame — keep them pure and cacheable.

---

## 9. Deployment

The plan's Power BI "Publish to web" workflow doesn't apply. For a free-tier Streamlit deployment:

- **Streamlit Community Cloud** (https://share.streamlit.io): push the repo to GitHub public, connect, deploy. Free for public apps.
- Alternative: **Hugging Face Spaces** (Streamlit SDK), also free.

For the course submission, embed the live URL in the project webpage instead of an iframe. If an iframe is specifically required, Streamlit apps iframe cleanly.

---

## 10. Acceptance Checklist (port of docx §8)

### Data
- [ ] `python scripts/sanity_check.py` exits 0, all ✅.
- [ ] All 6 CSVs loaded through cached loaders in `data_loader.py`.
- [ ] Governorate name alignment verified across WFP and IPC.

### Visuals
- [ ] Landing: 4 KPI cards, values match sanity check (Lebanon inflation ≈ 221.3%, GDP contraction ≈ 63%).
- [ ] Page 1: dual-axis GDP/rate chart + 3 event markers + inflation small multiples (6 countries).
- [ ] Page 2: indexed commodity lines (2019=100), dual-currency view, scatter with trendline + computed R².
- [ ] Page 3: governorate bar + choropleth + phase-stack + population donut + date slicer.
- [ ] Page 4: dual-panel lag timeline with shaded region + nutrition small multiples.

### Polish
- [ ] Consistent color palette across all pages.
- [ ] Event vlines only on charts spanning 2019–2021.
- [ ] All slicers debounced / cached (no full recompute on each interaction).
- [ ] `README.md` has quickstart + screenshot.
- [ ] App runs locally from a fresh clone after `pip install -r requirements.txt` and `streamlit run app.py`.

---

## 11. Working Style Notes for Claude Code

- **Prefer editing over creating** when files already exist.
- **Read before writing**: always `cat` a CSV's first 20 rows before writing loader code that assumes columns.
- **Cache everything**: every data loader and every derived metric goes behind `@st.cache_data`.
- **Do NOT fabricate** missing data (especially regional under-5 mortality). Surface the gap in-app.
- **Do NOT hardcode** the R² value — compute it.
- **Defer to `frontend-design` skill** on questions of spacing, hierarchy, typography, component density.
- **Ask before restructuring** `data/` or adding new CSVs. The preprocessing is done; don't re-run it.
