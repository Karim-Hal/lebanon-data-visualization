# Lebanon Crisis Dashboard — Chart Redesign Spec
**Date:** 2026-05-06
**Authors:** Reem Marji & Karim Hallal
**Status:** Draft — pending review

---

## 1. Goal

Improve `report.html` along three dimensions:

1. **Diversify chart types** — replace redundant line-chart blocks with chart forms that fit the underlying data better.
2. **Surface untold stories** — three story angles already in the data are currently invisible: the official-vs-unofficial FX divergence, population-group inequality over time, and the absolute-headcount geography of food insecurity.
3. **Round out the macro narrative** — add two external datasets (remittances, UNHCR refugees) so the report explains *why* Lebanon hasn't fully imploded (diaspora) and *who* carries the humanitarian load (refugees).

Output stays a single self-contained `report.html` produced by `generate_report.py`. No structural changes to the generator architecture.

---

## 2. Scope summary

**Additions** (9 new chart slots):

| # | Chart | Page | Data |
|---|-------|------|------|
| A1 | Sankey: Population Group → IPC Phase → Governorate | Landing | Existing (`ipc_geo`, `ipc_pop`) |
| A2 | FX spread (official vs unofficial, filled area) | Macro Shock | Existing (`wdi_long`, `wfp_exchange_rate`) |
| A3 | Remittances as % of GDP (6-country comparison) | Macro Shock | **New** WDI series |
| A4 | Inflation ridgeline by country | Macro Shock | Existing (`wdi_long`) |
| A5 | Treemap B: Category → Commodity, area = monthly cost share | Food Prices | Existing (`wfp_food_prices_clean`) |
| A6 | Treemap A: Governorate → Population Group, area = headcount | Food Insecurity | Existing (`ipc_geo`, `ipc_pop`) |
| A7 | Population-group inequality over time | Food Insecurity | Existing (`ipc_pop`) |
| A8 | UNHCR Syrian refugees by governorate (companion choropleth) | Food Insecurity | **New** UNHCR snapshot |
| A9 | Slope chart: pre-crisis → latest, all health indicators | Health Toll | Existing (`health_filtered`) |

**Removals** (3):

| # | Chart | Page | Reason |
|---|-------|------|--------|
| R1 | Inflation 6-panel small multiples | Macro Shock | Replaced by A4 (ridgeline says it more compactly) |
| R2 | Health 4-panel small multiples | Health Toll | Replaced by A9 (slope chart says it more compactly) |
| R3 | Pre-crisis vs post-crisis radar | Health Toll | Dumbbell tells the same story more accurately |

**Modifications** (2):

| # | Chart | Page | Change |
|---|-------|------|--------|
| M1 | Population-group donut | Food Insecurity | Shrink to companion of A7 (latest-snapshot reference) |
| M2 | GDP per capita table | Macro Shock | Add inline heatmap-style cell coloring + sparkline column |

**Net:** ~17 → ~23 charts.

---

## 3. Page-by-page final layout

### Page 0 — Landing
1. Hero KPI cards (4) — keep
2. Event timeline scatter — keep
3. **A1 Sankey**: Population Group → IPC Phase → Governorate (thesis preview at bottom)

