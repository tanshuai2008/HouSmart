import math
import time

import requests

from app.config.db import require_supabase
from app.services.geocode import geocode_address


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
    supabase = require_supabase()

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
            "source": "Supabase Cache"
        }

    # --------------------------------------------------
    # Compute noise
    # --------------------------------------------------
    distance = nearest_road_distance(lat, lon)

    noise = classify_noise(distance)

    # --------------------------------------------------
    # Store in Supabase
    # --------------------------------------------------
    supabase.table("noise_scores").insert({
        "address": address,
        "latitude": lat,
        "longitude": lon,
        "distance_to_road": distance,
        "noise_level": noise
    }).execute()

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

    distance = nearest_road_distance(lat, lon)
    noise = classify_noise(distance)

    return {
        "lat": lat,
        "lon": lon,
        "noise_level": noise,
        "distance_to_road_m": distance,
        "source": "OpenStreetMap"
    }


# --------------------------------------------------
# CLI TEST
# --------------------------------------------------
if __name__ == "__main__":

    addr = input("Enter property address: ").strip()

    result = estimate_noise_from_address(addr)

    print(result)
