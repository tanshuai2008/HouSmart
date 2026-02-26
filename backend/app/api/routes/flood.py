from fastapi import APIRouter, HTTPException
from app.api.schemas.flood import FloodCheckRequest, FloodZoneResponse
from app.services.flood_service import get_flood_zone, save_flood_zone_to_db
import httpx

router = APIRouter(prefix="/flood", tags=["Flood Risk"])


@router.post("/import", summary="Task 2 — Import FEMA flood zone for a property into DB")
async def import_flood_zone(request: FloodCheckRequest):
    try:
        result = await save_flood_zone_to_db(lat=request.lat, lng=request.lng)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/check", summary="Task 4 — Check if property intersects a flood zone")
async def check_flood_zone(lat: float, lng: float):
    try:
        result = await get_flood_zone(lat, lng)
        return {"status": "success", "data": FloodZoneResponse(**result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug-fema", summary="Debug — Test raw FEMA API response")
async def debug_fema(lat: float, lng: float):
    """
    Calls FEMA API directly and returns the raw response.
    Use this to diagnose what FEMA is returning.
    """
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

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query",
                params=params
            )
        return {
            "status_code": response.status_code,
            "raw_response": response.json(),
            "url_called": str(response.url),
        }
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}