### Page 1 — Macro Shock
1. GDP + Official rate dual-axis — keep
2. **A2 FX spread filled-area** (new — paired immediately after #1)
3. **A3 Remittances % of GDP** — 6-country comparison line chart
4. Inflation heatmap — keep
5. **A4 Ridgeline of inflation by country** — replaces the removed 6-panel small-multiples
6. **M2 Enhanced GDP per capita table** — heatmap-style coloring + sparkline column

### Page 2 — Food Prices
1. Commodity price index multi-line — keep
2. LBP vs USD basket dual-axis — keep
3. Scatter + OLS + R² callout — keep
4. **A5 Treemap B** — replaces current treemap in the same slot. Hierarchy: Category → Commodity. Area = monthly cost share (basket weight × current USD price). Color = % change since 2019.

### Page 3 — Food Insecurity
- Filter bar (existing snapshot date selector) — keep
- **Row 1 (g2):** IPC Phase 3+ choropleth | **A8 UNHCR Syrian refugees by governorate** (companion choropleth, latest snapshot)
- **Row 2 (g2):** **A6 Treemap A** (Gov → Pop Group, area = Phase 3+ headcount) | **A7 Population-group time series** with **M1 small companion donut** beneath it
- **Row 3:** IPC stacked bar by gov — keep
- **Row 4:** Avg basket price by gov — keep

### Page 4 — Health Toll
1. Indicator explorer (interactive lines) — keep
2. Food prices vs stunting lag dual-panel — keep
3. **A9 Slope chart** — replaces removed 4-panel small-multiples
4. Dumbbell — keep
5. ~~Radar~~ — REMOVED
6. MENA under-5 mortality — keep

---

## 4. Chart specifications (new + modified only)

### A1 — Sankey: Population Group → IPC Phase → Governorate

- **Type:** `plotly.graph_objects.Sankey`
- **Data:** Latest IPC snapshot (most recent `analysis_date` shared by `ipc_geo` and `ipc_pop`).
- **Nodes (3 columns):**
  - Column 1: Population groups (`Lebanese residents`, `Syrian refugees`, `Palestinian Refugees`, `Newly displaced Syrian`).
  - Column 2: IPC phases (`Phase 1`, `Phase 2`, `Phase 3`, `Phase 4`, `Phase 5`).
  - Column 3: Governorates (the 8 normalized governorates).
- **Links:**
  - Group → Phase value = headcount in that group × phase (from `ipc_pop`).
  - Phase → Gov value = headcount in that phase × governorate (from `ipc_geo`).
- **Color:** Phase nodes use `COLORS["ipc_phase_*"]`; group nodes use `PALETTE`; gov nodes neutral.
- **Open issue:** `ipc_pop` and `ipc_geo` are independent surveys — phase totals between the two columns may not match exactly. Mitigation: scale right-side flows so their column total matches the phase column total (and document this in the chart caption).

### A2 — FX spread filled area

- **Type:** `go.Scatter` two traces with `fill="tonexty"`.
- **Data:** Monthly. Official rate from `wdi_long` (`PA.NUS.FCRF`, annual — interpolate monthly with step function or use start-of-year value). Unofficial rate from `wfp_exchange_rate` (already monthly).
- **Encoding:** Y axis log scale (the spread is multiplicative, ~50× at peak — linear scale crushes the early years to zero).
- **Annotations:** Same three event vlines as elsewhere.
- **Caption notes:** Explain that the gap *is* the crisis — shadow market vs official.

### A3 — Remittances % of GDP

- **Type:** `px.line` (lines + markers), 6-country comparison, Lebanon highlighted.
- **Data:** New WDI series `BX.TRF.PWKR.DT.GD.ZS` (Personal remittances received, % of GDP) for the same 6 countries already in `wdi_long`.
- **Encoding:** Color = country (use existing `COUNTRY_COLORS`). Lebanon line `width=3`, others `width=2`.
- **Callout:** "Remittances are ~30% of Lebanon's GDP — among the highest in the world. The diaspora prop." Pull the latest Lebanon value into the caption text dynamically.

### A4 — Inflation ridgeline by country

- **Type:** Stacked `go.Violin` with `side="positive"` and vertical offsets per country (Plotly doesn't have a true ridgeline but stacked offset violins or KDE traces approximate it cleanly).
- **Data:** All annual inflation observations from `wdi_long` (`FP.CPI.TOTL.ZG`) per country.
- **Encoding:** One ridge per country, Lebanon at top in crisis red. X axis = inflation %, capped at 300% to keep readable. Vertical position = country.
- **Replaces:** R1 (the 6-panel small multiples).

### A5 — Treemap B (Food Prices)

- **Type:** `px.treemap`.
- **Hierarchy:** Category (Cereals, Proteins, Oils, Dairy/Eggs) → Commodity. Mapping defined in `src/config.py` as a `BASKET_CATEGORIES` dict.
- **Tile area:** Monthly cost share = `weight_kg × latest_usd_price`. Use equal weights (1 unit per commodity) as a defensible default; document in the chart caption that this is "an equally-weighted basket". If WFP publishes official basket weights for Lebanon, prefer those.
- **Color:** % change in `price_index` since 2019 (continuous scale, `card_bg` → `crisis_red`).
- **Replaces:** Current treemap in the same slot.

### A6 — Treemap A (Food Insecurity)

- **Type:** `px.treemap`.
- **Hierarchy:** Governorate → Population Group.
- **Tile area:** **Phase 3+ headcount** = `phase3plus_pct × population_in_gov_group`. Requires us to combine `ipc_geo` (gov-level rates) with `ipc_pop` (group-level absolute numbers). If a clean cross-tab isn't available in the data, document the assumption (uniform group distribution within a gov, or whatever else applies) in the caption.
- **Color:** % of that group in Phase 3+ (severity), continuous scale.
- **Open issue:** Same data-mismatch caveat as A1. The two IPC surveys are independent.

### A7 — Population-group inequality over time

- **Type:** `px.line` with markers, one line per population group.
- **Data:** `ipc_pop` — Phase 3+ % across all `analysis_date` snapshots, grouped by `Level 1`.
- **Encoding:** Color = group (`PALETTE`). Marker size = number of people in Phase 3+ (so visually-large markers signal scale). Y axis ticksuffix `%`.
- **Companion (M1):** A small (height ~180px) donut next to or below A7 showing the latest snapshot composition. Acts as a quick reference legend.

### A8 — UNHCR Syrian refugees by governorate

- **Type:** `px.choropleth_map` (matches existing IPC choropleth styling).
- **Data:** New `unhcr_refugees_lebanon.csv`. Columns: `governorate` (matching `admin1_normalized`), `registered_syrian_refugees` (count), `as_of_date`.
- **Encoding:** Color scale `card_bg → PALETTE[0]`. Hover shows count + per-capita ratio if local population data is available.
- **Caption:** Source + as-of date, plus a brief note that Lebanon hosts the world's highest per-capita refugee population.

### A9 — Slope chart (Health)

- **Type:** Custom `go.Scatter` with two-point lines.
- **Data:** `health_filtered`, all key indicators (stunting, wasting, underweight, anaemia children, infant mortality, under-5 mortality, neonatal mortality).
- **X axis:** Two ticks — "2019" and "Latest year".
- **Y axis:** Indicator values (one indicator per line).
- **Encoding:** Line color = `#8ac926` if improved, `#ff595e` if worsened (same logic as the dumbbell). Indicator label at right end. Slope steepness reads as direction-and-magnitude.
- **Replaces:** R2 (the 4-panel health small-multiples).

### M2 — Enhanced GDP per capita table

- Inline cell color (heatmap style) per row using the same scale as the inflation heatmap, on the GDP-per-capita value (low = card_bg, high = a single cool tone).
- Add a final column "Trajectory" containing a small inline SVG sparkline per country.
- Lebanon row keeps its existing red highlight class.

---

## 5. New data acquisition

### 5.1 Remittances (% of GDP)

- **Source:** World Bank WDI, series `BX.TRF.PWKR.DT.GD.ZS` (Personal remittances, received, % of GDP).
- **URL:** https://data.worldbank.org/indicator/BX.TRF.PWKR.DT.GD.ZS
- **Method:** Manual CSV download from the World Bank UI for the 6 countries (Lebanon, Jordan, Egypt Arab Rep., Syrian Arab Republic, Saudi Arabia, United Arab Emirates).
- **Storage:** Append rows to existing `data/wdi_long.csv` (it already accepts arbitrary `Series Code` values). Loader code in `src/data_loader.py` doesn't need to change.
- **Sanity check addition:** Confirm `BX.TRF.PWKR.DT.GD.ZS` exists for Lebanon for at least 2010–2022.

### 5.2 UNHCR Syrian refugees by governorate

- **Source:** UNHCR Lebanon Operational Data Portal, https://data.unhcr.org/en/country/lbn
- **What to look for:** "Registered Syrian Refugees by Governorate" snapshot (typically published as a periodic infographic + CSV).
- **Method:** Manual download. The portal updates the snapshot infrequently (quarterly to annually). Pick the most recent available snapshot.
- **Storage:** New file `data/unhcr_refugees_lebanon.csv` with columns:
  - `governorate` — must match `admin1_normalized` values from `ipc_geo`
  - `registered_refugees` — integer count
  - `as_of_date` — ISO date
- **Loader:** Add `load_unhcr_refugees()` to `src/data_loader.py`.
- **Sanity check addition:** Verify all 8 governorates are present and the as-of date is within 2 years of today.
- **Fallback:** If a governorate-level UNHCR CSV is not findable in time, use the latest published infographic data manually transcribed into the CSV. Document the source URL and as-of date in the caption.

### 5.3 No other new data

Per scope: not adding CPI components, electricity data, banking deposits, brain drain, or healthcare access metrics.

---

## 6. Out of scope

- Restructuring `generate_report.py` architecture (still a single-file generator).
- Streamlit app changes (the live URL still serves the existing pages until separately migrated).
- Adding bump charts, calendar heatmaps, waterfalls, or other chart types we considered and dropped.
- Mobile responsiveness improvements beyond what already exists.
- Any change to the `src/config.py` color palette beyond adding a `BASKET_CATEGORIES` mapping for A5.

---

## 7. Acceptance criteria

- [ ] `python generate_report.py` runs cleanly and produces `report.html`.
- [ ] All 9 new charts render and respond to hover.
- [ ] All 3 removed charts are no longer in the output.
- [ ] M1 (small companion donut) and M2 (enhanced table) reflect the modifications described.
- [ ] `data/wdi_long.csv` contains `BX.TRF.PWKR.DT.GD.ZS` rows for all 6 countries.
- [ ] `data/unhcr_refugees_lebanon.csv` exists with all 8 governorates.
- [ ] `python scripts/sanity_check.py` exits 0.
- [ ] No existing kept charts are visually changed beyond what's in §3.
- [ ] Page nav still has 5 anchors (Landing / Macro / Food / Insecurity / Health) — no new top-level sections.

---

## 8. Risks & mitigations

| Risk | Mitigation |
|------|-----------|
| Sankey data mismatch (`ipc_geo` and `ipc_pop` are independent surveys) | Scale flows so column sums match phase totals; document in caption |
| Treemap A relies on combining gov rates with group counts — clean cross-tab may not exist | Use the simplest defensible assumption (uniform group distribution within a gov) and label clearly |
| WFP basket weights not officially published for Lebanon → A5 cost share is approximate | Use equal weights; caption explicitly states "equally weighted basket" |
| UNHCR governorate CSV not directly downloadable | Manual transcription from latest infographic, cite source URL + as-of date |
| FX spread on log scale may surprise readers | Add chart caption explicitly noting log scale and why |
| Ridgeline (A4) — Plotly has no native ridgeline; stacked offset violins are the closest | Acceptable; if visual quality is poor we fall back to a single overlaid `go.Violin` per country with shared X axis |
| Slope chart label collisions when many indicators converge | Reduce indicator set if needed; or use small jitter on the right-side label positions |
