import httpx
import math
import redis
import json
from typing import Optional
from app.core.config import settings

# Redis client for caching (30-day TTL — transit changes slowly)
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
CACHE_TTL = 60 * 60 * 24 * 30  # 30 days

# OSM Overpass API endpoint
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Transit stop types we care about (OSM tags)
TRANSIT_TAGS = [
    "bus_stop",
    "station",
    "tram_stop",
    "subway_entrance",
    "halt",
    "ferry_terminal",
]

# Scoring rubric: (min_bus_stops, min_rail_stations) → base score
# Rail bonus: +15 if any rail/subway station found (capped at 100)
SCORE_RUBRIC = [
    (20, 2, 95),
    (15, 1, 85),
    (10, 1, 75),
    (8,  0, 65),
    (5,  0, 50),
    (3,  0, 35),
    (1,  0, 20),
    (0,  0, 5),
]

RAIL_TYPES = {"station", "subway_entrance", "halt", "ferry_terminal"}


def _build_overpass_query(lat: float, lng: float, radius_meters: int) -> str:
    """Build Overpass QL query to fetch all transit stops within radius."""
    tags = "".join(
        f'node["highway"="bus_stop"](around:{radius_meters},{lat},{lng});'
        f'node["public_transport"="stop_position"](around:{radius_meters},{lat},{lng});'
        f'node["railway"="station"](around:{radius_meters},{lat},{lng});'
        f'node["railway"="subway_entrance"](around:{radius_meters},{lat},{lng});'
        f'node["railway"="tram_stop"](around:{radius_meters},{lat},{lng});'
        f'node["railway"="halt"](around:{radius_meters},{lat},{lng});'
    )
    return f"[out:json][timeout:25];({tags});out body;"


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in meters between two lat/lng points."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _compute_transit_score(bus_count: int, rail_count: int) -> float:
    """Map stop counts to a 0–100 transit score using the rubric table."""
    base_score = 5  # default: no transit
    for min_bus, min_rail, score in SCORE_RUBRIC:
        if bus_count >= min_bus and rail_count >= min_rail:
            base_score = score
            break
    # Rail bonus
    if rail_count > 0:
        base_score = min(100, base_score + 15)
    return float(base_score)


async def fetch_transit_stops(lat: float, lng: float, radius_meters: int = 800) -> dict:
    """
    Task 1 & 3: Fetch transit stops from OSM Overpass within radius,
    compute transit score, return structured result.
    """
    cache_key = f"transit:{lat:.4f}:{lng:.4f}:{radius_meters}"

    # Check Redis cache first
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    query = _build_overpass_query(lat, lng, radius_meters)

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(OVERPASS_URL, data={"data": query})
        response.raise_for_status()
        data = response.json()

    elements = data.get("elements", [])

    stops = []
    bus_count = 0
    rail_count = 0
    nearest_meters: Optional[float] = None

    for el in elements:
        el_lat = el.get("lat")
        el_lng = el.get("lon")
        tags = el.get("tags", {})

        # Determine stop type
        stop_type = "bus_stop"
        if tags.get("railway") in ("station", "subway_entrance", "halt"):
            stop_type = tags["railway"]
            rail_count += 1
        else:
            bus_count += 1

        # Distance from property to this stop
        dist = _haversine_meters(lat, lng, el_lat, el_lng)
        if nearest_meters is None or dist < nearest_meters:
            nearest_meters = dist

        stops.append({
            "osm_id": str(el.get("id")),
            "name": tags.get("name"),
            "stop_type": stop_type,
            "lat": el_lat,
            "lng": el_lng,
        })

    transit_score = _compute_transit_score(bus_count, rail_count)

    result = {
        "property_lat": lat,
        "property_lng": lng,
        "radius_meters": radius_meters,
        "bus_stop_count": bus_count,
        "rail_station_count": rail_count,
        "transit_score": transit_score,
        "nearest_stop_meters": round(nearest_meters, 1) if nearest_meters else None,
        "stops": stops,
        "source": "OpenStreetMap (Overpass API)",
    }

    # Cache the result for 30 days
    redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))

    return result


async def save_transit_stops_to_db(lat: float, lng: float, radius_meters: int = 800) -> dict:
    """
    Task 1: Import transit stop locations into Supabase DB.
    Fetches from OSM and upserts into transit_stops table.
    """
    data = await fetch_transit_stops(lat, lng, radius_meters)
    stops = data.get("stops", [])

    if not stops:
        return {"inserted": 0, "message": "No transit stops found in radius"}

    from app.core.supabase_client import supabase

    rows = [
        {
            "osm_id": s["osm_id"],
            "name": s["name"],
            "stop_type": s["stop_type"],
            "lat": s["lat"],
            "lng": s["lng"],
        }
        for s in stops
    ]

    # Upsert — if osm_id already exists, update it
    result = supabase.table("transit_stops").upsert(rows, on_conflict="osm_id").execute()

    return {
        "inserted": len(rows),
        "transit_score": data["transit_score"],
        "bus_stops": data["bus_stop_count"],
        "rail_stations": data["rail_station_count"],
        "nearest_stop_meters": data["nearest_stop_meters"],
    }