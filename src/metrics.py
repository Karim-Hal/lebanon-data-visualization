"""
DAX → pandas measure translations (see CLAUDE.md §8).

NOTE on FP.CPI.TOTL.ZG: values are already annual percentages (e.g. 221.3).
Do NOT multiply by 100 anywhere — not here, not in pages.
"""

import pandas as pd
import streamlit as st
from scipy.stats import pearsonr

from src.config import BASKET, SERIES


# ---------------------------------------------------------------------------
# Landing KPIs
# ---------------------------------------------------------------------------

@st.cache_data
def lebanon_peak_inflation(wdi: pd.DataFrame) -> float:
    """Max annual inflation % for Lebanon. Equivalent to DAX [Lebanon Peak Inflation]."""
    mask = (wdi["Country Name"] == "Lebanon") & (wdi["Series Code"] == SERIES["inflation"])
    return float(wdi.loc[mask, "Value"].max())


@st.cache_data
def gdp_contraction(wdi: pd.DataFrame, start: int = 2018, end: int = 2023) -> float:
    """(gdp_start - gdp_end) / gdp_start for Lebanon. Returns a fraction (e.g. 0.63)."""
    mask = (wdi["Country Name"] == "Lebanon") & (wdi["Series Code"] == SERIES["gdp"])
    gdp = wdi.loc[mask].set_index("Year")["Value"]
    gdp_start = gdp.loc[start]
    gdp_end   = gdp.loc[end]
    return float((gdp_start - gdp_end) / gdp_start)


@st.cache_data
def lebanese_phase3_plus(ipc_pop: pd.DataFrame) -> float:
    """Phase 3+ % for Lebanese residents at the most recent analysis_date."""
    latest = ipc_pop["analysis_date"].max()
    row = ipc_pop[
        (ipc_pop["analysis_date"] == latest) &
        (ipc_pop["Level 1"] == "Lebanese residents")
    ]
    if row.empty:
        return float("nan")
    return float(row["Phase 3+ percentage current"].iloc[0])


@st.cache_data
def latest_unofficial_rate(exrate: pd.DataFrame) -> float:
    """Most recent LBP/USD unofficial exchange rate."""
    return float(exrate.loc[exrate["date"].idxmax(), "price"])


# ---------------------------------------------------------------------------
# Food price measures
# ---------------------------------------------------------------------------

@st.cache_data
def avg_basket_usd(prices: pd.DataFrame, date_range: tuple | None = None) -> float:
    """Overall average USD price across basket items, optionally filtered by date range."""
    df = prices[prices["commodity"].isin(BASKET)].copy()
    if date_range is not None:
        start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
        df = df[(df["date"] >= start) & (df["date"] <= end)]
    return float(df["usdprice"].mean())


@st.cache_data
def basket_price_index(prices: pd.DataFrame) -> pd.DataFrame:
    """
    Monthly average price_index across all basket items.
    Returns a DataFrame with columns: year_month, price_index.
    Baseline: 2019 = 100 (set during preprocessing).
    """
    df = prices[prices["commodity"].isin(BASKET)].copy()
    monthly = (
        df.groupby("year_month", as_index=False)["price_index"]
        .mean()
        .sort_values("year_month")
    )
    return monthly


@st.cache_data
def monthly_unofficial_rate(exrate: pd.DataFrame) -> pd.DataFrame:
    """Monthly average unofficial LBP/USD rate. Returns year_month + price columns."""
    return (
        exrate.groupby("year_month", as_index=False)["price"]
        .mean()
        .sort_values("year_month")
    )


@st.cache_data
def monthly_basket_usd(prices: pd.DataFrame) -> pd.DataFrame:
    """Monthly average USD price across basket items. Returns year_month + usdprice."""
    df = prices[prices["commodity"].isin(BASKET)].copy()
    return (
        df.groupby("year_month", as_index=False)["usdprice"]
        .mean()
        .sort_values("year_month")
    )


@st.cache_data
def monthly_basket_lbp(prices: pd.DataFrame) -> pd.DataFrame:
    """Monthly average LBP price across basket items. Returns year_month + price."""
    df = prices[prices["commodity"].isin(BASKET)].copy()
    return (
        df.groupby("year_month", as_index=False)["price"]
        .mean()
        .sort_values("year_month")
    )


# ---------------------------------------------------------------------------
# Scatter R² — computed via Pearson, never hardcoded
# ---------------------------------------------------------------------------

@st.cache_data
def rate_vs_basket_r_squared(prices: pd.DataFrame, exrate: pd.DataFrame) -> tuple[float, float]:
    """
    Pearson R and R² between monthly avg unofficial LBP/USD rate
    and monthly avg basket USD price, over their overlapping date range.
    Returns (r, r_squared).
    """
    basket_monthly = monthly_basket_usd(prices)
    rate_monthly   = monthly_unofficial_rate(exrate)

    merged = pd.merge(basket_monthly, rate_monthly, on="year_month", suffixes=("_basket", "_rate"))
    merged = merged.dropna(subset=["usdprice", "price"])

    if len(merged) < 3:
        return float("nan"), float("nan")

    r, _ = pearsonr(merged["price"], merged["usdprice"])
    return float(r), float(r ** 2)
