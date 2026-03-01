import time
from pathlib import Path

from app.services.median_house_price import fetch_median_house_price


def _cache_file_path() -> Path:
    # backend/app/tests/... -> backend/
    backend_root = Path(__file__).resolve().parents[2]
    return backend_root / "median_price_cache.json"


def main() -> None:
    addresses = [
        "1600 Pennsylvania Ave NW, Washington, DC 20500",
        "1600 Amphitheatre Parkway, Mountain View, CA 94043",
        "1 Microsoft Way, Redmond, WA 98052",
        "350 5th Ave, New York, NY 10118",
        "500 S Buena Vista St, Burbank, CA 91521",
    ]

    cache_file = _cache_file_path()
    if cache_file.exists():
        cache_file.unlink()

    rows: list[dict] = []
    for address in addresses:
        t0 = time.time()
        result_1 = fetch_median_house_price(address)
        dt_1 = time.time() - t0

        t1 = time.time()
        result_2 = fetch_median_house_price(address)
        dt_2 = time.time() - t1

        ok = isinstance(result_1, dict) and not result_1.get("error")
        cache_hit_2nd = ok and (result_1 == result_2)

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

    print("\n=== Summary (5 addresses, 2 calls each) ===")
    for idx, row in enumerate(rows, start=1):
        if row["ok"]:
            print(
                f"{idx}. OK  | hit2={row['cache_hit_2nd']} | {row['t1_s']}s -> {row['t2_s']}s | "
                f"key={row['key']} | median={row['median']} | {row['address']}"
            )
        else:
            print(
                f"{idx}. ERR | hit2=False | {row['t1_s']}s -> {row['t2_s']}s | {row['error']} | {row['address']}"
            )

    if cache_file.exists():
        print(f"\nCache file: {cache_file} | bytes={cache_file.stat().st_size}")
    else:
        print(f"\nCache file missing: {cache_file}")


if __name__ == "__main__":
    main()
