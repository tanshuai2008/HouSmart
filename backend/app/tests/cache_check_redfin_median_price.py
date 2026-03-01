from __future__ import annotations

import time
from pathlib import Path

from app.services.median_house_price import get_redfin_median_price
from app.utils.cache_utils import CACHE_FILE


def main() -> None:
    # A few common cities that should exist in the Redfin city dataset.
    examples: list[tuple[str, str]] = [
        ("Seattle", "WA"),
        ("San Francisco", "CA"),
        ("Los Angeles", "CA"),
        ("Chicago", "IL"),
        ("Austin", "TX"),
    ]

    cache_path = Path(CACHE_FILE)
    if cache_path.exists():
        cache_path.unlink()

    rows: list[dict] = []
    for city, state in examples:
        t0 = time.time()
        r1 = get_redfin_median_price(city, state)
        dt1 = time.time() - t0

        t1 = time.time()
        r2 = get_redfin_median_price(city, state)
        dt2 = time.time() - t1

        ok = isinstance(r1, dict) and not r1.get("error")
        cache_hit_2nd = ok and (r1 == r2)

        rows.append(
            {
                "city": city,
                "state": state,
                "ok": ok,
                "cache_hit_2nd": cache_hit_2nd,
                "t1_s": round(dt1, 2),
                "t2_s": round(dt2, 2),
                "median_sale_price": (None if not ok else r1.get("median_sale_price")),
                "period": (None if not ok else r1.get("period")),
                "error": (None if ok else r1.get("error")),
            }
        )

    print("\n=== Redfin Cache Check (city+state, 2 calls each) ===")
    for idx, row in enumerate(rows, start=1):
        if row["ok"]:
            print(
                f"{idx}. OK  | hit2={row['cache_hit_2nd']} | {row['t1_s']}s -> {row['t2_s']}s | "
                f"price={row['median_sale_price']} | period={row['period']} | {row['city']}, {row['state']}"
            )
        else:
            print(
                f"{idx}. ERR | hit2=False | {row['t1_s']}s -> {row['t2_s']}s | {row['error']} | {row['city']}, {row['state']}"
            )

    if cache_path.exists():
        print(f"\nCache file: {cache_path} | bytes={cache_path.stat().st_size}")
    else:
        print(f"\nCache file missing: {cache_path}")


if __name__ == "__main__":
    main()
