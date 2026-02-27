import httpx
import math
import redis
import json
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
CACHE_TTL = 60 * 60 * 24 * 30  # 30 days

# Multiple Overpass mirrors — tried in order if one times out
OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

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
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
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
    """
    Fetch transit stops from OSM Overpass within radius.
    Tries multiple mirrors. Results cached in Redis for 30 days.
    """
    cache_key = f"transit:{lat:.4f}:{lng:.4f}:{radius_meters}"

    # 1. Check Redis cache
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Redis cache read failed: {e}")

    # 2. Query Overpass — try each mirror
    query = _build_overpass_query(lat, lng, radius_meters)
    data = None
    last_error = None

    async with httpx.AsyncClient(timeout=30) as client:
        for mirror in OVERPASS_MIRRORS:
            try:
                response = await client.post(mirror, data={"data": query})
                response.raise_for_status()
                data = response.json()
                # Validate response has expected structure
                if "elements" not in data:
                    raise ValueError(f"Unexpected Overpass response structure: {list(data.keys())}")
                logger.info(f"Overpass responded from mirror: {mirror}")
                break
            except Exception as e:
                logger.warning(f"Overpass mirror {mirror} failed: {type(e).__name__}")
                last_error = e
                continue

    if data is None:
        raise Exception(f"All Overpass mirrors failed. Last error: {last_error}")

    # 3. Parse stops
    elements = data.get("elements", [])
    stops = []
    bus_count = 0
    rail_count = 0
    nearest_meters: Optional[float] = None

    for el in elements:
        el_lat = el.get("lat")
        el_lng = el.get("lon")
        if el_lat is None or el_lng is None:
            continue

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

    # 4. Cache result
    try:
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))
    except Exception as e:
        logger.warning(f"Redis cache write failed: {e}")

    return result


async def save_transit_stops_to_db(lat: float, lng: float, radius_meters: int = 800) -> dict:
    """
    Task 1: Fetch stops from OSM and upsert into transit_stops table.
    Handles duplicates via on_conflict="osm_id".
    """
    data = await fetch_transit_stops(lat, lng, radius_meters)
    stops = data.get("stops", [])

    if not stops:
        return {
            "inserted": 0,
            "message": "No transit stops found within radius",
            "transit_score": data["transit_score"],
            "nearest_stop_meters": data["nearest_stop_meters"],
        }

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

    try:
        # on_conflict="osm_id" handles duplicates — updates existing rows
        supabase.table("transit_stops").upsert(
            rows, on_conflict="osm_id"
        ).execute()
    except Exception as e:
        logger.error(f"DB upsert failed for transit stops: {e}")
        raise

    return {
        "inserted": len(rows),
        "transit_score": data["transit_score"],
        "bus_stops": data["bus_stop_count"],
        "rail_stations": data["rail_station_count"],
        "nearest_stop_meters": data["nearest_stop_meters"],
    }


async def save_transit_score_to_db(lat: float, lng: float, radius_meters: int = 800) -> dict:
    """
    Task 3: Calculate transit score and upsert into transit_scores table.
    Handles duplicates via on_conflict="property_lat,property_lng".
    """
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

    try:
        supabase.table("transit_scores").upsert(
            row, on_conflict="property_lat,property_lng"
        ).execute()
    except Exception as e:
        logger.error(f"DB upsert failed for transit score: {e}")
        raise

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
    Task 3 (main): Look up property coordinates from DB,
    calculate distance to nearest transit stop, save score.
    """
    from app.core.supabase_client import supabase

    # 1. Look up property
    response = (
        supabase.table("properties")
        .select("id, formatted_address, latitude, longitude")
        .eq("id", property_id)
        .single()
        .execute()
    )

    if not response.data:
        raise ValueError(f"Property {property_id} not found in database")

    prop = response.data
    lat = prop.get("latitude")
    lng = prop.get("longitude")

    if lat is None or lng is None:
        raise ValueError(f"Property {property_id} has no coordinates (lat/lng is null)")

    address = prop.get("formatted_address", "Unknown address")

    # 2. Calculate and save score
    score_data = await save_transit_score_to_db(lat, lng, radius_meters)

    return {
        "property_id": property_id,
        "property_address": address,
        **score_data,
    }