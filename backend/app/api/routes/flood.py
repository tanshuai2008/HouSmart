from fastapi import APIRouter, HTTPException
from app.api.schemas.flood import FloodCheckRequest, FloodZoneResponse, PropertyFloodResponse
from app.services.flood_service import (
    get_flood_zone,
    save_flood_zone_to_db,
    check_flood_for_property,
    check_all_properties_flood_intersect,
)

router = APIRouter(prefix="/flood", tags=["Flood Risk"])


@router.post("/import", summary="Task 2 — Import FEMA flood zone for a location into DB")
async def import_flood_zone(request: FloodCheckRequest):
    """
    Queries FEMA NFHL for flood zone at lat/lng and saves to flood_zones table.
    Handles duplicates via upsert on (lat, lng).

    - lat/lng: validated -90/90 and -180/180
    - Falls back to geographic mock if FEMA unreachable (non-US IP)
    """
    try:
        result = await save_flood_zone_to_db(lat=request.lat, lng=request.lng)
        return {"status": "success", "data": FloodZoneResponse(**result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check", summary="Task 2 — Check flood zone by lat/lng (no DB write)")
async def check_flood_zone(lat: float, lng: float):
    """
    Returns FEMA flood zone and risk score (0-100) for a lat/lng.
    Uses Redis cache. Does NOT write to DB (read-only).
    """
    if not (-90 <= lat <= 90):
        raise HTTPException(status_code=422, detail="lat must be between -90 and 90")
    if not (-180 <= lng <= 180):
        raise HTTPException(status_code=422, detail="lng must be between -180 and 180")

    try:
        result = await get_flood_zone(lat, lng)
        return {"status": "success", "data": FloodZoneResponse(**result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/check/property/{property_id}",
    summary="Task 4 — Check if a property intersects a flood zone"
)
async def check_property_flood(property_id: str):
    """
    Task 4: Looks up property coordinates from DB, checks FEMA flood zone,
    returns whether property is in high-risk or moderate-risk flood zone.

    Returns 404 if property not found or has no coordinates.
    """
    try:
        result = await check_flood_for_property(property_id)
        return {"status": "success", "data": PropertyFloodResponse(**result)}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/check/all-properties",
    summary="Task 4 — Check ALL properties for flood zone intersections"
)
async def check_all_properties_flood():
    """
    Task 4 (bulk): Checks every property in DB against FEMA flood zones.
    Returns summary counts + full result list.
    Properties with missing coordinates are skipped (reported in skipped_count).
    """
    try:
        result = await check_all_properties_flood_intersect()
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug-fema", summary="Debug — Test raw FEMA API response")
async def debug_fema(lat: float, lng: float):
    """Calls FEMA API directly and returns raw response. For debugging only."""
    import httpx
    params = {
        "geometry": f"{lng-0.001},{lat-0.001},{lng+0.001},{lat+0.001}",
        "geometryType": "esriGeometryEnvelope",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "FLD_ZONE,ZONE_SUBTY,DFIRM_ID",
        "returnGeometry": "false",
        "f": "json",
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query",
                params=params
            )
        return {"status_code": response.status_code, "raw": response.json()}
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}