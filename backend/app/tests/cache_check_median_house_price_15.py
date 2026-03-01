import os
import time
from pathlib import Path

from app.services.median_house_price import fetch_median_house_price


def _cache_file_path() -> Path:
    # backend/app/tests/... -> backend/
    backend_root = Path(__file__).resolve().parents[2]
    return backend_root / "median_price_cache.json"


def main() -> None:
    # Keep this test fast and deterministic by skipping the huge Redfin dataset.
    os.environ.setdefault("HOUSMART_REDFIN_MAX_SECONDS", "0")

    addresses = [
        "350 5th Ave, New York, NY 10118",  # Empire State Building
        "405 Lexington Ave, New York, NY 10174",  # Chrysler Building
        "11 Wall St, New York, NY 10005",  # NYSE
        "30 Rockefeller Plaza, New York, NY 10112",
        "1600 Amphitheatre Pkwy, Mountain View, CA 94043",
        "10600 N Tantau Ave, Cupertino, CA 95014",  # Apple Park Visitor Center
        "1 Market St, San Francisco, CA 94105",
        "111 8th Ave, New York, NY 10011",
        "200 Central Park West, New York, NY 10024",
        "500 S Buena Vista St, Burbank, CA 91521",
        "111 S Michigan Ave, Chicago, IL 60603",  # Art Institute of Chicago
        "233 S Wacker Dr, Chicago, IL 60606",  # Willis Tower
        "600 Montgomery St, San Francisco, CA 94111",  # Coit Tower area
        "700 Exposition Park Dr, Los Angeles, CA 90037",  # USC area
        "400 Broad St, Seattle, WA 98109",  # Space Needle
    ]

    cache_file = _cache_file_path()
    if cache_file.exists():
        cache_file.unlink()

    rows: list[dict] = []
    ok_count = 0
    cache_hit_count = 0

    for address in addresses:
        t0 = time.time()
        result_1 = fetch_median_house_price(address)
        dt_1 = time.time() - t0

        t1 = time.time()
        result_2 = fetch_median_house_price(address)
        dt_2 = time.time() - t1

        ok = isinstance(result_1, dict) and not result_1.get("error")
        if ok:
            ok_count += 1

        cache_hit_2nd = ok and (result_1 == result_2)
        if cache_hit_2nd:
            cache_hit_count += 1

        key = None
        if ok:
            state = result_1.get("state")
            county = result_1.get("county")
            tract = result_1.get("tract")
            if state and county and tract:
                key = f"{state}:{county}:{tract}"

        rows.append(
            {
                "address": address,
                "ok": ok,
                "cache_hit_2nd": cache_hit_2nd,
                "t1_s": round(dt_1, 2),
                "t2_s": round(dt_2, 2),
                "key": key,
                "median": (None if not ok else result_1.get("median_house_price")),
                "error": (None if ok else result_1.get("error")),
            }
        )

    print("\n=== Summary (15 addresses, 2 calls each) ===")
    for idx, row in enumerate(rows, start=1):
        if row["ok"]:
            print(
                f"{idx:02d}. OK  | hit2={row['cache_hit_2nd']} | {row['t1_s']}s -> {row['t2_s']}s | "
                f"key={row['key']} | median={row['median']} | {row['address']}"
            )
        else:
            print(
                f"{idx:02d}. ERR | hit2=False | {row['t1_s']}s -> {row['t2_s']}s | {row['error']} | {row['address']}"
            )

    print(
        f"\nOK results: {ok_count}/{len(addresses)} | Cache hits on 2nd call: {cache_hit_count}/{len(addresses)}"
    )

    if cache_file.exists():
        print(f"Cache file: {cache_file} | bytes={cache_file.stat().st_size}")
    else:
        print(f"Cache file missing: {cache_file}")


if __name__ == "__main__":
    main()
