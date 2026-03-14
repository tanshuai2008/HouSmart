
from datetime import date
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


# --------------------------------------------------
# Get Median House Price
# --------------------------------------------------
def get_median_house_price(address: str):

    if not address.strip():
        return {"error": "Address is required"}

    # STEP 1 — Ensure Redfin data exists
    if is_redfin_empty():
        print("⚠ Redfin table is empty. Running ingest...")
        ingest_redfin()

    # STEP 2 — Geocode address
    geo = geocode_address(address)
    if not geo:
        return {"error": "Address not found"}

    lat, lon, city, state = geo

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
    response = None
    for city_try in city_variants(city):
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
        return {
            "error": f"No median price data found for {city}, {state}"
        }

    record = response.data[0]

    return {
        "date": date.today().isoformat(),
        "address": address,
        "city": record["city"],
        "state": record["state"],
        "median_price": record["median_price"],
        "period": record["period"],
        "source": "Supabase (Redfin Official Data)"
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

    # Suppress any internal logging/printing; CLI output must be only the two lines below.
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
