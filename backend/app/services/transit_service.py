import asyncio
import httpx
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import settings
from app.core.supabase_client import supabase
from app.utils.geo import haversine_meters

logger = logging.getLogger(__name__)

GOOGLE_PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

def _compute_transit_score(
    bus_count: int,
    rail_count: int,
    nearest_meters: Optional[float],
    radius_meters: int,
) -> float:
    """
    Normalized 0-100 score based on stop density and proximity.
    Availability-aware weights:
    - nearest-stop proximity keeps fixed 20%
    - bus/rail share the remaining 80% across modes that are present
    """
    if bus_count <= 0 and rail_count <= 0:
        return 5.0

    # Saturation points chosen from existing rubric ranges.
    bus_norm = min(bus_count / 20.0, 1.0)
    rail_norm = min(rail_count / 8.0, 1.0)

    if nearest_meters is None or radius_meters <= 0:
        proximity_norm = 0.0
    else:
        proximity_norm = max(0.0, 1.0 - (nearest_meters / float(radius_meters)))

    mode_weight_pool = 80.0
    active_modes = int(bus_count > 0) + int(rail_count > 0)
    bus_weight = (mode_weight_pool / active_modes) if bus_count > 0 else 0.0
    rail_weight = (mode_weight_pool / active_modes) if rail_count > 0 else 0.0

    score = (bus_norm * bus_weight) + (rail_norm * rail_weight) + (proximity_norm * 20.0)
    return float(round(max(5.0, min(100.0, score)), 1))


def _build_result(
    lat: float,
    lng: float,
    radius_meters: int,
    stops: list[dict],
    bus_count: int,
    rail_count: int,
    nearest_meters: Optional[float],
    source: str,
    api_used: str,
) -> dict:
    return {
        "property_lat": lat,
        "property_lng": lng,
        "radius_meters": radius_meters,
        "bus_stop_count": bus_count,
        "rail_station_count": rail_count,
        "transit_score": _compute_transit_score(
            bus_count=bus_count,
            rail_count=rail_count,
            nearest_meters=nearest_meters,
            radius_meters=radius_meters,
        ),
        "nearest_stop_meters": round(nearest_meters, 1) if nearest_meters else None,
        "stops": stops,
        "source": source,
        "api_used": api_used,
    }


def _normalize_google_stop_type(types: list[str]) -> tuple[str, bool]:
    if "train_station" in types:
        return "train_station", True
    if "subway_station" in types:
        return "subway_station", True
    if "transit_station" in types:
        return "transit_station", True
    if "bus_station" in types:
        return "bus_station", False
    return "transit_station", False


async def _fetch_google_transit(
    client: httpx.AsyncClient, lat: float, lng: float, radius_meters: int
) -> Optional[dict]:
    if not settings.GOOGLE_MAPS_API_KEY:
        logger.warning("GOOGLE_MAPS_API_KEY is empty; Google transit fetch skipped")
        return None

    query_types = ("transit_station", "bus_station", "train_station", "subway_station")
    stops = []
    seen_place_ids = set()
    bus_count = 0
    rail_count = 0
    nearest_meters: Optional[float] = None

    async def _fetch_nearby_pages(place_type: str) -> list[dict]:
        page_results: list[dict] = []
        params = {
            "key": settings.GOOGLE_MAPS_API_KEY,
            "location": f"{lat},{lng}",
            "radius": radius_meters,
            "type": place_type,
        }

        for _ in range(3):
            response = await client.get(GOOGLE_PLACES_NEARBY_URL, params=params)
            response.raise_for_status()
            payload = response.json()
            status = payload.get("status")

            if status in ("OK", "ZERO_RESULTS"):
                page_results.extend(payload.get("results", []))
                next_page_token = payload.get("next_page_token")
                if not next_page_token:
                    break
                # Google nearby pagination token usually needs a brief delay before becoming valid.
                await asyncio.sleep(2)
                params = {"key": settings.GOOGLE_MAPS_API_KEY, "pagetoken": next_page_token}
                continue

            if status == "INVALID_REQUEST" and params.get("pagetoken"):
                await asyncio.sleep(2)
                continue

            raise ValueError(f"Google Places returned status {status} for type={place_type}")

        return page_results

    for place_type in query_types:
        for result in await _fetch_nearby_pages(place_type):
            place_id = result.get("place_id")
            location = (result.get("geometry") or {}).get("location") or {}
            stop_lat = location.get("lat")
            stop_lng = location.get("lng")
            if not place_id or stop_lat is None or stop_lng is None or place_id in seen_place_ids:
                continue
            seen_place_ids.add(place_id)

            stop_type, is_rail = _normalize_google_stop_type(result.get("types", []))
            if is_rail:
                rail_count += 1
            else:
                bus_count += 1

            dist = haversine_meters(lat, lng, stop_lat, stop_lng)
            if nearest_meters is None or dist < nearest_meters:
                nearest_meters = dist

            stops.append(
                {
                    "osm_id": str(place_id),
                    "name": result.get("name"),
                    "stop_type": stop_type,
                    "lat": stop_lat,
                    "lng": stop_lng,
                }
            )

    return _build_result(
        lat=lat,
        lng=lng,
        radius_meters=radius_meters,
        stops=stops,
        bus_count=bus_count,
        rail_count=rail_count,
        nearest_meters=nearest_meters,
        source="Google Maps Places API",
        api_used="google_places",
    )


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


def _is_empty_cached_transit(value: dict) -> bool:
    """Treat zero-stop payloads as refreshable so we can retry provider fetch."""
    bus_count = int(value.get("bus_stop_count") or 0)
    rail_count = int(value.get("rail_station_count") or 0)
    nearest = value.get("nearest_stop_meters")
    return bus_count == 0 and rail_count == 0 and nearest is None


async def fetch_transit_stops(lat: float, lng: float, radius_meters: int = 800) -> dict:
    """Fetch transit stops from Google Places and cache the response."""
    cache_key = f"transit:google:{lat:.4f}:{lng:.4f}:{radius_meters}"
    cached = _cache_get(cache_key)
    if cached:
        if not _is_empty_cached_transit(cached):
            cached.setdefault("api_used", "cache")
            return cached
        logger.info("Cache refresh forced for empty transit payload: %s", cache_key)

    async with httpx.AsyncClient(timeout=settings.GOOGLE_PLACES_HTTP_TIMEOUT_SECONDS) as client:
        try:
            google_result = await _fetch_google_transit(client, lat, lng, radius_meters)
        except Exception:
            # Keep endpoint resilient: if a refresh attempt fails, fallback to stale empty cache.
            if cached:
                logger.warning("Transit refresh failed; falling back to cached payload: %s", cache_key)
                cached.setdefault("api_used", "cache")
                return cached
            raise
    if google_result is None:
        raise Exception("Google transit fetch failed: GOOGLE_MAPS_API_KEY is missing or invalid")
    result = google_result
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
        "api_used": data.get("api_used", "unknown"),
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
