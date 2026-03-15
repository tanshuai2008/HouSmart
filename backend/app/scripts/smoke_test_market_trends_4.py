from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

import requests


# Allow running from any directory
_BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.config.db import require_supabase


def _safe(val: Any) -> str:
    if val is None:
        return ""
    s = str(val)
    return s.replace("\n", " ").strip()


def main() -> None:
    base_url = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    months = int(os.getenv("MARKET_TRENDS_MONTHS", "24"))

    supabase = require_supabase()

    props_resp = supabase.table("user_properties").select("*").limit(12).execute()
    props = props_resp.data or []
    if len(props) < 1:
        raise SystemExit("No rows found in Supabase table 'user_properties'.")

    print(f"Using backend: {base_url}")
    print("Testing graph endpoint(s) using user_properties rows:")
    print("- /api/market-trends")
    print()

    successes = 0
    for i, prop in enumerate(props, start=1):
        prop_id = prop.get("id") or prop.get("property_id")
        prop_id = str(prop_id) if prop_id is not None else ""

        addr = _safe(prop.get("formatted_address") or prop.get("full_address") or prop.get("address"))
        city = _safe(prop.get("city"))
        state = _safe(prop.get("state"))
        if not prop_id:
            continue

        url = f"{base_url}/api/market-trends"
        r = requests.get(url, params={"property_id": prop_id, "months": months}, timeout=45)

        ok = r.status_code == 200
        cache_control = _safe(r.headers.get("cache-control"))
        if not ok:
            print(f"{i}. property_id={prop_id} ({city}, {state})")
            print(f"   address={addr}")
            print(f"   cache-control={cache_control or '(missing)'}")
            print(f"   ERROR {r.status_code}: {_safe(r.text)[:200]}")
            print()
            continue

        data = r.json() if r.content else {}
        price_trend = data.get("priceTrend") or []
        revenue_expenses = data.get("revenueExpenses") or []

        print(f"{i}. property_id={prop_id} ({city}, {state})")
        print(f"   address={addr}")
        print(f"   cache-control={cache_control or '(missing)'}")
        print(f"   market-trends: priceTrend={len(price_trend)} revenueExpenses={len(revenue_expenses)}")

        # Print one sample point for sanity.
        if revenue_expenses:
            print(f"   sample revenueExpenses[0]: {revenue_expenses[0]}")
        if price_trend:
            print(f"   sample priceTrend[0]: {price_trend[0]}")

        print()

        # Stop after a few successful real-data checks to keep runtime predictable.
        if revenue_expenses:
            successes += 1
        if successes >= 4:
            break


if __name__ == "__main__":
    main()
