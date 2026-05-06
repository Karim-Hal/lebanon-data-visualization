"""Lightweight smoke check for new chart figure builders.
Asserts each function returns valid Plotly JSON with expected structure.
Run: python scripts/chart_smoke.py
"""
import json
import sys
import traceback
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Stub streamlit before any src imports
from types import ModuleType
_st = ModuleType("streamlit")
_st.cache_data = lambda f: f
sys.modules["streamlit"] = _st

results = {}


def smoke(name, fn):
    try:
        fn()
        results[name] = ("✅", "PASS", "")
    except AssertionError as e:
        results[name] = ("❌", "FAIL", str(e))
    except Exception as e:
        results[name] = ("❌", "ERROR", f"{type(e).__name__}: {e}")
        traceback.print_exc()


def assert_valid_plotly_json(fig_json, expected_min_traces=1, label=""):
    obj = json.loads(fig_json)
    assert "data" in obj and "layout" in obj, f"{label}: missing data/layout"
    assert len(obj["data"]) >= expected_min_traces, (
        f"{label}: expected >= {expected_min_traces} traces, got {len(obj['data'])}"
    )


# Tests get registered here as new chart builders are added.

def t_treemap_b():
    from generate_report import _fig_treemap
    from src.data_loader import load_wfp_prices
    j = _fig_treemap(load_wfp_prices())
    assert_valid_plotly_json(j, expected_min_traces=1, label="treemap_b")
    obj = json.loads(j)
    assert obj["data"][0]["type"] == "treemap", "treemap_b: not a treemap"
    labels = obj["data"][0].get("labels", [])
    assert len(labels) >= 6 + 4 + 1, f"treemap_b: too few tiles ({len(labels)})"

smoke("treemap_b", t_treemap_b)


def t_fx_spread():
    from generate_report import _fig_fx_spread
    from src.data_loader import load_wdi, load_exchange_rate
    j = _fig_fx_spread(load_wdi(), load_exchange_rate())
    assert_valid_plotly_json(j, expected_min_traces=2, label="fx_spread")
    obj = json.loads(j)
    assert obj["layout"]["yaxis"].get("type") == "log", "fx_spread: y-axis is not log"

smoke("fx_spread", t_fx_spread)


def t_remittances():
    from generate_report import _fig_remittances
    from src.data_loader import load_wdi
    j = _fig_remittances(load_wdi())
    assert_valid_plotly_json(j, expected_min_traces=1, label="remittances")
    obj = json.loads(j)
    countries = {tr["name"] for tr in obj["data"]}
    assert "Lebanon" in countries, f"remittances: Lebanon trace missing. Got: {countries}"

smoke("remittances", t_remittances)


def t_inflation_ridge():
    from generate_report import _fig_inflation_ridge
    from src.data_loader import load_wdi
    j = _fig_inflation_ridge(load_wdi())
    assert_valid_plotly_json(j, expected_min_traces=3, label="inflation_ridge")
    obj = json.loads(j)
    types = {tr["type"] for tr in obj["data"]}
    assert "violin" in types, f"inflation_ridge: expected violin traces. Got: {types}"

smoke("inflation_ridge", t_inflation_ridge)


def t_treemap_insecurity():
    from generate_report import _fig_treemap_insecurity, _IPC_TO_GOV
    from src.data_loader import load_ipc_geo, load_ipc_population_groups
    geo = load_ipc_geo().copy()
    geo["gov"] = geo["admin1_normalized"].map(_IPC_TO_GOV)
    snap = geo[geo["analysis_date"] == geo["analysis_date"].max()]
    j = _fig_treemap_insecurity(snap, load_ipc_population_groups())
    assert_valid_plotly_json(j, expected_min_traces=1, label="treemap_a")
    obj = json.loads(j)
    assert obj["data"][0].get("type") == "treemap", "treemap_a: not a treemap"

smoke("treemap_a", t_treemap_insecurity)


def t_pop_group_time():
    from generate_report import _fig_pop_group_time
    from src.data_loader import load_ipc_population_groups
    j = _fig_pop_group_time(load_ipc_population_groups())
    assert_valid_plotly_json(j, expected_min_traces=2, label="pop_group_time")

smoke("pop_group_time", t_pop_group_time)


def t_unhcr_choropleth():
    from generate_report import _fig_unhcr_choropleth
    from src.data_loader import load_unhcr_refugees
    j = _fig_unhcr_choropleth(load_unhcr_refugees())
    assert_valid_plotly_json(j, expected_min_traces=1, label="unhcr_choropleth")

smoke("unhcr_choropleth", t_unhcr_choropleth)


def t_slope():
    from generate_report import _fig_slope
    from src.data_loader import load_health
    j = _fig_slope(load_health())
    assert_valid_plotly_json(j, expected_min_traces=2, label="slope")

smoke("slope", t_slope)


def t_sankey():
    from generate_report import _fig_sankey
    from src.data_loader import load_ipc_geo, load_ipc_population_groups
    j = _fig_sankey(load_ipc_geo(), load_ipc_population_groups())
    assert_valid_plotly_json(j, expected_min_traces=1, label="sankey")
    obj = json.loads(j)
    assert obj["data"][0]["type"] == "sankey", "sankey: not a sankey"
    nodes = obj["data"][0]["node"]["label"]
    assert len(nodes) >= 13, f"sankey: too few nodes ({len(nodes)})"

smoke("sankey", t_sankey)

if __name__ == "__main__":
    if not results:
        print("(no smoke tests registered yet)")
        sys.exit(0)

    print(f"\n{'='*64}\nCHART SMOKE RESULTS\n{'='*64}")
    for name, (icon, status, msg) in results.items():
        print(f"{icon} {name:<32} {status}  {msg}")
    n_fail = sum(1 for _, s, _ in results.values() if s != "PASS")
    sys.exit(0 if n_fail == 0 else 1)
