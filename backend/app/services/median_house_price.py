
from __future__ import annotations

from datetime import date
import sys

from app.config.db import require_supabase
from app.core.config import settings
from app.core.redfin_trends import redfin_trends_table_candidates
from app.services.geocode import geocode_address
from app.scripts.ingest_redfin import ingest_redfin
from app.utils.supabase_kv_cache import cache_get_json, cache_set_json


# --------------------------------------------------
# Check if Redfin table is empty
# --------------------------------------------------
def is_redfin_empty():
    supabase = require_supabase()
    last_error: Exception | None = None
    for table_name in redfin_trends_table_candidates():
        try:
            response = (
                supabase.table(table_name)
                .select("period", count="exact")
                .limit(1)
                .execute()
            )
            return response.count == 0
        except Exception as e:
            last_error = e
            continue

    raise RuntimeError(f"Unable to query any Redfin trends table: {last_error}")


# --------------------------------------------------
# Get Median House Price
# --------------------------------------------------
def get_median_house_price(*, city: str | None = None, state: str | None = None, address: str | None = None):

    input_address = (address or "").strip()
    input_city = (city or "").strip()
    input_state = (state or "").strip()

    if not input_address and (not input_city or not input_state):
        return {"error": "Provide either address OR (city and state)"}

    # STEP 1 — Ensure Redfin data exists
    if is_redfin_empty():
        print("⚠ Redfin table is empty. Running ingest...")
        ingest_redfin()

    # STEP 2 — Resolve city/state
    resolved_city = input_city
    resolved_state = input_state

    if input_address:
        geo = geocode_address(input_address)
        if not geo:
            return {"error": "Address not found"}

        _lat, _lon, geo_city, geo_state = geo
        resolved_city = (geo_city or "").strip()
        resolved_state = (geo_state or "").strip()

    if not resolved_city or not resolved_state:
        return {"error": "Could not resolve city/state"}

    normalized_city = " ".join(resolved_city.split()).strip().lower()
    normalized_state = " ".join(resolved_state.split()).strip().lower()
    cache_key = f"median_house_price:{normalized_city}:{normalized_state}"

    cached = cache_get_json(table="median_house_price_cache", key=cache_key)
    if isinstance(cached, dict) and cached.get("median_price") is not None:
        cached = {**cached, "source": "Supabase Cache"}
        # Preserve caller-provided address when present.
        if input_address:
            cached["address"] = input_address
        return cached

    def city_variants(name: str) -> list[str]:
        base = (name or "").strip()
        if not base:
            return []

        variants = {base}
        variants.add(base.replace("Saint ", "St. "))
        variants.add(base.replace("St. ", "Saint "))
        variants.add(base.replace("St ", "Saint "))
        variants.add(base.replace("Saint ", "St "))

        # Nominatim sometimes returns prefixed forms like "City of ..."
        if base.lower().startswith("city of "):
            variants.add(base[8:])

        return [v for v in variants if v.strip()]

    # STEP 3 — Fetch latest median price from Supabase
    supabase = require_supabase()

    response = None
    for table_name in redfin_trends_table_candidates():
        for city_try in city_variants(resolved_city):
            try:
                response = (
                    supabase.table(table_name)
                    .select("*")
                    .ilike("city", f"%{city_try}%")
                    .ilike("state", f"%{resolved_state}%")
                    .order("period", desc=True)
                    .limit(1)
                    .execute()
                )
            except Exception:
                response = None
                continue

            if response and response.data:
                break

        if response and response.data:
            break

    if not response or not response.data:
        return {"error": f"No median price data found for {resolved_city}, {resolved_state}"}

    record = response.data[0]

    sale_to_list_ratio = None
    if isinstance(record, dict):
        sale_to_list_ratio = record.get("sale_to_list_ratio")

    result = {
        "date": date.today().isoformat(),
        "address": input_address or None,
        "city": record["city"],
        "state": record["state"],
        "median_price": record["median_price"],
        "sale_to_list_ratio": sale_to_list_ratio,
        "period": record["period"],
        "source": "Supabase (Redfin Official Data)"
    }

    cache_set_json(
        table="median_house_price_cache",
        key=cache_key,
        value=result,
        ttl_seconds=settings.MEDIAN_HOUSE_PRICE_CACHE_TTL_SECONDS,
    )

    return result


# --------------------------------------------------
# CLI RUN
# --------------------------------------------------
if __name__ == "__main__":
    addr = " ".join(sys.argv[1:]).strip() if len(sys.argv) > 1 else ""
    if not addr:
        addr = input("Enter property address: ").strip()

    import contextlib
    import io

    input_place = (addr or "").strip()

    # Suppress any internal logging/printing; CLI output must be only the two lines below.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = get_median_house_price(address=addr)

    if isinstance(result, dict) and result.get("error"):
        print(f"place:- {input_place}" if input_place else "place:-")
        print("median house price:-")
        raise SystemExit(1)

    place = input_place
    median_price = result.get("median_price")
    print(f"place:- {place}")
    print(f"median house price:- {median_price}")
