from datetime import date
import re
import sys

from app.config.db import supabase
from app.services.geocode import geocode_address
from app.scripts.ingest_redfin import ingest_redfin


# --------------------------------------------------
# Check if Redfin table is empty
# --------------------------------------------------
def is_redfin_empty():
    response = (
        supabase.table("redfin_median_prices")
        .select("id", count="exact")
        .limit(1)
        .execute()
    )

    return response.count == 0


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


def _fetch_latest_median_price(city: str, state: str):
    # Ensure Redfin data exists before querying.
    if is_redfin_empty():
        print("Redfin table is empty. Running ingest...")
        ingest_redfin()

    response = None
    for city_try in _city_variants(city):
        response = (
            supabase.table("redfin_median_prices")
            .select("*")
            .ilike("city", f"%{city_try}%")
            .ilike("state", f"%{state}%")
            .order("period", desc=True)
            .limit(1)
            .execute()
        )
        if response.data:
            break

    if not response or not response.data:
        return None

    return response.data[0]


def _parse_city_state_from_us_address(address: str) -> tuple[str, str] | None:
    """
    Best-effort parser for addresses like:
    - "86 Highpoint Dr, Berwyn, PA 19312"
    - "Berwyn, PA"
    """
    text = (address or "").strip()
    if not text:
        return None

    # Prefer the final "..., City, ST [ZIP]" pattern.
    match = re.search(r",\s*([^,]+?),\s*([A-Za-z]{2})(?:\s+\d{5}(?:-\d{4})?)?\s*$", text)
    if match:
        city = match.group(1).strip()
        state = match.group(2).strip().upper()
        if city and state:
            return city, state

    # Secondary pattern: "City, ST"
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if len(parts) >= 2:
        city = parts[-2]
        state_token = parts[-1].split()[0].strip().upper() if parts[-1] else ""
        if city and len(state_token) == 2 and state_token.isalpha():
            return city, state_token

    return None


def get_median_house_price_by_city_state(city: str, state: str):
    city = (city or "").strip()
    state = (state or "").strip()

    if not city or not state:
        return {"error": "Both city and state are required"}

    record = _fetch_latest_median_price(city=city, state=state)
    if not record:
        return {"error": f"No median price data found for {city}, {state}"}

    return {
        "date": date.today().isoformat(),
        "city": record["city"],
        "state": record["state"],
        "median_price": record["median_price"],
        "period": record["period"],
        "source": "Supabase (Redfin Official Data)",
    }


# --------------------------------------------------
# Get Median House Price by full address
# --------------------------------------------------
def get_median_house_price(address: str):

    if not (address or "").strip():
        return {"error": "Address is required"}

    # STEP 1 - Geocode address.
    geo = geocode_address(address)
    if geo:
        _lat, _lon, city, state = geo
    else:
        # Fallback: parse city/state directly from US-style address strings.
        parsed = _parse_city_state_from_us_address(address)
        if not parsed:
            return {"error": "Address not found"}
        city, state = parsed

    # STEP 2 - Fetch latest median price by resolved city/state.
    record = _fetch_latest_median_price(city=city, state=state)
    if not record:
        return {"error": f"No median price data found for {city}, {state}"}

    return {
        "date": date.today().isoformat(),
        "address": address,
        "city": record["city"],
        "state": record["state"],
        "median_price": record["median_price"],
        "period": record["period"],
        "source": "Supabase (Redfin Official Data)",
    }


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

    # Suppress internal logging/printing; CLI output must be only the two lines below.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        result = get_median_house_price(addr)

    if isinstance(result, dict) and result.get("error"):
        print(f"place:- {input_place}" if input_place else "place:-")
        print("median house price:-")
        raise SystemExit(1)

    place = input_place
    median_price = result.get("median_price")
    print(f"place:- {place}")
    print(f"median house price:- {median_price}")
