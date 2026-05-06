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

if __name__ == "__main__":
    if not results:
        print("(no smoke tests registered yet)")
        sys.exit(0)

    print(f"\n{'='*64}\nCHART SMOKE RESULTS\n{'='*64}")
    for name, (icon, status, msg) in results.items():
        print(f"{icon} {name:<32} {status}  {msg}")
    n_fail = sum(1 for _, s, _ in results.values() if s != "PASS")
    sys.exit(0 if n_fail == 0 else 1)
