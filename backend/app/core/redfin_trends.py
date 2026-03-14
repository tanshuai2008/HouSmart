from __future__ import annotations

import os

DEFAULT_REDFIN_TRENDS_TABLE = "redfin_city_monthly_trends"
LEGACY_REDFIN_TRENDS_TABLE = "redfin_median_prices"


def redfin_trends_table_candidates() -> list[str]:
    """Return the ordered Redfin trend tables to try."""

    preferred = (os.getenv("REDFIN_TRENDS_TABLE") or "").strip() or DEFAULT_REDFIN_TRENDS_TABLE
    candidates = [preferred, LEGACY_REDFIN_TRENDS_TABLE]

    out: list[str] = []
    seen: set[str] = set()
    for name in candidates:
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    return out
