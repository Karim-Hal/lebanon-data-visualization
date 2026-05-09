from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import BASKET, POPULATION_GROUPS

DATA = Path(__file__).parent.parent / "data"


# ---------------------------------------------------------------------------
# Raw loaders — each decorated with @st.cache_data
# ---------------------------------------------------------------------------

@st.cache_data
def load_wfp_prices() -> pd.DataFrame:
    df = pd.read_csv(DATA / "wfp_food_prices_clean.csv", parse_dates=["date"])
    # Helper column: "YYYY-MM" string for monthly groupbys
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    return df


@st.cache_data
def load_supermarket_compare() -> pd.DataFrame:
    """Side-by-side basket comparison of 10 staples at two Lebanese
    supermarkets (anonymised "A" vs "B" as published in the source).
    Single-snapshot LBP prices.
    """
    return pd.read_csv(DATA / "supermarket_compare.csv")


@st.cache_data
def load_exchange_rate() -> pd.DataFrame:
    df = pd.read_csv(DATA / "wfp_exchange_rate.csv", parse_dates=["date"])
    df["year_month"] = df["date"].dt.to_period("M").astype(str)
    return df


@st.cache_data
def load_wdi() -> pd.DataFrame:
    df = pd.read_csv(DATA / "wdi_long.csv")
    df["Year"] = df["Year"].astype(int)
    # Value is already numeric from preprocessing; cast defensively
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    return df


@st.cache_data
def load_ipc_geo() -> pd.DataFrame:
    df = pd.read_csv(DATA / "ipc_geo.csv", parse_dates=["analysis_date"])
    return df


@st.cache_data
def load_ipc_population_groups() -> pd.DataFrame:
    df = pd.read_csv(DATA / "ipc_population_groups.csv", parse_dates=["analysis_date"])
    return df


@st.cache_data
def load_health() -> pd.DataFrame:
    df = pd.read_csv(DATA / "health_filtered.csv")
    df["YEAR (DISPLAY)"] = pd.to_numeric(df["YEAR (DISPLAY)"], errors="coerce").astype("Int64")
    df["Numeric"] = pd.to_numeric(df["Numeric"], errors="coerce")
    return df


# ---------------------------------------------------------------------------
# Cross-file alignment check: governorate names in WFP prices vs IPC geo
# Call once at startup (e.g. from app.py) — does not crash, only warns.
# ---------------------------------------------------------------------------

def check_governorate_alignment() -> list[str]:
    """Return a list of warning strings; empty list means full alignment."""
    warnings = []

    prices = load_wfp_prices()
    ipc    = load_ipc_geo()

    wfp_govs = set(prices["admin1"].dropna().unique())
    ipc_govs = set(ipc["admin1_normalized"].dropna().unique())

    only_in_wfp = wfp_govs - ipc_govs
    only_in_ipc = ipc_govs - wfp_govs

    if only_in_wfp:
        warnings.append(f"Governorates in WFP prices but not IPC geo: {sorted(only_in_wfp)}")
    if only_in_ipc:
        warnings.append(f"Governorates in IPC geo but not WFP prices: {sorted(only_in_ipc)}")

    return warnings


# ---------------------------------------------------------------------------
# Convenience: basket-filtered prices
# ---------------------------------------------------------------------------

@st.cache_data
def load_basket_prices() -> pd.DataFrame:
    df = load_wfp_prices()
    return df[df["commodity"].isin(BASKET)].copy()


@st.cache_data
def load_u5mort_mena() -> pd.DataFrame:
    df = pd.read_csv(DATA / "2322814_ALL_LATEST.csv")
    df = df[
        (df["DIM_SEX"] == "TOTAL") &
        (df["DIM_POP_WEALTH_QUINTILE"] == "TOTAL") &
        (df["DIM_TIME"] >= 2000)
    ][["DIM_TIME", "GEO_NAME_SHORT", "RATE_PER_1000_N", "RATE_PER_1000_NL", "RATE_PER_1000_NU"]].copy()
    df = df.rename(columns={
        "DIM_TIME": "year",
        "GEO_NAME_SHORT": "country",
        "RATE_PER_1000_N": "rate",
        "RATE_PER_1000_NL": "rate_low",
        "RATE_PER_1000_NU": "rate_high",
    })
    return df


@st.cache_data
def load_unhcr_refugees() -> pd.DataFrame:
    df = pd.read_csv(DATA / "unhcr_refugees_lebanon.csv", parse_dates=["as_of_date"])
    df["registered_refugees"] = pd.to_numeric(df["registered_refugees"], errors="coerce").astype("Int64")
    return df
