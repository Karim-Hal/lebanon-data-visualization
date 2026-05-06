import sys
import traceback
from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent.parent / "data"

BASKET = [
    "Bread (pita)",
    "Rice (imported, Egyptian)",
    "Oil (sunflower)",
    "Eggs",
    "Meat (chicken, whole, frozen)",
    "Wheat flour",
]

POPULATION_GROUPS = [
    "Lebanese residents",
    "Syrian refugees",
    "Palestinian Refugees",
    "Newly displaced Syrian",
    "Others",
]

ADMIN1_NORMALIZED = {
    "Akkar", "Baalbek-El Hermel", "Beirut", "Bekaa",
    "El Nabatieh", "Mount Lebanon", "North", "South",
}

WDI_COUNTRIES = {
    "Lebanon", "Jordan", "Egypt, Arab Rep.",
    "Syrian Arab Republic", "Saudi Arabia", "United Arab Emirates",
}

WDI_SERIES = {"FP.CPI.TOTL.ZG", "NY.GDP.MKTP.CD", "PA.NUS.FCRF"}

results = {}


def run(name, fn):
    try:
        fn()
        results[name] = ("✅", "PASS", "")
    except AssertionError as e:
        results[name] = ("❌", "FAIL", str(e))
    except Exception as e:
        results[name] = ("❌", "ERROR", f"{type(e).__name__}: {e}")


# ---------------------------------------------------------------------------
# wfp_food_prices_clean.csv
# ---------------------------------------------------------------------------
def check_wfp_prices():
    path = DATA / "wfp_food_prices_clean.csv"
    assert path.exists(), f"File not found: {path}"

    df = pd.read_csv(path, parse_dates=["date"])
    print(f"\n[wfp_food_prices_clean] shape={df.shape}")
    print(df.head(3).to_string())
    print("columns:", df.columns.tolist())
    print("pricetype unique:", df["pricetype"].unique())
    print("category unique:", df["category"].unique())
    print("commodity sample:", df["commodity"].unique()[:10])

    assert pd.api.types.is_datetime64_any_dtype(df["date"]), \
        "'date' did not parse as datetime"
    assert (df["pricetype"] == "Retail").all(), \
        f"Non-retail rows found: {df[df['pricetype'] != 'Retail']['pricetype'].unique()}"
    assert "non-food" not in df["category"].str.lower().unique(), \
        "non-food category leaked in"
    assert "Exchange rate (unofficial)" not in df["commodity"].unique(), \
        "Exchange rate rows leaked into food prices"
    assert "baseline_usd" in df.columns, "Missing column: baseline_usd"
    assert "price_index" in df.columns, "Missing column: price_index"

    basket_in_data = set(df["commodity"].unique())
    missing_basket = [b for b in BASKET if b not in basket_in_data]
    assert not missing_basket, f"Missing basket items: {missing_basket}"

    rows_2019 = df[df["date"].dt.year == 2019]
    basket_2019 = rows_2019[rows_2019["commodity"].isin(BASKET)]
    assert not basket_2019.empty, "No 2019 rows found for basket commodities"
    annual_mean = basket_2019["price_index"].mean()
    assert abs(annual_mean - 100) <= 10, \
        f"2019 basket price_index annual mean = {annual_mean:.2f}, expected ~100"

    print(f"2019 basket price_index annual mean: {annual_mean:.2f}")


run("wfp_food_prices_clean", check_wfp_prices)


