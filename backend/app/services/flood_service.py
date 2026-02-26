import httpx
import redis
import json
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
CACHE_TTL = 60 * 60 * 24 * 180  # 180 days

FEMA_QUERY_URL = (
    "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
)

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


async def get_flood_zone(lat: float, lng: float) -> dict:
    """
    Task 2 & 4: Query FEMA NFHL API for flood zone at given lat/lng.
    Returns zone label, risk label, and 0-100 flood score.
    """
    cache_key = f"flood:{lat:.5f}:{lng:.5f}"

    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    flood_data_unknown = False
    fld_zone = None

    try:
        # Bounding box around the point (0.001 deg ~ 100m)
        xmin = lng - 0.001
        ymin = lat - 0.001
        xmax = lng + 0.001
        ymax = lat + 0.001

        params = {
            "geometry": f"{xmin},{ymin},{xmax},{ymax}",
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "FLD_ZONE,ZONE_SUBTY,DFIRM_ID",
            "returnGeometry": "false",
            "f": "json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(FEMA_QUERY_URL, params=params)
            response.raise_for_status()
            data = response.json()

        features = data.get("features", [])
        if features:
            attrs = features[0].get("attributes", {})
            fld_zone = attrs.get("FLD_ZONE", "").strip().upper()
            subtype = attrs.get("ZONE_SUBTY", "").strip().upper()
            if fld_zone == "X" and "0.2" in subtype:
                fld_zone = "X500"
        else:
            # No flood polygon at this location = minimal risk
            fld_zone = "X"

    except Exception:
        flood_data_unknown = True
        fld_zone = "D"

    zone_key = fld_zone if fld_zone in FLOOD_ZONE_MAP else "D"
    risk_label, flood_score = FLOOD_ZONE_MAP[zone_key]

    result = {
        "property_lat": lat,
        "property_lng": lng,
        "fld_zone": fld_zone,
        "risk_label": risk_label,
        "flood_score": float(flood_score),
        "flood_data_unknown": flood_data_unknown,
        "source": "FEMA National Flood Hazard Layer (NFHL)",
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