from fastapi import APIRouter, HTTPException
from app.api.schemas.transit import TransitStopImportRequest, TransitScoreResponse
from app.services.transit_service import (
    fetch_transit_stops,
    save_transit_stops_to_db,
    save_transit_score_to_db,
    save_transit_score_for_property,
)

router = APIRouter(prefix="/transit", tags=["Transit"])


@router.post("/import-stops", summary="Task 1 — Import transit stop locations into DB")
async def import_transit_stops(request: TransitStopImportRequest):
    """
    Fetches transit stops from OSM Overpass within the given radius
    and saves them to the transit_stops table in Supabase.
    """
    try:
        result = await save_transit_stops_to_db(
            lat=request.lat,
            lng=request.lng,
            radius_meters=request.radius_meters,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/score", summary="Task 3 — Calculate transit distance & score by lat/lng")
async def get_transit_score(lat: float, lng: float, radius_meters: int = 800):
    """
    Calculates distance to nearest transit stop and score (0-100) for a lat/lng.
    Saves result to transit_scores table.
    """
    try:
        result = await save_transit_score_to_db(lat, lng, radius_meters)
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/score/property/{property_id}",
    summary="Task 3 — Calculate transit distance to nearest stop per property"
)
async def get_transit_score_for_property(property_id: str, radius_meters: int = 800):
    """
    Task 3 (main): Given a property_id, looks up the property lat/lng from
    the properties table, calculates distance to nearest transit stop,
    and saves the transit score to transit_scores table.
    """
    try:
        result = await save_transit_score_for_property(property_id, radius_meters)
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))