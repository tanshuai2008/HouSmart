# HouSmart/backend/app/api/routes/income.py
from fastapi import APIRouter, HTTPException
from app.api.schemas.property import PropertyCreateRequest
from app.services.census_service import CensusService
from app.services.income_repository import IncomeRepository

router = APIRouter(prefix="/api", tags=["Income"])

@router.post("/median-income")
def get_median_income_by_address(request: PropertyCreateRequest):
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

    