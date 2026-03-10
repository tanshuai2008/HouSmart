import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode_address(address: str):
    if not address:
        return None

    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
        # Redfin dataset is US-only; restricting improves accuracy and avoids
        # returning international results that won't be found in the dataset.
        "countrycodes": "us",
    }

    headers = {"User-Agent": "HouSmart"}

    try:
        res = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=20)
        res.raise_for_status()
        data = res.json()

        if not data:
            return None

        result = data[0]
        lat = float(result["lat"])
        lon = float(result["lon"])

        addr = result.get("address", {})
        city = (
            addr.get("city")
            or addr.get("town")
            or addr.get("village")
            or addr.get("hamlet")
            or addr.get("borough")
            or addr.get("municipality")
            or ""
        )
        state = addr.get("state") or addr.get("state_code") or ""

        return lat, lon, city, state
    except Exception:
        return None
