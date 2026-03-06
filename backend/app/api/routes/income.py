# HouSmart/backend/app/api/routes/income.py
from fastapi import APIRouter, HTTPException
from app.api.schemas.property import PropertyCreateRequest
from app.services.census_service import CensusService
from app.services.income_repository import IncomeRepository

router = APIRouter(prefix="/api", tags=["Income"])

@router.post("/median_income", summary="Get tract-level median household income for an address")
def get_median_income_by_address(request: PropertyCreateRequest):
    """
    Returns tract-level median household income for a provided address from US Census ACS.

    Input:
    - JSON body (PropertyCreateRequest):
      - address: full street address string.

    Output:
    - JSON containing:
      - address: normalized/formatted address
      - median_income: tract median household income in USD
      - currency: fixed value "USD"
      - state_fips, county_fips, tract_geoid: geographic identifiers
      - source: dataset attribution ("US Census ACS 2024")
    - If lookup fails, income/geographic fields are returned as null.

    How it is calculated:
    - Geocodes the input address and resolves census tract.
    - Fetches ACS income metrics for that tract through CensusService.
    - Upserts tract income record via IncomeRepository.

    What can be extracted:
    - Income affordability context for underwriting, pricing, and demand modeling.
    """
    data = CensusService.get_income_by_address(request.address)

    if not data:
        return {
            "address": request.address,
            "median_income": None,
            "currency": "USD",
            "state_fips": None,
            "county_fips": None,
            "tract_geoid": None,
            "source": "US Census ACS 2024"
        }

    IncomeRepository.upsert_tract_income(data)

    return {
        "address": data["formatted_address"],
        "median_income": data["median_income"],
        "currency": "USD",
        "state_fips": data["state_fips"],
        "county_fips": data["county_code"],
        "tract_geoid": data["tract_geoid"],
        "source": "US Census ACS 2024"
    }

    
