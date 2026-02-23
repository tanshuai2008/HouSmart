from fastapi import APIRouter, HTTPException
from app.api.schemas.property import PropertyCreateRequest
from app.services.census_service import CensusService
from app.services.property_repository import PropertyRepository

router = APIRouter()


@router.post("/properties")
def create_property(request: PropertyCreateRequest):

    location_data = CensusService.get_location_data(request.address)

    if not location_data:
        raise HTTPException(status_code=404, detail="Address not found")

    property_data = PropertyRepository.create_property(location_data)

    return property_data