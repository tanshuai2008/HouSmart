import requests
from app.utils.cache_utils import get_cached, set_cache

CENSUS_GEO_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
CENSUS_TRACT_URL = "https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
ACS_URL = "https://api.census.gov/data/2022/acs/acs5"

TIMEOUT = 10


def fetch_median_house_price(address):
    try:
        # ---------- STEP 1: Geocode ----------
        geo_params = {
            "address": address,
            "benchmark": "Public_AR_Current",
            "format": "json",
        }

        geo_res = requests.get(CENSUS_GEO_URL, params=geo_params, timeout=TIMEOUT)
        geo_res.raise_for_status()
        geo_data = geo_res.json()

        matches = geo_data.get("result", {}).get("addressMatches", [])
        if not matches:
            return {"error": "Address not found"}

        coords = matches[0]["coordinates"]
        lat = coords["y"]
        lng = coords["x"]

        # ---------- STEP 2: Get Census Tract ----------
        tract_params = {
            "x": lng,
            "y": lat,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "format": "json",
        }

        tract_res = requests.get(CENSUS_TRACT_URL, params=tract_params, timeout=TIMEOUT)
        tract_res.raise_for_status()
        tract_data = tract_res.json()

        tracts = tract_data.get("result", {}).get("geographies", {}).get("Census Tracts", [])
        if not tracts:
            return {"error": "Census tract not found"}

        tract_info = tracts[0]
        state = tract_info["STATE"]
        county = tract_info["COUNTY"]
        tract = tract_info["TRACT"]

        cache_key = f"{state}:{county}:{tract}"

        # ==================================================
        # 🔥 STEP 3 — CHECK CACHE BEFORE API CALL
        # ==================================================
        cached = get_cached(cache_key)

        if cached:
            print("⚡ Cache hit — returning cached data")
            return cached

        # ---------- STEP 4: Fetch Median House Price ----------
        acs_params = {
            "get": "B25077_001E",
            "for": f"tract:{tract}",
            "in": f"state:{state}+county:{county}",
        }

        acs_res = requests.get(ACS_URL, params=acs_params, timeout=TIMEOUT)
        acs_res.raise_for_status()
        acs_data = acs_res.json()

        if len(acs_data) < 2:
            return {"error": "Median price data unavailable"}

        median_price_raw = int(acs_data[1][0])

        # Handle Census special values
        if median_price_raw < 0:
            median_price = None
            note = "Median price unavailable for this tract"
        else:
            median_price = median_price_raw
            note = None

        result = {
            "latitude": lat,
            "longitude": lng,
            "state": state,
            "county": county,
            "tract": tract,
            "median_house_price": median_price,
            "note": note,
            "source": "US Census ACS 2022 (B25077)",
        }

        # ==================================================
        # 🔥 STEP 4 — SAVE RESULT TO CACHE
        # ==================================================
        set_cache(cache_key, result)

        print("💾 Saved to cache")

        return result

    except requests.exceptions.RequestException as e:
        return {"error": f"Network/API error: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}


# ==================================================
# 🧪 USER INPUT TEST MODE
# ==================================================
if __name__ == "__main__":
    address = input("🏠 Enter property address: ").strip()

    if not address:
        print("❌ No address provided.")
    else:
        result = fetch_median_house_price(address)

        print("\n📊 Result:")
        print(result)