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
    "ipc_phase_1": "#8ac926",   # PALETTE green  — minimal
    "ipc_phase_2": "#ffca3a",   # PALETTE amber  — stressed
    "ipc_phase_3": "#E36C09",   # PALETTE/COLORS orange — crisis
    "ipc_phase_4": "#ff595e",   # PALETTE coral red — emergency
    "ipc_phase_5": "#C00000",   # COLORS crisis_red — famine
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

# Per-country color assignments — mapped to PALETTE (see CLAUDE.md §7)
COUNTRY_COLORS = {
    "Lebanon":                "#ff595e",  # PALETTE coral red
    "Jordan":                 "#46dff7",  # PALETTE cyan
    "Egypt, Arab Rep.":       "#6a4c93",  # PALETTE dark purple
    "Syrian Arab Republic":   "#ffca3a",  # PALETTE amber
    "Saudi Arabia":           "#1982c4",  # PALETTE blue
    "United Arab Emirates":   "#7f6aa3",  # PALETTE medium purple
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
