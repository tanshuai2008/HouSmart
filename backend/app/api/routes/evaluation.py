from fastapi import APIRouter, HTTPException
from app.services.poi_service import POIService
from app.api.schemas.location import LocationRequest
from app.services.property_repository import PropertyRepository

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])

property_repo = PropertyRepository()
poi_service = POIService()

@router.post("/amenity-score")
def amenity_score(payload: LocationRequest):

    service = POIService()

    result = service.compute_all_categories(
        payload.latitude,
        payload.longitude
    )

    return {
        "status": "success",
        "data": result
    }

@router.get("/{property_id}/location-intelligence")
def location_intelligence(property_id: str):

    property = property_repo.get_by_id(property_id)

    if not property:
        raise HTTPException(status_code=404, detail="Property not found")

    result = poi_service.compute_all_categories(
        property["latitude"],
        property["longitude"]
    )

    return {
        "status": "success",
        "property_id": property_id,
        "data": result
    }