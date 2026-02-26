from fastapi import APIRouter, HTTPException
from app.api.schemas.transit import TransitStopImportRequest, TransitScoreResponse
from app.services.transit_service import fetch_transit_stops, save_transit_stops_to_db

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


@router.get("/score", summary="Task 3 — Calculate transit score for a property")
async def get_transit_score(lat: float, lng: float, radius_meters: int = 800):
    """
    Returns the transit score (0–100) for a property location.
    Counts bus stops and rail stations within the radius.
    Includes distance to nearest stop.
    """
    try:
        result = await fetch_transit_stops(lat, lng, radius_meters)
        return {
            "status": "success",
            "data": TransitScoreResponse(
                property_lat=result["property_lat"],
                property_lng=result["property_lng"],
                radius_meters=result["radius_meters"],
                bus_stop_count=result["bus_stop_count"],
                rail_station_count=result["rail_station_count"],
                transit_score=result["transit_score"],
                nearest_stop_meters=result["nearest_stop_meters"],
                source=result["source"],
            )
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))