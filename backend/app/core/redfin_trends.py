from __future__ import annotations

import os

DEFAULT_REDFIN_TRENDS_TABLE = "redfin_city_monthly_trends"
LEGACY_REDFIN_TRENDS_TABLE = "redfin_median_prices"


def redfin_trends_table_candidates() -> list[str]:
    """Ordered list of tables to try for Redfin city-level monthly trends.

    - Prefer the thin table by default.
    - Fall back to the legacy table for backwards compatibility.

    Override with env var `REDFIN_TRENDS_TABLE`.
    """

    preferred = (os.getenv("REDFIN_TRENDS_TABLE") or "").strip() or DEFAULT_REDFIN_TRENDS_TABLE
    candidates = [preferred, LEGACY_REDFIN_TRENDS_TABLE]

    # De-dup while preserving order.
    out: list[str] = []
    seen: set[str] = set()
    for name in candidates:
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    return out
