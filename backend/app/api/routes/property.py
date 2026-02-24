from fastapi import APIRouter, HTTPException
from app.api.schemas.property import PropertyCreateRequest
from app.services.census_service import CensusService
from app.services.property_repository import PropertyRepository
from app.services.geo_repository import GeoRepository

router = APIRouter()


@router.post("/properties")
def create_property(request: PropertyCreateRequest):

    location_data = CensusService.get_income_by_address(request.address)

    if not location_data:
        raise HTTPException(status_code=404, detail="Address not found")

    # Save tract income separately
    GeoRepository.upsert_tract_income(location_data)

    # Save property without income
    property_data = PropertyRepository.create_property(location_data)

    return property_data