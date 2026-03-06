import httpx
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import settings
from app.core.supabase_client import supabase

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": settings.HTTP_USER_AGENT,
    "Accept": "application/json",
}

FLOOD_ZONE_MAP = {
    "AE": ("High Risk - 1% Annual Chance", 20),
    "A": ("High Risk - 1% Annual Chance", 20),
    "AO": ("High Risk - Shallow Flooding", 25),
    "AH": ("High Risk - Shallow Ponding", 25),
    "A99": ("High Risk - Protected by Levee", 30),
    "AR": ("Moderate Risk - Restoring Levee", 30),
    "VE": ("Very High Risk - Coastal Wave Action", 10),
    "V": ("Very High Risk - Coastal", 10),
    "X500": ("Moderate Risk - 0.2% Annual Chance", 60),
    "B": ("Moderate Risk", 60),
    "X": ("Minimal Risk", 95),
    "C": ("Minimal Risk", 95),
    "D": ("Undetermined Risk", 50),
}

HIGH_RISK_ZONES = {"A", "AE", "AO", "AH", "A99", "AR", "VE", "V"}
MODERATE_RISK_ZONES = {"X500", "B"}


def _get_mock_flood_zone(lat: float, lng: float) -> str:
    """Geographic mock for non-US dev environments."""
    if 28.0 <= lat <= 31.0 and -92.0 <= lng <= -88.0:
        return "AE"
    if 24.0 <= lat <= 27.0 and -82.0 <= lng <= -79.0:
        return "VE"
    if 29.0 <= lat <= 30.5 and -96.0 <= lng <= -94.0:
        return "AE"
    if 47.0 <= lat <= 48.5 and -123.0 <= lng <= -121.0:
        return "X"
    return "X"


def _cache_get(cache_key: str) -> Optional[dict]:
    """Read from flood_risk_cache. Returns None if missing, expired, or on any error."""
    try:
        now = datetime.now(timezone.utc).isoformat()
        response = (
            supabase.table("flood_risk_cache")
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
        logger.warning("Flood cache GET failed: %s", exc)
    return None


def _cache_set(cache_key: str, value: dict) -> None:
    """Write to flood_risk_cache. Silently skips on any error."""
    try:
        expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=settings.FLOOD_CACHE_TTL_SECONDS)
        ).isoformat()
        supabase.table("flood_risk_cache").upsert(
            {
                "key": cache_key,
                "value": value,
                "expires_at": expires_at,
            },
            on_conflict="key",
        ).execute()
    except Exception as exc:
        logger.warning("Flood cache SET failed: %s", exc)


async def get_flood_zone(lat: float, lng: float) -> dict:
    """
    Query FEMA NFHL for flood zone at given lat/lng.
    Falls back to geographic mock when FEMA API is unreachable.
    """
    cache_key = f"flood:{lat:.5f}:{lng:.5f}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    used_mock = False
    try:
        params = {
            "geometry": f"{lng-0.001},{lat-0.001},{lng+0.001},{lat+0.001}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "FLD_ZONE,ZONE_SUBTY",
            "returnGeometry": "false",
            "f": "json",
        }
        async with httpx.AsyncClient(
            timeout=settings.FEMA_HTTP_TIMEOUT_SECONDS,
            headers=HEADERS,
            follow_redirects=True,
        ) as client:
            response = await client.get(settings.FEMA_QUERY_URL, params=params)
            response.raise_for_status()
            data = response.json()

        features = data.get("features", [])
        if features:
            attrs = features[0].get("attributes", {})
            fld_zone = attrs.get("FLD_ZONE", "X").strip().upper()
            subtype = attrs.get("ZONE_SUBTY", "").strip().upper()
            if fld_zone == "X" and "0.2" in subtype:
                fld_zone = "X500"
        else:
            fld_zone = "X"
    except Exception as exc:
        logger.warning(
            "FEMA API unavailable (%s), using mock for lat=%s, lng=%s",
            type(exc).__name__,
            lat,
            lng,
        )
        fld_zone = _get_mock_flood_zone(lat, lng)
        used_mock = True

    zone_key = fld_zone if fld_zone in FLOOD_ZONE_MAP else "D"
    risk_label, flood_score = FLOOD_ZONE_MAP[zone_key]

    result = {
        "property_lat": lat,
        "property_lng": lng,
        "fld_zone": fld_zone,
        "risk_label": risk_label,
        "flood_score": float(flood_score),
        "flood_data_unknown": False,
        "source": (
            "FEMA NFHL (mock - FEMA unreachable from local dev)"
            if used_mock
            else "FEMA National Flood Hazard Layer (NFHL)"
        ),
    }
    _cache_set(cache_key, result)
    return result


async def save_flood_zone_to_db(lat: float, lng: float) -> dict:
    """Import flood zone for a lat/lng and upsert into flood_zones table."""
    data = await get_flood_zone(lat, lng)
    row = {
        "lat": lat,
        "lng": lng,
        "fld_zone": data["fld_zone"],
        "risk_label": data["risk_label"],
        "flood_score": data["flood_score"],
        "flood_data_unknown": data["flood_data_unknown"],
        "source": data["source"],
    }
    try:
        supabase.table("flood_zones").upsert(row, on_conflict="lat,lng").execute()
    except Exception as exc:
        logger.error("DB upsert failed for flood zone lat=%s, lng=%s: %s", lat, lng, exc)
        raise
    return data


async def get_flood_zone_by_address(address: str) -> dict:
    """Address-based entry point for flood risk scoring."""
    from app.services.geocoding_service import geocode_address

    lat, lng = await geocode_address(address)
    flood_data = await save_flood_zone_to_db(lat, lng)
    fld_zone = flood_data["fld_zone"]

    return {
        "address": address,
        "property_lat": lat,
        "property_lng": lng,
        "fld_zone": fld_zone,
        "risk_label": flood_data["risk_label"],
        "flood_score": flood_data["flood_score"],
        "in_flood_zone": fld_zone in HIGH_RISK_ZONES,
        "in_moderate_zone": fld_zone in MODERATE_RISK_ZONES,
        "flood_data_unknown": flood_data["flood_data_unknown"],
        "source": flood_data["source"],
    }
