from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.services.median_house_price import get_median_house_price
from app.utils.cache_utils import CACHE_FILE


@dataclass(frozen=True)
class Row:
    idx: int
    city: str
    state: str
    ok: bool
    cache_hit_2nd: bool
    t1_s: float
    t2_s: float
    median_sale_price: int | None
    period: str | None
    error: str | None


def _examples_10() -> list[tuple[str, str]]:
    # Common large cities that should exist in Redfin's city dataset.
    return [
        ("Seattle", "WA"),
        ("San Francisco", "CA"),
        ("Los Angeles", "CA"),
        ("Chicago", "IL"),
        ("Austin", "TX"),
        ("New York", "NY"),
        ("Miami", "FL"),
        ("Denver", "CO"),
        ("Boston", "MA"),
        ("Atlanta", "GA"),
    ]


def _count_redfin_entries(cache_obj: dict[str, Any]) -> int:
    return sum(1 for k in cache_obj.keys() if isinstance(k, str) and k.startswith("redfin_city:"))


def main() -> int:
    data_url = os.getenv("HOUSMART_REDFIN_DATA_URL")
    if not data_url:
        print("ERROR: HOUSMART_REDFIN_DATA_URL is not set")
        return 2

    cache_path = Path(CACHE_FILE)
    if cache_path.exists():
        cache_path.unlink()

    rows: list[Row] = []
    for idx, (city, state) in enumerate(_examples_10(), start=1):
        t0 = time.perf_counter()
        r1 = get_median_house_price(city, state)
        t1 = time.perf_counter()

        r2 = get_median_house_price(city, state)
        t2 = time.perf_counter()

        ok = isinstance(r1, dict) and not r1.get("error")
        cache_hit_2nd = ok and (r1 == r2)

        median = None
        period = None
        err = None

        if ok:
            median = r1.get("median_sale_price")
            period = r1.get("period")
            # Require a real integer price.
            if not isinstance(median, int) or median <= 0:
                ok = False
                err = f"Invalid median_sale_price: {median!r}"
        else:
            err = None if not isinstance(r1, dict) else r1.get("error")

        rows.append(
            Row(
                idx=idx,
                city=city,
                state=state,
                ok=ok,
                cache_hit_2nd=cache_hit_2nd,
                t1_s=round(t1 - t0, 2),
                t2_s=round(t2 - t1, 2),
                median_sale_price=median,
                period=None if period is None else str(period),
                error=err,
            )
        )

    # Validate cache file exists and contains 10 Redfin keys.
    cache_exists = cache_path.exists()
    cache_bytes = cache_path.stat().st_size if cache_exists else 0

    cache_obj: dict[str, Any] = {}
    if cache_exists:
        try:
            cache_obj = json.loads(cache_path.read_text("utf-8"))
            if not isinstance(cache_obj, dict):
                cache_obj = {}
        except Exception:
            cache_obj = {}

    redfin_entries = _count_redfin_entries(cache_obj)

    # Report
    print("\n=== Validate Redfin Median Price + Cache (10 examples) ===")
    print(f"data_url={data_url}")
    print(f"cache_file={cache_path} exists={cache_exists} bytes={cache_bytes} redfin_entries={redfin_entries}")

    failures = 0
    for row in rows:
        if row.ok:
            print(
                f"{row.idx}. OK  | hit2={row.cache_hit_2nd} | {row.t1_s}s -> {row.t2_s}s | "
                f"price={row.median_sale_price} | period={row.period} | {row.city}, {row.state}"
            )
        else:
            failures += 1
            print(
                f"{row.idx}. ERR | hit2={row.cache_hit_2nd} | {row.t1_s}s -> {row.t2_s}s | "
                f"{row.error} | {row.city}, {row.state}"
            )

    if not cache_exists:
        print("\nFAIL: cache file was not created")
        return 1

    if redfin_entries < 10:
        print(f"\nFAIL: expected >=10 redfin cache entries, got {redfin_entries}")
        return 1

    if failures:
        print(f"\nFAIL: {failures} / 10 lookups failed")
        return 1

    if any(not r.cache_hit_2nd for r in rows):
        print("\nFAIL: at least one lookup did not hit cache on the 2nd call")
        return 1

    print("\nPASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
