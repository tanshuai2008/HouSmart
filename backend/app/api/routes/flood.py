from fastapi import APIRouter, HTTPException
from app.api.schemas.flood import FloodCheckRequest, FloodZoneResponse
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
    Queries FEMA NFHL for flood zone at given lat/lng
    and saves to flood_zones table in Supabase.
    """
    try:
        result = await save_flood_zone_to_db(lat=request.lat, lng=request.lng)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check", summary="Task 2 — Check flood zone by lat/lng")
async def check_flood_zone(lat: float, lng: float):
    """Returns FEMA flood zone and risk score (0-100) for a lat/lng."""
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
    Task 4: Looks up property coordinates from DB,
    checks FEMA flood zone, returns whether property
    is in a high-risk or moderate-risk flood zone.
    """
    try:
        result = await check_flood_for_property(property_id)
        return {"status": "success", "data": result}
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
    Task 4 (bulk): Checks every property in the DB against FEMA flood zones.
    Returns a summary of how many are high-risk, moderate, or minimal risk,
    plus a full list with each property's flood zone classification.
    """
    try:
        result = await check_all_properties_flood_intersect()
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug-fema", summary="Debug — Test raw FEMA API response")
async def debug_fema(lat: float, lng: float):
    """Calls FEMA API directly and returns raw response for debugging."""
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