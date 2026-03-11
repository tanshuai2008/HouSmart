import requests

from app.config.db import supabase
from app.core.config import settings
from app.services.geocode import geocode_address
from app.utils.geo import haversine_meters


def _build_cached_noise_response(*, distance, source: str, api_used: str, address: str | None = None, city: str | None = None, state: str | None = None, latitude: float | None = None, longitude: float | None = None):
    return {
        "address": address,
        "city": city,
        "state": state,
        "noise_level": classify_noise(distance) if distance is not None else "Unknown",
        "noise_index": estimate_noise_index(distance),
        "estimated_noise_db": estimate_noise_db(distance),
        "distance_to_road_m": distance,
        "source": source,
        "api_used": api_used,
        "latitude": latitude,
        "longitude": longitude,
    }

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


def estimate_noise_index(distance) -> float | None:
    """
    Convert road proximity into a 0-100 noise index.
    Higher means noisier. This is a modeled proxy, not measured dB.
    """
    if distance is None:
        return None

    # Exponential decay keeps values high near roads and tapers smoothly.
    # 0m -> ~100, 50m -> ~60, 100m -> ~37, 200m -> ~13
    import math

    idx = 100.0 * math.exp(-distance / 100.0)
    return round(max(0.0, min(100.0, idx)), 1)


def estimate_noise_db(distance) -> float | None:
    """
    Convert proximity index to an estimated ambient dB range midpoint.
    Approximate mapping: index 0-100 -> 35-80 dB.
    """
    idx = estimate_noise_index(distance)
    if idx is None:
        return None
    db = 35.0 + (idx / 100.0) * 45.0
    return round(db, 1)


# --------------------------------------------------
# Estimate Noise Level
# --------------------------------------------------
def estimate_noise(lat: float, lon: float):
    distance, api_used, source = nearest_road_distance(lat, lon)
    noise = classify_noise(distance)
    noise_index = estimate_noise_index(distance)
    noise_db = estimate_noise_db(distance)
    return {
        "latitude": lat,
        "longitude": lon,
        "noise_level": noise,
        "noise_index": noise_index,
        "estimated_noise_db": noise_db,
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
        distance = record["distance_to_road"]
        response = _build_cached_noise_response(
            distance=distance,
            source="Supabase Cache",
            api_used="cache",
            address=address,
            city=city,
            state=state,
            latitude=lat,
            longitude=lon,
        )
        if record.get("noise_level"):
            response["noise_level"] = record.get("noise_level")
        return response

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
        "noise_index": result["noise_index"],
        "estimated_noise_db": result["estimated_noise_db"],
        "distance_to_road_m": distance,
        "source": result["source"],
        "api_used": result["api_used"],
    }


def estimate_noise_from_coordinates(lat: float, lon: float):
    if lat is None or lon is None:
        return {"error": "Coordinates are required"}

    # Reuse nearby cached row to avoid repeated Roads API calls for same/similar point.
    tol = 0.0001
    existing = (
        supabase.table("noise_scores")
        .select("*")
        .gte("latitude", lat - tol)
        .lte("latitude", lat + tol)
        .gte("longitude", lon - tol)
        .lte("longitude", lon + tol)
        .limit(1)
        .execute()
    )

    if existing.data:
        record = existing.data[0]
        distance = record.get("distance_to_road")
        response = _build_cached_noise_response(
            distance=distance,
            source="Supabase Cache",
            api_used="cache",
            address=record.get("address"),
            latitude=record.get("latitude"),
            longitude=record.get("longitude"),
        )
        if record.get("noise_level"):
            response["noise_level"] = record.get("noise_level")
        return response

    result = estimate_noise(lat=lat, lon=lon)
    distance = result.get("distance_to_road_m")
    noise = result.get("noise_level")

    supabase.table("noise_scores").insert(
        {
            "address": None,
            "latitude": lat,
            "longitude": lon,
            "distance_to_road": distance,
            "noise_level": noise,
        }
    ).execute()

    return {
        "address": None,
        "city": None,
        "state": None,
        "noise_level": noise,
        "noise_index": result.get("noise_index"),
        "estimated_noise_db": result.get("estimated_noise_db"),
        "distance_to_road_m": distance,
        "source": result.get("source"),
        "api_used": result.get("api_used"),
        "latitude": lat,
        "longitude": lon,
    }


# --------------------------------------------------
# CLI TEST
# --------------------------------------------------
if __name__ == "__main__":

    addr = input("Enter property address: ").strip()

    result = estimate_noise_from_address(addr)

    print(result)
