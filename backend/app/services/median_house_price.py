
from __future__ import annotations

from datetime import date
import sys

from app.config.db import require_supabase
from app.core.config import settings
from app.core.redfin_trends import redfin_trends_table_candidates
from app.services.census_service import CensusService
from app.services.geocode import geocode_address
from app.scripts.ingest_redfin import ingest_redfin
from app.utils.supabase_kv_cache import cache_get_json, cache_set_json


REDFIN_LATEST_TABLE = "redfin_city_latest"


# --------------------------------------------------
# Check if Redfin table is empty
# --------------------------------------------------
def is_redfin_empty():
    supabase = require_supabase()

    # Prefer the latest snapshot table if present.
    try:
        response = (
            supabase.table(REDFIN_LATEST_TABLE)
            .select("period", count="exact")
            .limit(1)
            .execute()
        )
        return response.count == 0
    except Exception:
        # Table might not exist yet; fall back to trends tables.
        pass

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


def _resolve_city_state(*, address: str | None, city: str | None, state: str | None) -> tuple[str, str] | None:
    """Resolve (city, state) for a place.

    Prefer the US Census geocoder for US addresses; fall back to OSM Nominatim.
    """

    city_in = (city or "").strip()
    state_in = (state or "").strip()
    address_in = (address or "").strip()

    if address_in:
        # 1) Census geocoder (best for US)
        try:
            loc = CensusService.get_location_data(address_in)
            if isinstance(loc, dict):
                c = (loc.get("city") or "").strip()
                s = (loc.get("state") or "").strip()
                if c and s:
                    return c, s
        except Exception:
            pass

        # 2) Nominatim fallback
        geo = geocode_address(address_in)
        if geo:
            _lat, _lon, geo_city, geo_state = geo
            c = (geo_city or "").strip()
            s = (geo_state or "").strip()
            if c and s:
                return c, s

    if city_in and state_in:
        return city_in, state_in

    return None


def _city_variants(name: str) -> list[str]:
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


def _state_variants(state: str) -> list[str]:
    """Return likely state representations found in Supabase."""

    s = (state or "").strip()
    if not s:
        return []

    # If caller already provided an abbreviation, try both abbreviation + full name.
    if len(s) == 2 and s.isalpha():
        abbr = s.upper()
        full = {
            "AL": "Alabama",
            "AK": "Alaska",
            "AZ": "Arizona",
            "AR": "Arkansas",
            "CA": "California",
            "CO": "Colorado",
            "CT": "Connecticut",
            "DE": "Delaware",
            "DC": "District Of Columbia",
            "FL": "Florida",
            "GA": "Georgia",
            "HI": "Hawaii",
            "ID": "Idaho",
            "IL": "Illinois",
            "IN": "Indiana",
            "IA": "Iowa",
            "KS": "Kansas",
            "KY": "Kentucky",
            "LA": "Louisiana",
            "ME": "Maine",
            "MD": "Maryland",
            "MA": "Massachusetts",
            "MI": "Michigan",
            "MN": "Minnesota",
            "MS": "Mississippi",
            "MO": "Missouri",
            "MT": "Montana",
            "NE": "Nebraska",
            "NV": "Nevada",
            "NH": "New Hampshire",
            "NJ": "New Jersey",
            "NM": "New Mexico",
            "NY": "New York",
            "NC": "North Carolina",
            "ND": "North Dakota",
            "OH": "Ohio",
            "OK": "Oklahoma",
            "OR": "Oregon",
            "PA": "Pennsylvania",
            "RI": "Rhode Island",
            "SC": "South Carolina",
            "SD": "South Dakota",
            "TN": "Tennessee",
            "TX": "Texas",
            "UT": "Utah",
            "VT": "Vermont",
            "VA": "Virginia",
            "WA": "Washington",
            "WV": "West Virginia",
            "WI": "Wisconsin",
            "WY": "Wyoming",
        }.get(abbr)
        return [abbr, full] if full else [abbr]

    full_norm = " ".join(s.split()).strip()
    return [full_norm, full_norm.title()]


def _safe_select_latest_snapshot(*, supabase, city: str, state: str) -> dict | None:
    """Best-effort select from `redfin_city_latest`.

    Returns the row dict if found, else None.
    """

    city_clean = (city or "").strip()
    if not city_clean:
        return None

    for state_try in _state_variants(state):
        for city_try in _city_variants(city_clean):
            # 1) Exact match
            try:
                resp = (
                    supabase.table(REDFIN_LATEST_TABLE)
                    .select("*")
                    .eq("city", city_try)
                    .eq("state", state_try)
                    .limit(1)
                    .execute()
                )
                rows = resp.data or []
                if rows:
                    return rows[0]
            except Exception:
                pass

            # 2) Case-insensitive exact city match
            try:
                resp = (
                    supabase.table(REDFIN_LATEST_TABLE)
                    .select("*")
                    .ilike("city", city_try)
                    .eq("state", state_try)
                    .limit(1)
                    .execute()
                )
                rows = resp.data or []
                if rows:
                    return rows[0]
            except Exception:
                pass

            # 3) Fuzzy city match (last resort)
            try:
                resp = (
                    supabase.table(REDFIN_LATEST_TABLE)
                    .select("*")
                    .ilike("city", f"%{city_try}%")
                    .eq("state", state_try)
                    .limit(1)
                    .execute()
                )
                rows = resp.data or []
                if rows:
                    return rows[0]
            except Exception:
                pass

    return None


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
    resolved = _resolve_city_state(address=input_address, city=input_city, state=input_state)
    if not resolved:
        return {"error": "Could not resolve city/state"}
    resolved_city, resolved_state = resolved

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

    # STEP 3 — Fetch latest median price from Supabase
    supabase = require_supabase()

    # 3a) Prefer the latest snapshot table (fast, one row per city/state).
    record = None
    try:
        record = _safe_select_latest_snapshot(supabase=supabase, city=resolved_city, state=resolved_state)
    except Exception:
        record = None

    source = "Supabase (Redfin Latest Snapshot)"

    # 3b) Fallback: monthly trends tables (legacy behavior)
    response = None
    if record is None:
        source = "Supabase (Redfin Official Data)"
        for table_name in redfin_trends_table_candidates():
            for city_try in _city_variants(resolved_city):
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

        if response and response.data:
            record = response.data[0]

    if not isinstance(record, dict):
        return {"error": f"No median price data found for {resolved_city}, {resolved_state}"}

    sale_to_list_ratio = None
    sale_to_list_ratio = record.get("sale_to_list_ratio")

    period = record.get("period")
    # Supabase may return a date-like string or a date object depending on client.
    period_str = str(period) if period is not None else None

    result = {
        "date": date.today().isoformat(),
        "address": input_address or None,
        "city": record["city"],
        "state": record["state"],
        "median_price": record["median_price"],
        "sale_to_list_ratio": sale_to_list_ratio,
        "period": period_str,
        "source": source,
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
