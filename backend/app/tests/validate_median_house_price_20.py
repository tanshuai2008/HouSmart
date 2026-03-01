from __future__ import annotations

import argparse
import json
import os
import statistics
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.services.median_house_price import fetch_median_house_price
from app.utils.cache_utils import CACHE_FILE, load_cache


@dataclass(frozen=True)
class Row:
    idx: int
    address: str
    ok: bool
    pre_cached: bool
    cache_hit_2nd: bool
    t1_s: float
    t2_s: float
    key: str | None
    median: int | None
    redfin_median_sale_price: int | None
    redfin_period: str | None
    error: str | None


def _cache_key_from_result(result: dict[str, Any]) -> str | None:
    state = result.get("state")
    county = result.get("county")
    tract = result.get("tract")
    if not (state and county and tract):
        return None
    return f"{state}:{county}:{tract}"


def _safe_float(x: Any) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _addresses_20() -> list[str]:
    # Chosen as well-known US addresses that the Census geocoder usually resolves reliably.
    return [
        "1600 Pennsylvania Ave NW, Washington, DC 20500",
        "350 5th Ave, New York, NY 10118",
        "405 Lexington Ave, New York, NY 10174",
        "11 Wall St, New York, NY 10005",
        "30 Rockefeller Plaza, New York, NY 10112",
        "1000 5th Ave, New York, NY 10028",
        "200 Central Park West, New York, NY 10024",
        "111 8th Ave, New York, NY 10011",
        "233 S Wacker Dr, Chicago, IL 60606",
        "111 S Michigan Ave, Chicago, IL 60603",
        "201 E Randolph St, Chicago, IL 60602",
        "400 Broad St, Seattle, WA 98109",
        "1 Microsoft Way, Redmond, WA 98052",
        "1600 Amphitheatre Pkwy, Mountain View, CA 94043",
        "901 Cherry Ave, San Bruno, CA 94066",
        "1 Dr Carlton B Goodlett Pl, San Francisco, CA 94102",
        "151 3rd St, San Francisco, CA 94103",
        "100 N Main St, Los Angeles, CA 90012",
        "700 Exposition Park Dr, Los Angeles, CA 90037",
        "1100 Congress Ave, Austin, TX 78701",
    ]


