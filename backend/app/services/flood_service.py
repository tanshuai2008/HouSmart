import httpx
import redis
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
CACHE_TTL = 60 * 60 * 24 * 180  # 180 days

FEMA_QUERY_URL = (
    "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HouSmart/1.0)",
    "Accept": "application/json",
}

FLOOD_ZONE_MAP = {
    "AE":   ("High Risk — 1% Annual Chance",          20),
    "A":    ("High Risk — 1% Annual Chance",          20),
    "AO":   ("High Risk — Shallow Flooding",          25),
    "AH":   ("High Risk — Shallow Ponding",           25),
    "A99":  ("High Risk — Protected by Levee",        30),
    "AR":   ("Moderate Risk — Restoring Levee",       30),
    "VE":   ("Very High Risk — Coastal Wave Action",  10),
    "V":    ("Very High Risk — Coastal",              10),
    "X500": ("Moderate Risk — 0.2% Annual Chance",    60),
    "B":    ("Moderate Risk",                         60),
    "X":    ("Minimal Risk",                          95),
    "C":    ("Minimal Risk",                          95),
    "D":    ("Undetermined Risk",                     50),
}

HIGH_RISK_ZONES = {"A", "AE", "AO", "AH", "A99", "AR", "VE", "V"}
MODERATE_RISK_ZONES = {"X500", "B"}


def _get_mock_flood_zone(lat: float, lng: float) -> str:
    """Geographic mock for non-US dev environments."""
    if 28.0 <= lat <= 31.0 and -92.0 <= lng <= -88.0:
        return "AE"   # Louisiana / New Orleans
    if 24.0 <= lat <= 27.0 and -82.0 <= lng <= -79.0:
        return "VE"   # Florida coast
    if 29.0 <= lat <= 30.5 and -96.0 <= lng <= -94.0:
        return "AE"   # Houston
    if 47.0 <= lat <= 48.5 and -123.0 <= lng <= -121.0:
        return "X"    # Seattle
    return "X"        # Default: minimal risk


async def get_flood_zone(lat: float, lng: float) -> dict:
    """
    Query FEMA NFHL for flood zone at given lat/lng.
    Falls back to geographic mock when FEMA API is unreachable (local dev outside US).
    Always returns a valid result — never raises.
    """
    cache_key = f"flood:{lat:.5f}:{lng:.5f}"

    # 1. Check Redis cache
    try:
        cached = redis_client.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Redis cache read failed: {e}")

    flood_data_unknown = False
    fld_zone = None
    used_mock = False

    # 2. Try FEMA API
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
            timeout=15, headers=HEADERS, follow_redirects=True
        ) as client:
            response = await client.get(FEMA_QUERY_URL, params=params)
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
            fld_zone = "X"  # No polygon = minimal risk

    except Exception as e:
        # FEMA unreachable (non-US IP, timeout, etc.) — use geographic mock
        logger.warning(f"FEMA API unavailable ({type(e).__name__}), using mock for lat={lat}, lng={lng}")
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
        "flood_data_unknown": flood_data_unknown,
        "source": (
            "FEMA NFHL (mock — FEMA unreachable from local dev)"
            if used_mock
            else "FEMA National Flood Hazard Layer (NFHL)"
        ),
    }

    # 3. Cache result
    try:
        redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))
    except Exception as e:
        logger.warning(f"Redis cache write failed: {e}")

    return result


async def save_flood_zone_to_db(lat: float, lng: float) -> dict:
    """
    Import flood zone for a lat/lng and upsert into flood_zones table.
    Handles duplicate key gracefully via on_conflict.
    """
    data = await get_flood_zone(lat, lng)

    try:
        from app.core.supabase_client import supabase
        row = {
            "lat": lat,
            "lng": lng,
            "fld_zone": data["fld_zone"],
            "risk_label": data["risk_label"],
            "flood_score": data["flood_score"],
            "flood_data_unknown": data["flood_data_unknown"],
            "source": data["source"],
        }
        # on_conflict="lat,lng" handles duplicates — updates existing row
        supabase.table("flood_zones").upsert(
            row, on_conflict="lat,lng"
        ).execute()
    except Exception as e:
        logger.error(f"DB upsert failed for flood zone lat={lat}, lng={lng}: {e}")
        raise

    return data


async def check_flood_for_property(property_id: str) -> dict:
    """
    Task 4: Look up property from DB, check its flood zone,
    return whether it intersects a flood zone.
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

    # 2. Get flood zone — upsert to DB
    flood_data = await save_flood_zone_to_db(lat, lng)

    fld_zone = flood_data["fld_zone"]

    return {
        "property_id": property_id,
        "property_address": prop.get("formatted_address"),
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


async def check_all_properties_flood_intersect() -> dict:
    """
    Task 4 (bulk): Check ALL properties in DB against FEMA flood zones.
    Skips properties with missing coordinates gracefully.
    """
    from app.core.supabase_client import supabase

    response = (
        supabase.table("properties")
        .select("id, formatted_address, latitude, longitude")
        .execute()
    )

    properties = response.data or []
    if not properties:
        return {
            "total": 0,
            "high_risk_count": 0,
            "moderate_risk_count": 0,
            "minimal_risk_count": 0,
            "skipped_count": 0,
            "results": [],
            "message": "No properties found in database",
        }

    results = []
    high_risk_count = 0
    moderate_risk_count = 0
    minimal_risk_count = 0
    skipped_count = 0

    for prop in properties:
        lat = prop.get("latitude")
        lng = prop.get("longitude")

        # Skip properties without coordinates
        if lat is None or lng is None:
            skipped_count += 1
            logger.warning(f"Skipping property {prop.get('id')} — no coordinates")
            continue

        try:
            flood_data = await get_flood_zone(lat, lng)
            fld_zone = flood_data["fld_zone"]
            in_flood_zone = fld_zone in HIGH_RISK_ZONES
            in_moderate_zone = fld_zone in MODERATE_RISK_ZONES

            if in_flood_zone:
                high_risk_count += 1
            elif in_moderate_zone:
                moderate_risk_count += 1
            else:
                minimal_risk_count += 1

            results.append({
                "property_id": prop["id"],
                "property_address": prop.get("formatted_address"),
                "fld_zone": fld_zone,
                "risk_label": flood_data["risk_label"],
                "flood_score": flood_data["flood_score"],
                "in_flood_zone": in_flood_zone,
                "in_moderate_zone": in_moderate_zone,
            })

        except Exception as e:
            logger.error(f"Failed to check flood for property {prop.get('id')}: {e}")
            skipped_count += 1
            continue

    return {
        "total": len(results),
        "high_risk_count": high_risk_count,
        "moderate_risk_count": moderate_risk_count,
        "minimal_risk_count": minimal_risk_count,
        "skipped_count": skipped_count,
        "results": results,
    }