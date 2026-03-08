import requests

from app.config.db import supabase
from app.core.config import settings
from app.services.geocode import geocode_address
from app.utils.geo import haversine_meters

def _nearest_road_distance_google(lat, lon):
    if not settings.GOOGLE_MAPS_API_KEY:
        return None

    url = "https://roads.googleapis.com/v1/nearestRoads"
    params = {
        "points": f"{lat},{lon}",
        "key": settings.GOOGLE_MAPS_API_KEY,
    }

    try:
        res = requests.get(
            url,
            params=params,
            timeout=settings.GOOGLE_ROADS_HTTP_TIMEOUT_SECONDS,
        )
        res.raise_for_status()
        data = res.json()
    except Exception:
        return None

    snapped = data.get("snappedPoints") or []
    if not snapped:
        return None

    min_dist = float("inf")
    for point in snapped:
        location = point.get("location", {})
        road_lat = location.get("latitude")
        road_lng = location.get("longitude")
        if road_lat is None or road_lng is None:
            continue
        d = haversine_meters(lat, lon, road_lat, road_lng)
        if d < min_dist:
            min_dist = d

    if min_dist == float("inf"):
        return None
    return round(min_dist, 2)


def nearest_road_distance(lat, lon):
    distance = _nearest_road_distance_google(lat, lon)
    if distance is not None:
        return distance, "google_roads", "Google Maps Roads API"
    return None, "unknown", "Unknown"


# --------------------------------------------------
# Noise Classification
# --------------------------------------------------
def classify_noise(distance):

    if distance is None:
        return "Unknown"

    if distance < 20:
        return "Very High"
    elif distance < 50:
        return "High"
    elif distance < 100:
        return "Moderate"
    else:
        return "Low"


# --------------------------------------------------
# Estimate Noise Level
# --------------------------------------------------
def estimate_noise(lat: float, lon: float):
    distance, api_used, source = nearest_road_distance(lat, lon)
    noise = classify_noise(distance)
    return {
        "latitude": lat,
        "longitude": lon,
        "noise_level": noise,
        "distance_to_road_m": distance,
        "source": source,
        "api_used": api_used,
    }


def estimate_noise_from_address(address: str):

    if not address.strip():
        return {"error": "Address required"}

    geo = geocode_address(address)

    if not geo:
        return {"error": "Address not found"}

    lat, lon, city, state = geo

    # --------------------------------------------------
    # Check Supabase Cache
    # --------------------------------------------------
    existing = (
        supabase.table("noise_scores")
        .select("*")
        .eq("address", address)
        .limit(1)
        .execute()
    )

    if existing.data:
        record = existing.data[0]
        return {
            "address": address,
            "city": city,
            "state": state,
            "noise_level": record["noise_level"],
            "distance_to_road_m": record["distance_to_road"],
            "source": "Supabase Cache",
            "api_used": "cache",
        }

    # --------------------------------------------------
    # Compute noise from coordinates
    # --------------------------------------------------
    result = estimate_noise(lat=lat, lon=lon)
    distance = result["distance_to_road_m"]
    noise = result["noise_level"]

    # --------------------------------------------------
    # Store in Supabase
    # --------------------------------------------------
    supabase.table("noise_scores").insert(
        {
            "address": address,
            "latitude": lat,
            "longitude": lon,
            "distance_to_road": distance,
            "noise_level": noise,
        }
    ).execute()

    return {
        "address": address,
        "city": city,
        "state": state,
        "noise_level": noise,
        "distance_to_road_m": distance,
        "source": result["source"],
        "api_used": result["api_used"],
    }


# --------------------------------------------------
# CLI TEST
# --------------------------------------------------
if __name__ == "__main__":

    addr = input("Enter property address: ").strip()

    result = estimate_noise_from_address(addr)

    print(result)
