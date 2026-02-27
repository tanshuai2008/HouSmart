import httpx
import math
import redis
import json
from typing import Optional
from app.core.config import settings

# Redis client for caching (30-day TTL)
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
CACHE_TTL = 60 * 60 * 24 * 30  # 30 days

# Multiple Overpass mirrors — tried in order if one times out
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

RAIL_TYPES = {"station", "subway_entrance", "halt", "ferry_terminal"}

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


def _build_overpass_query(lat: float, lng: float, radius_meters: int) -> str:
    return (
        f"[out:json][timeout:25];"
        f"("
        f'node["highway"="bus_stop"](around:{radius_meters},{lat},{lng});'
        f'node["public_transport"="stop_position"](around:{radius_meters},{lat},{lng});'
        f'node["railway"="station"](around:{radius_meters},{lat},{lng});'
        f'node["railway"="subway_entrance"](around:{radius_meters},{lat},{lng});'
        f'node["railway"="tram_stop"](around:{radius_meters},{lat},{lng});'
        f'node["railway"="halt"](around:{radius_meters},{lat},{lng});'
        f");"
        f"out body;"
    )


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _compute_transit_score(bus_count: int, rail_count: int) -> float:
    base_score = 5
    for min_bus, min_rail, score in SCORE_RUBRIC:
        if bus_count >= min_bus and rail_count >= min_rail:
            base_score = score
            break
    if rail_count > 0:
        base_score = min(100, base_score + 15)
    return float(base_score)


async def fetch_transit_stops(lat: float, lng: float, radius_meters: int = 800) -> dict:
    """Fetch transit stops from OSM and compute score. Cached in Redis."""
    cache_key = f"transit:{lat:.4f}:{lng:.4f}:{radius_meters}"

    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    query = _build_overpass_query(lat, lng, radius_meters)

    # Try each mirror in order until one responds
    data = None
    last_error = None
    async with httpx.AsyncClient(timeout=30) as client:
        for mirror in OVERPASS_MIRRORS:
            try:
                response = await client.post(mirror, data={"data": query})
                response.raise_for_status()
                data = response.json()
                break  # success — stop trying mirrors
            except Exception as e:
                last_error = e
                continue  # try next mirror
    if data is None:
        raise Exception(f"All Overpass mirrors failed. Last error: {last_error}")

    elements = data.get("elements", [])
    stops = []
    bus_count = 0
    rail_count = 0
    nearest_meters: Optional[float] = None

    for el in elements:
        el_lat = el.get("lat")
        el_lng = el.get("lon")
        tags = el.get("tags", {})

        stop_type = "bus_stop"
        if tags.get("railway") in ("station", "subway_entrance", "halt"):
            stop_type = tags["railway"]
            rail_count += 1
        else:
            bus_count += 1

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

    result = {
        "property_lat": lat,
        "property_lng": lng,
        "radius_meters": radius_meters,
        "bus_stop_count": bus_count,
        "rail_station_count": rail_count,
        "transit_score": _compute_transit_score(bus_count, rail_count),
        "nearest_stop_meters": round(nearest_meters, 1) if nearest_meters else None,
        "stops": stops,
        "source": "OpenStreetMap (Overpass API)",
    }

    redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))
    return result


async def save_transit_stops_to_db(lat: float, lng: float, radius_meters: int = 800) -> dict:
    """Task 1: Fetch stops from OSM and upsert into transit_stops table."""
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

    supabase.table("transit_stops").upsert(rows, on_conflict="osm_id").execute()

    return {
        "inserted": len(rows),
        "transit_score": data["transit_score"],
        "bus_stops": data["bus_stop_count"],
        "rail_stations": data["rail_station_count"],
        "nearest_stop_meters": data["nearest_stop_meters"],
    }


async def save_transit_score_to_db(lat: float, lng: float, radius_meters: int = 800) -> dict:
    """Task 3 (lat/lng): Calculate transit distance & score and persist to transit_scores."""
    data = await fetch_transit_stops(lat, lng, radius_meters)

    from app.core.supabase_client import supabase

    row = {
        "property_lat": lat,
        "property_lng": lng,
        "radius_meters": radius_meters,
        "bus_stop_count": data["bus_stop_count"],
        "rail_station_count": data["rail_station_count"],
        "nearest_stop_meters": data["nearest_stop_meters"],
        "transit_score": data["transit_score"],
        "source": data["source"],
    }

    supabase.table("transit_scores").upsert(
        row, on_conflict="property_lat,property_lng"
    ).execute()

    return {
        "property_lat": lat,
        "property_lng": lng,
        "nearest_stop_meters": data["nearest_stop_meters"],
        "transit_score": data["transit_score"],
        "bus_stop_count": data["bus_stop_count"],
        "rail_station_count": data["rail_station_count"],
        "source": data["source"],
    }


async def save_transit_score_for_property(
    property_id: str, radius_meters: int = 800
) -> dict:
    """
    Task 3 (main): Look up property lat/lng from properties table,
    calculate distance to nearest transit stop, save score to transit_scores.
    """
    from app.core.supabase_client import supabase

    # 1. Look up property coordinates from DB
    response = (
        supabase.table("properties")
        .select("id, formatted_address, latitude, longitude")
        .eq("id", property_id)
        .single()
        .execute()
    )

    if not response.data:
        raise ValueError(f"Property {property_id} not found in database")

    property_data = response.data
    lat = property_data["latitude"]
    lng = property_data["longitude"]
    address = property_data.get("formatted_address", "Unknown")

    if not lat or not lng:
        raise ValueError(f"Property {property_id} has no coordinates")

    # 2. Calculate transit score using property coordinates
    score_data = await save_transit_score_to_db(lat, lng, radius_meters)

    # 3. Return enriched result with property info
    return {
        "property_id": property_id,
        "property_address": address,
        **score_data,
    }