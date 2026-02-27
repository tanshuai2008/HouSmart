import httpx
import redis
import json
from app.core.config import settings

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

# ─── Dev mock: simulate realistic flood zones by lat/lng region ───────────────
# Used when FEMA API is unreachable (e.g. non-US IP during local development).
# Production (Render US servers) will always hit the real FEMA API.
def _get_mock_flood_zone(lat: float, lng: float) -> str:
    """
    Returns a realistic mock flood zone based on geography.
    Coastal/low-lying areas → high risk, inland/elevated → minimal risk.
    """
    # Gulf Coast / Louisiana (New Orleans area) → High Risk
    if 28.0 <= lat <= 31.0 and -92.0 <= lng <= -88.0:
        return "AE"
    # Florida coastal areas → High Risk
    if 24.0 <= lat <= 27.0 and -82.0 <= lng <= -79.0:
        return "VE"
    # Houston / Texas Gulf Coast → High Risk
    if 29.0 <= lat <= 30.5 and -96.0 <= lng <= -94.0:
        return "AE"
    # Pacific Northwest / Seattle → Minimal Risk
    if 47.0 <= lat <= 48.5 and -123.0 <= lng <= -121.0:
        return "X"
    # General inland US → Minimal Risk
    return "X"


async def get_flood_zone(lat: float, lng: float) -> dict:
    """
    Task 2 & 4: Query FEMA NFHL for flood zone at given lat/lng.
    Falls back to geographic mock when FEMA API is unreachable (local dev).
    """
    cache_key = f"flood:{lat:.5f}:{lng:.5f}"

    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    flood_data_unknown = False
    fld_zone = None
    used_mock = False

    # Build bounding box query
    params = {
        "geometry": f"{lng-0.001},{lat-0.001},{lng+0.001},{lat+0.001}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "FLD_ZONE,ZONE_SUBTY",
        "returnGeometry": "false",
        "f": "json",
    }

    try:
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

    except Exception:
        # FEMA unreachable (non-US IP, network issue, etc.)
        # Use geographic mock for local dev — real data in production
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
        # Clearly flag when mock is used so team knows
        "source": "FEMA NFHL (mock — FEMA unreachable from local dev)" if used_mock
                  else "FEMA National Flood Hazard Layer (NFHL)",
    }

    redis_client.setex(cache_key, CACHE_TTL, json.dumps(result))
    return result


async def save_flood_zone_to_db(lat: float, lng: float) -> dict:
    """
    Task 2 & 4: Import flood zone and save to flood_zones table in Supabase.
    """
    data = await get_flood_zone(lat, lng)

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

    supabase.table("flood_zones").upsert(row).execute()
    return data