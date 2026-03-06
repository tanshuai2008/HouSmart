import httpx
import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import settings
from app.core.supabase_client import supabase

logger = logging.getLogger(__name__)

OVERPASS_MIRRORS = [m.strip() for m in settings.OVERPASS_MIRRORS.split(",") if m.strip()]

SCORE_RUBRIC = [
    (20, 2, 95),
    (15, 1, 85),
    (10, 1, 75),
    (8, 0, 65),
    (5, 0, 50),
    (3, 0, 35),
    (1, 0, 20),
    (0, 0, 5),
]


def _build_overpass_query(lat: float, lng: float, radius_meters: int) -> str:
    return (
        f"[out:json][timeout:{settings.OVERPASS_QUERY_TIMEOUT_SECONDS}];"
        "("
        f'node["highway"="bus_stop"](around:{radius_meters},{lat},{lng});'
        f'node["public_transport"="stop_position"](around:{radius_meters},{lat},{lng});'
        f'node["railway"="station"](around:{radius_meters},{lat},{lng});'
        f'node["railway"="subway_entrance"](around:{radius_meters},{lat},{lng});'
        f'node["railway"="tram_stop"](around:{radius_meters},{lat},{lng});'
        f'node["railway"="halt"](around:{radius_meters},{lat},{lng});'
        ");"
        "out body;"
    )


def _haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_m = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _compute_transit_score(bus_count: int, rail_count: int) -> float:
    base_score = 5
    for min_bus, min_rail, score in SCORE_RUBRIC:
        if bus_count >= min_bus and rail_count >= min_rail:
            base_score = score
            break
    if rail_count > 0:
        base_score = min(100, base_score + 15)
    return float(base_score)


def _cache_get(cache_key: str) -> Optional[dict]:
    """Read from transit_cache. Returns None if missing, expired, or on any error."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        response = (
            supabase.table("transit_cache")
            .select("value")
            .eq("key", cache_key)
            .gt("expires_at", now)
            .single()
            .execute()
        )
        if response.data:
            logger.info("Cache HIT: %s", cache_key)
            return response.data["value"]
    except Exception as exc:
        logger.warning("Transit cache GET failed: %s", exc)
    return None


def _cache_set(cache_key: str, value: dict) -> None:
    """Write to transit_cache. Silently skips on any error."""
    try:
        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=settings.TRANSIT_CACHE_TTL_SECONDS)
        ).isoformat()
        supabase.table("transit_cache").upsert(
            {
                "key": cache_key,
                "value": value,
                "expires_at": expires_at,
            },
            on_conflict="key",
        ).execute()
    except Exception as exc:
        logger.warning("Transit cache SET failed: %s", exc)


async def fetch_transit_stops(lat: float, lng: float, radius_meters: int = 800) -> dict:
    """Fetch transit stops from OSM Overpass within radius and cache the response."""
    cache_key = f"transit:{lat:.4f}:{lng:.4f}:{radius_meters}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    query = _build_overpass_query(lat, lng, radius_meters)
    data = None
    last_error = None

    async with httpx.AsyncClient(timeout=settings.OVERPASS_HTTP_TIMEOUT_SECONDS) as client:
        for mirror in OVERPASS_MIRRORS:
            try:
                response = await client.post(mirror, data={"data": query})
                response.raise_for_status()
                data = response.json()
                if "elements" not in data:
                    raise ValueError(
                        f"Unexpected Overpass response structure: {list(data.keys())}"
                    )
                logger.info("Overpass responded from mirror: %s", mirror)
                break
            except Exception as exc:
                logger.warning("Overpass mirror %s failed: %s", mirror, type(exc).__name__)
                last_error = exc

    if data is None:
        raise Exception(f"All Overpass mirrors failed. Last error: {last_error}")

    elements = data.get("elements", [])
    stops = []
    bus_count = 0
    rail_count = 0
    nearest_meters: Optional[float] = None

    for element in elements:
        stop_lat = element.get("lat")
        stop_lng = element.get("lon")
        if stop_lat is None or stop_lng is None:
            continue

        tags = element.get("tags", {})
        stop_type = "bus_stop"
        if tags.get("railway") in ("station", "subway_entrance", "halt"):
            stop_type = tags["railway"]
            rail_count += 1
        else:
            bus_count += 1

        dist = _haversine_meters(lat, lng, stop_lat, stop_lng)
        if nearest_meters is None or dist < nearest_meters:
            nearest_meters = dist

        stops.append(
            {
                "osm_id": str(element.get("id")),
                "name": tags.get("name"),
                "stop_type": stop_type,
                "lat": stop_lat,
                "lng": stop_lng,
            }
        )

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

    _cache_set(cache_key, result)
    return result


async def save_transit_score_to_db(lat: float, lng: float, radius_meters: int = 800) -> dict:
    """Calculate transit score and upsert into transit_scores table."""
    data = await fetch_transit_stops(lat, lng, radius_meters)

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
            row,
            on_conflict="property_lat,property_lng",
        ).execute()
    except Exception as exc:
        logger.error("DB upsert failed for transit score: %s", exc)
        raise

    return {
        "property_lat": lat,
        "property_lng": lng,
        "radius_meters": radius_meters,
        "nearest_stop_meters": data["nearest_stop_meters"],
        "transit_score": data["transit_score"],
        "bus_stop_count": data["bus_stop_count"],
        "rail_station_count": data["rail_station_count"],
        "source": data["source"],
    }


async def get_transit_score_by_address(address: str, radius_meters: int = 800) -> dict:
    """Address-based entry point for transit scoring."""
    from app.services.geocoding_service import geocode_address

    lat, lng = await geocode_address(address)
    score_data = await save_transit_score_to_db(lat, lng, radius_meters)

    return {
        "address": address,
        **score_data,
    }
