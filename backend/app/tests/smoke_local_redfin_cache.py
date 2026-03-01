from __future__ import annotations

import os
import time
from pathlib import Path

from app.services.median_house_price import get_redfin_median_price
from app.utils.cache_utils import CACHE_FILE


def main() -> None:
    data_url = os.getenv("HOUSMART_REDFIN_DATA_URL")
    if not data_url:
        raise SystemExit(
            "HOUSMART_REDFIN_DATA_URL is not set. "
            "Example: set it to your local city_market_tracker.tsv000 path."
        )

    cache_path = Path(CACHE_FILE)
    if cache_path.exists():
        cache_path.unlink()

    city = os.getenv("HOUSMART_SMOKE_CITY", "St. Augusta")
    state = os.getenv("HOUSMART_SMOKE_STATE", "MN")

    t0 = time.perf_counter()
    r1 = get_redfin_median_price(city, state)
    t1 = time.perf_counter()

    r2 = get_redfin_median_price(city, state)
    t2 = time.perf_counter()

    print({
        "city": city,
        "state": state,
        "first_s": round(t1 - t0, 2),
        "second_s": round(t2 - t1, 2),
        "cache_file_exists": cache_path.exists(),
        "cache_bytes": (cache_path.stat().st_size if cache_path.exists() else 0),
        "same_result": r1 == r2,
        "first_error": r1.get("error"),
        "second_error": r2.get("error"),
        "median_sale_price": r2.get("median_sale_price"),
        "period": r2.get("period"),
        "retrieved_from": r2.get("retrieved_from"),
    })


if __name__ == "__main__":
    main()
