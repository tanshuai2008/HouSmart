import requests
from geopy.distance import geodesic

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


# ---------------------------
# STEP 1 — Address → Coordinates
# ---------------------------
def geocode_address(address):

    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }

    headers = {"User-Agent": "HouSmartProject"}

    try:
        res = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=headers,
            timeout=20
        )
        res.raise_for_status()
        data = res.json()

    except Exception:
        return None

    if not data:
        return None

    return float(data[0]["lat"]), float(data[0]["lon"])


# ---------------------------
# STEP 2 — Find nearest road (SAFE)
# ---------------------------
def nearest_road_distance(lat, lon):

    query = f"""
    [out:json];
    way(around:200,{lat},{lon})["highway"];
    out geom;
    """

    try:
        res = requests.post(
            OVERPASS_URL,
            data=query,
            timeout=30
        )

        res.raise_for_status()

        # Sometimes Overpass returns empty or HTML
        if not res.text.strip():
            return None

        data = res.json()

    except Exception:
        return None

    min_dist = None

    for element in data.get("elements", []):
        for p in element.get("geometry", []):
            d = geodesic((lat, lon), (p["lat"], p["lon"])).meters

            if min_dist is None or d < min_dist:
                min_dist = d

    return min_dist


# ---------------------------
# STEP 3 — Distance → Noise
# ---------------------------
def distance_to_noise(distance):

    if distance is None:
        return "Unknown"

    if distance < 20:
        return "Very High"
    elif distance < 50:
        return "High"
    elif distance < 150:
        return "Moderate"
    else:
        return "Low"


# ---------------------------
# MAIN FUNCTION
# ---------------------------
def estimate_noise_from_address(address):

    coords = geocode_address(address)

    if not coords:
        return {"error": "Address not found"}

    lat, lon = coords

    distance = nearest_road_distance(lat, lon)

    if distance is None:
        return {"error": "Unable to determine nearby road distance"}

    noise = distance_to_noise(distance)

    return {
        "noise_level": noise,
        "distance_to_nearest_road_m": round(distance, 2),
        "method": "Estimated from nearest road distance",
        "source": "OpenStreetMap"
    }


# ---------------------------
# RUN
# ---------------------------
if __name__ == "__main__":
    address = input("Enter property address: ")
    result = estimate_noise_from_address(address)
    print(result)