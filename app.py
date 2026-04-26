import streamlit as st

from src.config import COLORS, PALETTE  # noqa: F401 — registers plotly template

st.set_page_config(
    page_title="Lebanon Crisis Dashboard",
    page_icon="🇱🇧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <style>
        .hero-title {{
            font-size: 52px;
            font-weight: 800;
            color: {COLORS['deep_navy']};
            line-height: 1.1;
            margin-bottom: 6px;
        }}
        .hero-subtitle {{
            font-size: 18px;
            color: #555;
            font-weight: 400;
            margin-bottom: 0;
        }}
        .meta-pill {{
            display: inline-block;
            background: {COLORS['card_bg']};
            border-radius: 20px;
            padding: 5px 14px;
            font-size: 13px;
            color: {COLORS['deep_navy']};
            font-weight: 600;
            margin-right: 8px;
            margin-top: 6px;
        }}
        .act-card {{
            background: {COLORS['card_bg']};
            border-left: 4px solid;
            border-radius: 6px;
            padding: 14px 18px;
            margin-bottom: 10px;
            font-size: 14px;
            color: #333;
            line-height: 1.5;
        }}
        .act-card b {{
            color: {COLORS['deep_navy']};
        }}
        .source-tag {{
            display: inline-block;
            border-radius: 4px;
            padding: 4px 10px;
            font-size: 12px;
            font-weight: 600;
            margin: 4px 4px 4px 0;
            letter-spacing: 0.02em;
        }}
        .divider-line {{
            border: none;
            border-top: 1px solid #e0e0e0;
            margin: 28px 0;
        }}
        .section-label {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #999;
            margin-bottom: 10px;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="hero-title">Lebanon in Crisis</div>
    <div class="hero-subtitle">
        A decade of economic collapse, food insecurity, and deteriorating health outcomes &nbsp;·&nbsp; 2012–2026
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)

st.markdown(
    f"""
    <span class="meta-pill">🎓 Data Visualization · Spring 2026</span>
    <span class="meta-pill">👤 Reem Marji</span>
    <span class="meta-pill">👤 Karim Hallal</span>
    """,
    unsafe_allow_html=True,
)

st.markdown("<hr class='divider-line'>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Body: narrative + story map
# ---------------------------------------------------------------------------
col_desc, col_gap, col_nav = st.columns([3, 0.3, 2])

with col_desc:
    st.markdown(
        f"""
        <div class="section-label">Context</div>
        <p style="font-size:15px;line-height:1.8;color:#333;margin-top:0">
        Lebanon experienced one of the world's most severe economic collapses of the modern era.
        A banking-sector crisis in <b style="color:{COLORS['warning']}">October 2019</b>,
        compounded by the <b style="color:{COLORS['crisis_red']}">Beirut port explosion</b> in August 2020
        and the removal of fuel and food subsidies in 2021, triggered a cascading humanitarian emergency.
        </p>
        <p style="font-size:15px;line-height:1.8;color:#333">
        The Lebanese pound lost over <b>98 %</b> of its value against the US dollar.
        Consumer prices rose more than <b>200 %</b> in a single year.
        The ripple effects — food insecurity, child malnutrition, and deteriorating health outcomes
        — are the subject of this dashboard.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-label">Data Sources</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
        <span class="source-tag" style="background:{PALETTE[3]}22;color:{PALETTE[3]}">
            WFP VAM Food Prices
        </span>
        <span class="source-tag" style="background:{PALETTE[4]}22;color:{PALETTE[4]}">
            World Bank WDI
        </span>
        <span class="source-tag" style="background:{PALETTE[2]}22;color:{PALETTE[2]}">
            IPC Global Platform
        </span>
        <span class="source-tag" style="background:{PALETTE[5]}22;color:{PALETTE[5]}">
            WHO Global Health Observatory
        </span>
        """,
        unsafe_allow_html=True,
    )

with col_nav:
    st.markdown('<div class="section-label">Story Structure</div>', unsafe_allow_html=True)

    acts = [
        ("🏠", "Landing", "KPI snapshot & crisis timeline", PALETTE[3]),
        ("📉", "Act 1 — Macro Shock", "GDP, inflation & exchange rates across Lebanon and regional peers", PALETTE[0]),
        ("🛒", "Act 2 — Food Prices", "WFP commodity index, LBP/USD transmission & basket trends", PALETTE[1]),
        ("🗺️", "Act 2 Ext. — Who Suffers", "IPC food insecurity phases by governorate & population group", PALETTE[2]),
        ("🏥", "Act 3 — Health Toll", "Stunting, wasting, anaemia & mortality with lagged price overlay", PALETTE[4]),
    ]

    for icon, title, desc, color in acts:
        st.markdown(
            f"""
            <div class="act-card" style="border-left-color:{color}">
                {icon} <b>{title}</b><br>
                <span style="color:#666;font-size:13px">{desc}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<hr class='divider-line'>", unsafe_allow_html=True)
st.markdown(
    "<p style='font-size:12px;color:#aaa;text-align:center'>Select a page from the sidebar to begin navigating the story.</p>",
    unsafe_allow_html=True,
)
