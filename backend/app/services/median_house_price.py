from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys
from pathlib import Path
from typing import Any

import pandas as pd

# =========================================================
# 🔥 YOUR FULL PARQUET DATASET (HUGGING FACE)
# =========================================================
_REDFIN_DEFAULT_URL = (
    "https://huggingface.co/datasets/KJJ231/redfin-data/"
    "resolve/main/redfin_full.parquet"
)

# =========================================================
# Import cache utilities
# =========================================================
_BACKEND_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT_FOR_IMPORTS))

from app.utils.cache_utils import get_cached, set_cache

# =========================================================
# GLOBAL DATAFRAME (LOAD ONCE)
# =========================================================
_REDFIN_DF: pd.DataFrame | None = None


def _effective_redfin_data_url() -> str:
    return os.getenv("HOUSMART_REDFIN_DATA_URL", _REDFIN_DEFAULT_URL)


# =========================================================
# LOAD DATASET ONCE (VERY IMPORTANT)
# =========================================================
def _load_redfin_df() -> pd.DataFrame:
    global _REDFIN_DF

    if _REDFIN_DF is not None:
        return _REDFIN_DF

    url = _effective_redfin_data_url()

    print("Loading Redfin dataset (one-time)...")

    df = pd.read_parquet(url)

    # Normalize column names
    df.columns = df.columns.str.lower()

    # Use state_code if present
    if "state_code" in df.columns:
        df["state"] = df["state_code"]

    _REDFIN_DF = df

    print("Dataset loaded successfully!")

    return df


def _redfin_cache_key(*, city: str, state: str) -> str:
    return f"redfin_city:{state.strip().upper()}:{city.strip().lower()}"


# =========================================================
# PUBLIC API FUNCTION
# =========================================================
def get_redfin_median_price(city: str, state: str) -> dict[str, Any]:

    if not city or not str(city).strip():
        return {"error": "City is required"}

    if not state or not str(state).strip():
        return {"error": "State is required"}

    city = city.strip()
    state = state.strip().upper()

    key = _redfin_cache_key(city=city, state=state)

    # -------- Cache check --------
    cached = get_cached(key)
    if isinstance(cached, dict) and not cached.get("error"):
        cached.setdefault("source", "Redfin Data Center")
        cached["retrieved_from"] = {"url": _effective_redfin_data_url()}
        set_cache(key, cached)
        return cached

    # -------- Load dataset once --------
    df = _load_redfin_df()

    # -------- Filter city/state --------
    subset = df[
        (df["city"].str.lower() == city.lower())
        & (df["state"].str.upper() == state.upper())
    ]

    if subset.empty:
        return {"error": "No Redfin data found for this location"}

    # -------- Latest record --------
    latest = subset.sort_values("period_end").iloc[-1]

    price = None
    try:
        if pd.notna(latest["median_sale_price"]):
            price = int(latest["median_sale_price"])
    except Exception:
        pass

    result: dict[str, Any] = {
        "city": city,
        "state": state,
        "median_sale_price": price,
        "period": str(latest["period_end"]),
        "source": "Redfin Data Center",
        "retrieved_from": {"url": _effective_redfin_data_url()},
    }

    set_cache(key, result)
    return result


def get_median_house_price(city: str, state: str) -> dict[str, Any]:
    return get_redfin_median_price(city, state)


# =========================================================
# CLI ENTRY
# =========================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch Redfin median sale price from full Parquet dataset"
    )

    parser.add_argument("--city", "-c", type=str)
    parser.add_argument("--state", "-s", type=str)
    parser.add_argument("--raw", action="store_true")

    args = parser.parse_args()

    city_in = (args.city or input("Enter city: ")).strip()
    state_in = (args.state or input("Enter state code: ")).strip()

    resp = get_redfin_median_price(city_in, state_in)

    if args.raw or resp.get("error"):
        print(resp)
    else:
        print(
            {
                "date": _dt.date.today().isoformat(),
                "place_name": f"{resp['city']}, {resp['state']}",
                "period": resp["period"],
                "median_price": resp["median_sale_price"],
            }
        )