# ---------------------------------------------------------------------------
# wfp_exchange_rate.csv
# ---------------------------------------------------------------------------
def check_wfp_exchange_rate():
    path = DATA / "wfp_exchange_rate.csv"
    assert path.exists(), f"File not found: {path}"

    df = pd.read_csv(path, parse_dates=["date"])
    print(f"\n[wfp_exchange_rate] shape={df.shape}")
    print(df.head(3).to_string())
    print("columns:", df.columns.tolist())
    print("commodity unique:", df["commodity"].unique())

    assert (df["commodity"] == "Exchange rate (unofficial)").all(), \
        "Rows with commodity != 'Exchange rate (unofficial)' found"
    assert pd.api.types.is_datetime64_any_dtype(df["date"]), \
        "'date' did not parse as datetime"

    min_year = df["date"].dt.year.min()
    max_year = df["date"].dt.year.max()
    if min_year > 2019:
        print(f"  NOTE: exchange rate starts {min_year} (unofficial rate didn't exist pre-crisis)")
    assert max_year >= 2024, f"Date range ends at {max_year}, expected ≥ 2024"

    assert "price" in df.columns, "Missing column: price"
    assert pd.api.types.is_numeric_dtype(df["price"]), "'price' is not numeric"
    assert (df["price"] > 0).all(), "Non-positive price values found"

    print(f"Date range: {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"Price range: {df['price'].min():,.0f} → {df['price'].max():,.0f}")


run("wfp_exchange_rate", check_wfp_exchange_rate)


# ---------------------------------------------------------------------------
# wdi_long.csv
# ---------------------------------------------------------------------------
def check_wdi_long():
    path = DATA / "wdi_long.csv"
    assert path.exists(), f"File not found: {path}"

    df = pd.read_csv(path)
    print(f"\n[wdi_long] shape={df.shape}")
    print(df.head(3).to_string())
    print("columns:", df.columns.tolist())
    print("Country Name unique:", df["Country Name"].unique())
    print("Series Code sample:", df["Series Code"].unique()[:10])

    countries_in_data = set(df["Country Name"].unique())
    missing_countries = WDI_COUNTRIES - countries_in_data
    assert not missing_countries, f"Missing countries: {missing_countries}"
    extra_countries = countries_in_data - WDI_COUNTRIES
    if extra_countries:
        print(f"  WARNING: extra countries in WDI: {extra_countries}")

    assert pd.api.types.is_integer_dtype(df["Year"]) or \
        df["Year"].astype(str).str.match(r"^\d{4}$").all(), \
        "'Year' is not integer"
    df["Year"] = df["Year"].astype(int)

    assert not df["Value"].isin([".."]  ).any(), "'..' strings found in Value column"
    assert pd.api.types.is_numeric_dtype(df["Value"]), "'Value' is not numeric"
    assert df["Value"].notna().all(), "NaN values found in Value column"

    series_in_data = set(df["Series Code"].unique())
    missing_series = WDI_SERIES - series_in_data
    assert not missing_series, f"Missing series codes: {missing_series}"

    lbn_inf = df[
        (df["Country Name"] == "Lebanon") &
        (df["Series Code"] == "FP.CPI.TOTL.ZG") &
        (df["Year"] == 2023)
    ]
    assert not lbn_inf.empty, "Lebanon 2023 inflation row missing"
    inf_val = lbn_inf["Value"].iloc[0]
    assert abs(inf_val - 221.3) <= 20, \
        f"Lebanon 2023 inflation = {inf_val:.1f}%, expected ~221.3%"
    print(f"Lebanon 2023 inflation: {inf_val:.1f}%")


run("wdi_long", check_wdi_long)


# ---------------------------------------------------------------------------
# ipc_geo.csv
# ---------------------------------------------------------------------------
def check_ipc_geo():
    path = DATA / "ipc_geo.csv"
    assert path.exists(), f"File not found: {path}"

    df = pd.read_csv(path, parse_dates=["analysis_date"])
    print(f"\n[ipc_geo] shape={df.shape}")
    print(df.head(3).to_string())
    print("columns:", df.columns.tolist())

    if "Level 1" in df.columns:
        level1_vals = df["Level 1"].dropna().unique()
        pop_group_leak = [v for v in level1_vals if v in POPULATION_GROUPS]
        assert not pop_group_leak, \
            f"Population group rows leaked into ipc_geo 'Level 1': {pop_group_leak}"
    else:
        print("  INFO: no 'Level 1' column in ipc_geo (may be named differently)")

    assert "admin1_normalized" in df.columns, "Missing column: admin1_normalized"
    assert pd.api.types.is_datetime64_any_dtype(df["analysis_date"]), \
        "'analysis_date' did not parse as datetime"

    min_date = df["analysis_date"].min()
    max_date = df["analysis_date"].max()
    assert min_date <= pd.Timestamp("2022-09-30"), \
        f"analysis_date starts {min_date.date()}, expected ≤ Sep 2022"
    if max_date < pd.Timestamp("2025-10-01"):
        print(f"  NOTE: ipc_geo ends {max_date.date()} — governorate data lags population-groups file (expected)")

    normalized_in_data = set(df["admin1_normalized"].dropna().unique())
    invalid = normalized_in_data - ADMIN1_NORMALIZED
    assert not invalid, \
        f"admin1_normalized contains values outside allowed set: {invalid}"

    print(f"analysis_date range: {min_date.date()} → {max_date.date()}")
    print(f"admin1_normalized values: {sorted(normalized_in_data)}")


run("ipc_geo", check_ipc_geo)


# ---------------------------------------------------------------------------
# ipc_population_groups.csv
# ---------------------------------------------------------------------------
def check_ipc_population_groups():
    path = DATA / "ipc_population_groups.csv"
    assert path.exists(), f"File not found: {path}"

    df = pd.read_csv(path, parse_dates=["analysis_date"])
    print(f"\n[ipc_population_groups] shape={df.shape}")
    print(df.head(3).to_string())
    print("columns:", df.columns.tolist())
    print("Level 1 unique:", df["Level 1"].unique() if "Level 1" in df.columns else "N/A")

    assert "Level 1" in df.columns, "Missing column: Level 1"
    invalid_groups = set(df["Level 1"].unique()) - set(POPULATION_GROUPS)
    assert not invalid_groups, \
        f"'Level 1' contains values outside POPULATION_GROUPS: {invalid_groups}"

    assert pd.api.types.is_datetime64_any_dtype(df["analysis_date"]), \
        "'analysis_date' did not parse as datetime"

    latest_date = df["analysis_date"].max()
    latest = df[df["analysis_date"] == latest_date]
    assert "Lebanese residents" in latest["Level 1"].values, \
        f"'Lebanese residents' missing from most recent snapshot ({latest_date.date()})"

    print(f"Most recent snapshot: {latest_date.date()}")
    print(f"Groups in latest snapshot: {latest['Level 1'].unique().tolist()}")


run("ipc_population_groups", check_ipc_population_groups)


# ---------------------------------------------------------------------------
# health_filtered.csv
# ---------------------------------------------------------------------------
HEALTH_KEYWORDS = [
    "stunting", "wasting", "anaemia", "anemia", "mortality",
    "underweight", "overweight", "obesity", "malnutrition",
]


def check_health_filtered():
    path = DATA / "health_filtered.csv"
    assert path.exists(), f"File not found: {path}"

    df = pd.read_csv(path)
    print(f"\n[health_filtered] shape={df.shape}")
    print(df.head(3).to_string())
    print("columns:", df.columns.tolist())
    print("COUNTRY (CODE) unique:", df["COUNTRY (CODE)"].unique())

    assert (df["COUNTRY (CODE)"] == "LBN").all(), \
        f"Non-LBN country codes found: {df[df['COUNTRY (CODE)'] != 'LBN']['COUNTRY (CODE)'].unique()}"

    if "DIMENSION (TYPE)" in df.columns and "DIMENSION (CODE)" in df.columns:
        sex_rows = df[df["DIMENSION (TYPE)"] == "SEX"]
        if not sex_rows.empty:
            non_btsx = sex_rows[sex_rows["DIMENSION (CODE)"] != "SEX_BTSX"]
            assert non_btsx.empty, \
                f"SEX dimension rows with code != SEX_BTSX found: {non_btsx['DIMENSION (CODE)'].unique()}"

    assert "GHO (DISPLAY)" in df.columns, "Missing column: GHO (DISPLAY)"
    gho_values = df["GHO (DISPLAY)"].str.lower()
    matched = gho_values.apply(lambda v: any(kw in v for kw in HEALTH_KEYWORDS))
    assert matched.any(), \
        f"No GHO (DISPLAY) values matched health keywords. Sample: {df['GHO (DISPLAY)'].unique()[:5]}"
    print(f"GHO (DISPLAY) unique count: {df['GHO (DISPLAY)'].nunique()}")
    print(f"GHO (DISPLAY) values: {df['GHO (DISPLAY)'].unique().tolist()}")

    assert "YEAR (DISPLAY)" in df.columns, "Missing column: YEAR (DISPLAY)"
    df["YEAR (DISPLAY)"] = pd.to_numeric(df["YEAR (DISPLAY)"], errors="coerce")
    assert df["YEAR (DISPLAY)"].notna().all(), "Non-integer values in YEAR (DISPLAY)"

    assert "Numeric" in df.columns, "Missing column: Numeric"
    df["Numeric"] = pd.to_numeric(df["Numeric"], errors="coerce")
    assert pd.api.types.is_numeric_dtype(df["Numeric"]), "'Numeric' is not numeric"


run("health_filtered", check_health_filtered)


# ---------------------------------------------------------------------------
# Remittances (BX.TRF.PWKR.DT.GD.ZS) appended to wdi_long.csv
# ---------------------------------------------------------------------------
def check_remittances():
    path = DATA / "wdi_long.csv"
    df = pd.read_csv(path)
    rem = df[df["Series Code"] == "BX.TRF.PWKR.DT.GD.ZS"]
    assert not rem.empty, "Remittance series BX.TRF.PWKR.DT.GD.ZS missing from wdi_long.csv"
    countries = set(rem["Country Name"].unique())
    assert "Lebanon" in countries, f"Lebanon missing from remittance rows. Found: {countries}"
    lbn = rem[rem["Country Name"] == "Lebanon"]
    assert lbn["Year"].between(2010, 2024).any(), "No Lebanon remittance values in 2010-2024 range"


run("remittances", check_remittances)


# ---------------------------------------------------------------------------
# UNHCR registered refugees by governorate
# ---------------------------------------------------------------------------
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


run("unhcr_refugees", check_unhcr)


# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print(f"{'Check':<35} {'Status':<8} {'Detail'}")
print("=" * 60)
for name, (icon, status, detail) in results.items():
    detail_str = detail[:60] if detail else ""
    print(f"{icon} {name:<33} {status:<8} {detail_str}")
print("=" * 60)

failures = [n for n, (icon, _, _) in results.items() if icon == "❌"]
if failures:
    print(f"\n{len(failures)} check(s) failed. Fix data before proceeding.")
    sys.exit(1)
else:
    print(f"\nAll {len(results)} checks passed.")
    sys.exit(0)
