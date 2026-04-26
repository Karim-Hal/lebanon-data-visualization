import plotly.io as pio

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
COLORS = {
    "crisis_red":  "#C00000",
    "deep_navy":   "#1F3864",
    "steel_blue":  "#2E74B5",
    "teal":        "#1F7A8C",
    "warning":     "#E36C09",
    "ipc_phase_1": "#C8E6C9",
    "ipc_phase_2": "#FFF9C4",
    "ipc_phase_3": "#FFC000",
    "ipc_phase_4": "#E36C09",
    "ipc_phase_5": "#C00000",
    "bg":          "#F8F9FA",
    "card_bg":     "#EBF3FB",
}

# ---------------------------------------------------------------------------
# Project accent palette (10 colors) — use for chart series, indicators, peers
# ---------------------------------------------------------------------------
PALETTE = [
    "#ff595e",  # coral red   — crisis / Lebanon / worsened
    "#ffca3a",  # amber       — warning / Syria / anaemia
    "#8ac926",  # green       — improvement / positive trend
    "#1982c4",  # blue        — Saudi Arabia / infant mortality / neutral
    "#6a4c93",  # dark purple — Egypt / under-5 mortality / deep analytical
    "#46dff7",  # cyan        — Jordan / secondary series
    "#a99df2",  # lavender    — tertiary series
    "#ff89a6",  # pink        — quaternary series
    "#af848c",  # muted rose  — World reference / background series
    "#7f6aa3",  # medium purple — additional series
]

# Per-country color assignments for macro charts
COUNTRY_COLORS = {
    "Lebanon":                "#C00000",
    "Jordan":                 "#2E74B5",
    "Egypt, Arab Rep.":       "#1F7A8C",
    "Syrian Arab Republic":   "#E36C09",
    "Saudi Arabia":           "#1F3864",
    "United Arab Emirates":   "#6A9153",
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
