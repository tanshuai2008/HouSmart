# HouSmart/backend/app/api/routes/property.py
from fastapi import APIRouter, HTTPException
from app.api.schemas.property import PropertyCreateRequest
from app.services.census_service import CensusService
from app.services.property_repository import PropertyRepository
from app.services.income_repository import IncomeRepository

router = APIRouter()


@router.post("/properties")
def create_property(request: PropertyCreateRequest):

    location_data = CensusService.get_income_by_address(request.address)

    if not location_data:
        raise HTTPException(status_code=404, detail="Address not found")

    IncomeRepository.upsert_tract_income(location_data)

    property_data = PropertyRepository.create_property(location_data)

    return property_data
