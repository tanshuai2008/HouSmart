import math
import time

import requests

from app.config.db import require_supabase
from app.core.config import settings
from app.services.geocode import geocode_address
from app.utils.supabase_kv_cache import cache_get_json, cache_set_json


# --------------------------------------------------
# Haversine Distance (meters)
# --------------------------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# --------------------------------------------------
# Find nearest road using OpenStreetMap Overpass
# --------------------------------------------------
def nearest_road_distance(lat, lon):

    query = f"""
    [out:json];
    way(around:200,{lat},{lon})["highway"];
    out geom;
    """

    url = "https://overpass-api.de/api/interpreter"

    headers = {
        "User-Agent": "HouSmart/1.0"
    }

    # Retry mechanism
    for attempt in range(3):
        try:

            res = requests.post(
                url,
                data=query,
                headers=headers,
                timeout=30
            )

            if res.status_code != 200:
                time.sleep(2)
                continue

            data = res.json()
            break

        except Exception:
            time.sleep(2)

    else:
        return None

    min_dist = float("inf")

    for element in data.get("elements", []):
        for point in element.get("geometry", []):
            d = haversine(lat, lon, point["lat"], point["lon"])

            if d < min_dist:
                min_dist = d

    if min_dist == float("inf"):
        return None

    return round(min_dist, 2)


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
# Estimate Noise Level (by address)
# --------------------------------------------------
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
    normalized_address = " ".join(address.split()).strip().lower()
    cache_key = f"noise:address:{normalized_address}"

    cached = None
    try:
        cached = cache_get_json(table="noise_cache", key=cache_key)
    except Exception:
        cached = None
    if isinstance(cached, dict) and cached.get("noise_level") is not None:
        return {
            **cached,
            "address": address,
            "city": city,
            "state": state,
            "source": "Supabase Cache",
        }

    # Back-compat fallback: old cache table `noise_scores` (no TTL)
    try:
        supabase = require_supabase()
        existing = (
            supabase.table("noise_scores")
            .select("distance_to_road, noise_level")
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
                "noise_level": record.get("noise_level"),
                "distance_to_road_m": record.get("distance_to_road"),
                "source": "Supabase Cache",
            }
    except Exception:
        pass

    # --------------------------------------------------
    # Compute noise
    # --------------------------------------------------
    distance = nearest_road_distance(lat, lon)

    noise = classify_noise(distance)

    computed_result = {
        "address": address,
        "city": city,
        "state": state,
        "noise_level": noise,
        "distance_to_road_m": distance,
        "source": "OpenStreetMap",
        "lat": lat,
        "lon": lon,
    }

    # --------------------------------------------------
    # Store in Supabase
    # --------------------------------------------------
    try:
        cache_set_json(
            table="noise_cache",
            key=cache_key,
            value=computed_result,
            ttl_seconds=settings.NOISE_CACHE_TTL_SECONDS,
        )
    except Exception:
        pass

    # Best-effort write to legacy `noise_scores` table (if present)
    try:
        supabase = require_supabase()
        supabase.table("noise_scores").insert({
            "address": address,
            "latitude": lat,
            "longitude": lon,
            "distance_to_road": distance,
            "noise_level": noise
        }).execute()
    except Exception:
        pass

    return {
        "address": address,
        "city": city,
        "state": state,
        "noise_level": noise,
        "distance_to_road_m": distance,
        "source": "OpenStreetMap"
    }


# --------------------------------------------------
# Estimate Noise Level (by coordinates)
# --------------------------------------------------
def estimate_noise(lat: float, lon: float):
    cache_key = f"noise:coords:{lat:.5f}:{lon:.5f}"
    cached = None
    try:
        cached = cache_get_json(table="noise_cache", key=cache_key)
    except Exception:
        cached = None
    if isinstance(cached, dict) and cached.get("noise_level") is not None:
        return {
            **cached,
            "lat": lat,
            "lon": lon,
            "source": "Supabase Cache",
        }

    distance = nearest_road_distance(lat, lon)
    noise = classify_noise(distance)

    result = {
        "lat": lat,
        "lon": lon,
        "noise_level": noise,
        "distance_to_road_m": distance,
        "source": "OpenStreetMap",
    }

    try:
        cache_set_json(
            table="noise_cache",
            key=cache_key,
            value=result,
            ttl_seconds=settings.NOISE_CACHE_TTL_SECONDS,
        )
    except Exception:
        pass

    return result


# --------------------------------------------------
# CLI TEST
# --------------------------------------------------
if __name__ == "__main__":

    addr = input("Enter property address: ").strip()

    result = estimate_noise_from_address(addr)

    print(result)
