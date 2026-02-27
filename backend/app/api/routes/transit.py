from fastapi import APIRouter, HTTPException
from app.api.schemas.transit import (
    TransitStopImportRequest,
    TransitScoreResponse,
    PropertyTransitScoreResponse,
)
from app.services.transit_service import (
    save_transit_stops_to_db,
    save_transit_score_to_db,
    save_transit_score_for_property,
)

router = APIRouter(prefix="/transit", tags=["Transit"])


@router.post("/import-stops", summary="Task 1 — Import transit stop locations into DB")
async def import_transit_stops(request: TransitStopImportRequest):
    """
    Fetches all transit stops from OSM Overpass within radius and saves
    to transit_stops table. Handles duplicates via upsert on osm_id.

    - lat/lng: validated -90/90 and -180/180
    - radius_meters: 100–5000m (default 800m)
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


@router.get("/score", summary="Task 3 — Calculate transit score by lat/lng")
async def get_transit_score(
    lat: float = ...,
    lng: float = ...,
    radius_meters: int = 800,
):
    """
    Calculates transit score (0-100) and nearest stop distance for a lat/lng.
    Saves result to transit_scores table.
    """
    if not (-90 <= lat <= 90):
        raise HTTPException(status_code=422, detail="lat must be between -90 and 90")
    if not (-180 <= lng <= 180):
        raise HTTPException(status_code=422, detail="lng must be between -180 and 180")
    if not (100 <= radius_meters <= 5000):
        raise HTTPException(status_code=422, detail="radius_meters must be between 100 and 5000")

    try:
        result = await save_transit_score_to_db(lat, lng, radius_meters)
        return {"status": "success", "data": TransitScoreResponse(**result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/score/property/{property_id}",
    summary="Task 3 — Calculate transit distance to nearest stop per property"
)
async def get_transit_score_for_property(
    property_id: str,
    radius_meters: int = 800,
):
    """
    Task 3 (main): Looks up property lat/lng from DB, calculates distance
    to nearest transit stop, saves score to transit_scores table.

    Returns 404 if property not found or has no coordinates.
    """
    if not (100 <= radius_meters <= 5000):
        raise HTTPException(status_code=422, detail="radius_meters must be between 100 and 5000")

    try:
        result = await save_transit_score_for_property(property_id, radius_meters)
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))