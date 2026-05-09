import plotly.io as pio

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
COLORS = {
    "crisis_red":  "#d03109",        # PALETTE[10] red-orange — highest severity
    "deep_navy":   "#1F3864",
    "steel_blue":  "#00a8e2",        # PALETTE[2] blue
    "teal":        "#00906e",        # PALETTE[8] teal
    "warning":     "#f78b32",        # PALETTE[4] orange — warning level
    "ipc_phase_1": "#56b76a",        # PALETTE[1] green — minimal
    "ipc_phase_2": "#e8c235",        # warm yellow — stressed (estimated from palette tone)
    "ipc_phase_3": "#f78b32",        # PALETTE[4] orange — crisis
    "ipc_phase_4": "#e06600",        # PALETTE[0] deep orange — emergency
    "ipc_phase_5": "#d03109",        # PALETTE[10] red-orange — famine
    "bg":          "#F8F9FA",
    "card_bg":     "#EBF3FB",
}

# ---------------------------------------------------------------------------
# Project accent palette (11 colors) — use for chart series, indicators, peers
# ---------------------------------------------------------------------------
PALETTE = [
    "#e06600",  # 0  deep orange  — primary / heat / Lebanon
    "#56b76a",  # 1  green        — positive / improvement
    "#00a8e2",  # 2  blue         — neutral / official / Saudi Arabia
    "#aa5ba5",  # 3  purple       — Syria / analytical
    "#f78b32",  # 4  light orange — warning / secondary heat
    "#ca8572",  # 5  mauve        — Jordan / tertiary
    "#ac86ec",  # 6  lavender     — UAE / quaternary
    "#5e53c5",  # 7  indigo       — Egypt / deep analytical
    "#00906e",  # 8  teal         — additional series
    "#69b476",  # 9  light green  — additional series
    "#d03109",  # 10 red-orange   — crisis / worsened / famine
]

# Per-country color assignments — mapped to new PALETTE
COUNTRY_COLORS = {
    "Lebanon":                "#e06600",  # PALETTE[0] deep orange
    "Jordan":                 "#ca8572",  # PALETTE[5] mauve
    "Egypt, Arab Rep.":       "#5e53c5",  # PALETTE[7] indigo
    "Syrian Arab Republic":   "#aa5ba5",  # PALETTE[3] purple
    "Saudi Arabia":           "#00a8e2",  # PALETTE[2] blue
    "United Arab Emirates":   "#ac86ec",  # PALETTE[6] lavender
}

# ---------------------------------------------------------------------------
# Crisis event markers
# (date_str, label, color_key, dash_style)
# ---------------------------------------------------------------------------
EVENTS = [
    ("2019-10-01", "Banking crisis & protests", "warning",    "dash"),
    ("2020-08-04", "Beirut port explosion",     "crisis_red", "solid"),
    ("2021-03-01", "Subsidy removal",           "warning",    "dash"),
]

# ---------------------------------------------------------------------------
# Food basket commodities
# ---------------------------------------------------------------------------
BASKET = [
    "Bread (pita)",
    "Rice (imported, Egyptian)",
    "Oil (sunflower)",
    "Eggs",
    "Meat (chicken, whole, frozen)",
    "Wheat flour",
]

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

# ---------------------------------------------------------------------------
# IPC population groups
# ---------------------------------------------------------------------------
POPULATION_GROUPS = [
    "Lebanese residents",
    "Syrian refugees",
    "Palestinian Refugees",
    "Newly displaced Syrian",
    "Others",
]

# ---------------------------------------------------------------------------
# WDI series codes used across pages
# ---------------------------------------------------------------------------
SERIES = {
    "inflation":    "FP.CPI.TOTL.ZG",
    "gdp":          "NY.GDP.MKTP.CD",
    "gdp_pc":       "NY.GDP.PCAP.CD",
    "official_fx":  "PA.NUS.FCRF",
    "remittances":  "BX.TRF.PWKR.DT.GD.ZS",
}

# NOTE: FP.CPI.TOTL.ZG values are already percentages — do NOT multiply by 100.

# ---------------------------------------------------------------------------
# Plotly default template
# ---------------------------------------------------------------------------
pio.templates["lebanon"] = pio.templates["plotly_white"]
pio.templates["lebanon"].layout.font = dict(family="Segoe UI, sans-serif", color="#1F3864")
pio.templates["lebanon"].layout.paper_bgcolor = "#F8F9FA"
pio.templates["lebanon"].layout.plot_bgcolor  = "#F8F9FA"
pio.templates.default = "lebanon"
