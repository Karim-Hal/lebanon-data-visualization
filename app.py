import streamlit as st

from src.config import COLORS  # noqa: F401 — ensures template is registered on import
from src.data_loader import check_governorate_alignment

st.set_page_config(
    page_title="Lebanon Crisis Dashboard",
    page_icon="🇱🇧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.title("🇱🇧 Lebanon Crisis Dashboard")
st.sidebar.markdown(
    """
    **Spring 2026 — Data Visualization Final Project**
    Reem Marji & Karim Hallal

    ---

    **Pages**
    1. 🏠 Landing — KPIs & crisis timeline
    2. 📉 Macro Shock — GDP, inflation, exchange rates
    3. 🛒 Food Prices — commodity index & LBP/USD
    4. 🗺️ Food Insecurity — IPC phases by governorate
    5. 🏥 Health Toll — stunting, wasting, mortality

    ---
    *Data sources: WFP, World Bank WDI, IPC, WHO GHO*
    """
)

# ---------------------------------------------------------------------------
# Governorate alignment warning (logged once at startup)
# ---------------------------------------------------------------------------
gov_warnings = check_governorate_alignment()
if gov_warnings:
    for w in gov_warnings:
        st.sidebar.warning(w)

# ---------------------------------------------------------------------------
# Landing splash (shown when user opens the root URL before selecting a page)
# ---------------------------------------------------------------------------
st.title("Lebanon Crisis Dashboard")
st.markdown(
    """
    This dashboard traces Lebanon's multi-crisis trajectory from **2012 to 2026**:
    economic collapse → currency devaluation → food price shock → food insecurity → child malnutrition.

    **Use the sidebar** (or the pages list) to navigate through the five-act narrative.
    """,
    unsafe_allow_html=False,
)

st.info("Select a page from the sidebar to begin.", icon="👈")
