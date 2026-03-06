# HouSmart/backend/app/api/routes/education.py
from fastapi import APIRouter
from app.api.schemas.property import PropertyCreateRequest
from app.services.census_service import CensusService
from app.services.education_repository import EducationRepository

router = APIRouter(prefix="/api", tags=["Education"])


@router.post("/education_level", summary="Get tract-level bachelor's attainment for an address")
def get_education_level_by_address(request: PropertyCreateRequest):
    """
    Returns tract-level bachelor's degree attainment for a provided address using US Census ACS data.

    Input:
    - JSON body (PropertyCreateRequest):
      - address: full street address string.

    Output:
    - JSON containing:
      - address: normalized/formatted address
      - bachelor_percentage: percent of residents with bachelor's degree or higher
      - state_fips, county_fips, tract_geoid: geographic identifiers
      - source: dataset attribution ("US Census ACS 2024")
    - If lookup fails, geographic fields and bachelor_percentage are returned as null.

    How it is calculated:
    - Geocodes address and maps it to census geography via CensusService.
    - Reads ACS education attributes for the resolved tract.
    - Persists/upserts the tract-level education snapshot in EducationRepository.

    What can be extracted:
    - Education attainment signal for neighborhood quality scoring, targeting, and market segmentation.
    """
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
