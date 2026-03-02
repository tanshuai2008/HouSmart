# HouSmart/backend/app/api/routes/education.py
from fastapi import APIRouter
from app.api.schemas.property import PropertyCreateRequest
from app.services.census_service import CensusService
from app.services.education_repository import EducationRepository

router = APIRouter(prefix="/api", tags=["Education"])


@router.post("/education-level")
def get_education_level_by_address(request: PropertyCreateRequest):
    data = CensusService.get_education_by_address(request.address)

    if not data:
        return {
            "address": request.address,
            "bachelor_percentage": None,
            "state_fips": None,
            "county_fips": None,
            "tract_geoid": None,
            "source": "US Census ACS 2024"
        }

    EducationRepository.upsert_tract_education(data)

    return {
        "address": data["formatted_address"],
        "bachelor_percentage": data["bachelor_percentage"],
        "state_fips": data["state_fips"],
        "county_fips": data["county_code"],
        "tract_geoid": data["tract_geoid"],
        "source": "US Census ACS 2024"
    }