def _read_cache_stats(cache_path: Path) -> dict[str, Any]:
    if not cache_path.exists():
        return {"exists": False, "bytes": 0, "entries": 0}
    try:
        cache = load_cache()
        entries = len(cache) if isinstance(cache, dict) else 0
    except Exception:
        entries = 0
    return {"exists": True, "bytes": cache_path.stat().st_size, "entries": entries}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate median_house_price with 20 example addresses and cache behavior."
    )
    parser.add_argument(
        "--keep-cache-changes",
        action="store_true",
        help="Do not restore the original median_price_cache.json after validation.",
    )
    parser.add_argument(
        "--use-existing-cache",
        action="store_true",
        help="Do not wipe cache before running (may mix old/new entries).",
    )
    parser.add_argument(
        "--enable-redfin",
        action="store_true",
        help="Enable Redfin lookup (may download a large dataset).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON report to stdout.",
    )
    args = parser.parse_args()

    # Make runs fast/deterministic by default. Redfin is optional and huge.
    if not args.enable_redfin:
        os.environ["HOUSMART_REDFIN_MAX_SECONDS"] = "0"

    cache_path = Path(CACHE_FILE)
    backup_path = cache_path.with_suffix(cache_path.suffix + ".validation.bak")

    before_stats = _read_cache_stats(cache_path)

    # Backup + optionally wipe the cache for a clean cold->warm comparison.
    restored = False
    try:
        if cache_path.exists():
            backup_path.write_bytes(cache_path.read_bytes())
        if (not args.use_existing_cache) and cache_path.exists():
            cache_path.unlink()

        rows: list[Row] = []
        addrs = _addresses_20()

        for idx, address in enumerate(addrs, start=1):
            # Determine pre-cache hit by computing key from a cached response, if any.
            # Since we don't have the tract until after geocoding, we infer pre_cached
            # by checking presence of the computed key after the first successful response.
            t0 = time.perf_counter()
            result_1 = fetch_median_house_price(address)
            t1 = time.perf_counter()

            t2 = time.perf_counter()
            result_2 = fetch_median_house_price(address)
            t3 = time.perf_counter()

            ok = isinstance(result_1, dict) and not result_1.get("error")
            cache_hit_2nd = ok and (result_1 == result_2)

            key = None
            median = None
            redfin_median_sale_price = None
            redfin_period = None
            err = None
            pre_cached = False

            if ok:
                key = _cache_key_from_result(result_1)
                median = result_1.get("median_house_price")
                redfin_median_sale_price = result_1.get("redfin_median_sale_price")
                redfin_period = result_1.get("redfin_period")

                # Determine whether this key existed *before* this run by checking the backup.
                if backup_path.exists():
                    try:
                        backup_cache = json.loads(backup_path.read_text("utf-8"))
                        if isinstance(backup_cache, dict) and key is not None:
                            pre_cached = key in backup_cache
                    except Exception:
                        pre_cached = False

                # Basic sanity checks on coordinates & median.
                coords = result_1.get("coordinates") or {}
                lat = _safe_float(coords.get("lat"))
                lng = _safe_float(coords.get("lng"))
                if lat is None or lng is None:
                    ok = False
                    err = "Invalid coordinates in response"
                elif not isinstance(median, int) or median <= 0:
                    ok = False
                    err = f"Invalid median_house_price: {median!r}"
            else:
                err = None if not isinstance(result_1, dict) else result_1.get("error")

            rows.append(
                Row(
                    idx=idx,
                    address=address,
                    ok=ok,
                    pre_cached=pre_cached,
                    cache_hit_2nd=cache_hit_2nd,
                    t1_s=round(t1 - t0, 3),
                    t2_s=round(t3 - t2, 3),
                    key=key,
                    median=median if ok else None,
                    redfin_median_sale_price=redfin_median_sale_price if ok else None,
                    redfin_period=redfin_period if ok else None,
                    error=err if not ok else None,
                )
            )

        after_stats = _read_cache_stats(cache_path)

        ok_rows = [r for r in rows if r.ok]
        t1_list = [r.t1_s for r in ok_rows]
        t2_list = [r.t2_s for r in ok_rows]

        summary: dict[str, Any] = {
            "settings": {
                "enable_redfin": bool(args.enable_redfin),
                "use_existing_cache": bool(args.use_existing_cache),
                "keep_cache_changes": bool(args.keep_cache_changes),
                "cache_file": str(cache_path),
            },
            "cache_stats": {"before": before_stats, "after": after_stats},
            "results": {
                "total": len(rows),
                "ok": len(ok_rows),
                "errors": len(rows) - len(ok_rows),
                "cache_hit_2nd": sum(1 for r in rows if r.cache_hit_2nd),
                "timings_ok": {
                    "t1_mean_s": (round(statistics.mean(t1_list), 3) if t1_list else None),
                    "t1_median_s": (
                        round(statistics.median(t1_list), 3) if t1_list else None
                    ),
                    "t2_mean_s": (round(statistics.mean(t2_list), 3) if t2_list else None),
                    "t2_median_s": (
                        round(statistics.median(t2_list), 3) if t2_list else None
                    ),
                },
            },
            "rows": [r.__dict__ for r in rows],
        }

        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print("\n=== Median House Price Validation (20 addresses, 2 calls each) ===")
            print(
                f"Redfin enabled: {args.enable_redfin} | "
                f"Used existing cache: {args.use_existing_cache} | "
                f"Will restore cache: {not args.keep_cache_changes}"
            )
            print(
                f"Cache before: exists={before_stats['exists']} entries={before_stats['entries']} bytes={before_stats['bytes']}"
            )
            print(
                f"Cache after : exists={after_stats['exists']} entries={after_stats['entries']} bytes={after_stats['bytes']}"
            )
            print(
                f"OK: {summary['results']['ok']}/{summary['results']['total']} | "
                f"Cache hit on 2nd call: {summary['results']['cache_hit_2nd']}/{summary['results']['total']}"
            )
            if summary["results"]["timings_ok"]["t1_mean_s"] is not None:
                print(
                    "Timing (OK only): "
                    f"t1 mean={summary['results']['timings_ok']['t1_mean_s']}s, "
                    f"median={summary['results']['timings_ok']['t1_median_s']}s | "
                    f"t2 mean={summary['results']['timings_ok']['t2_mean_s']}s, "
                    f"median={summary['results']['timings_ok']['t2_median_s']}s"
                )

            print("\n--- Per-address ---")
            for r in rows:
                if r.ok:
                    print(
                        f"{r.idx:02d}. OK  | pre_cached={r.pre_cached} | hit2={r.cache_hit_2nd} | "
                        f"{r.t1_s}s -> {r.t2_s}s | key={r.key} | median={r.median} | {r.address}"
                    )
                else:
                    print(
                        f"{r.idx:02d}. ERR | pre_cached={r.pre_cached} | hit2=False | "
                        f"{r.t1_s}s -> {r.t2_s}s | {r.error} | {r.address}"
                    )

        return 0
    finally:
        # Restore original cache unless the user requested to keep changes.
        if (not args.keep_cache_changes) and backup_path.exists():
            try:
                if cache_path.exists():
                    cache_path.unlink()
            except OSError:
                pass
            try:
                cache_path.write_bytes(backup_path.read_bytes())
                restored = True
            except OSError:
                restored = False
            try:
                backup_path.unlink()
            except OSError:
                pass

        if restored and not args.json:
            print("\n(Cache restored to pre-validation state.)")


if __name__ == "__main__":
    raise SystemExit(main())
