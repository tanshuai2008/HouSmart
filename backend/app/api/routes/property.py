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

@router.post("/education")
def fetch_education(request: PropertyCreateRequest):

    location_data = CensusService.get_location_data(request.address)

    if not location_data:
        raise HTTPException(status_code=404, detail="Address not found")

    income = CensusService.get_median_income(
        state=location_data["state_fips"],
        county=location_data["county_code"],
        tract=location_data["tract_code"]
    )

    bachelor_pct = CensusService.get_bachelor_percentage(
        state=location_data["state_fips"],
        county=location_data["county_code"],
        tract=location_data["tract_code"]
    )

    GeoRepository.upsert_tract_metrics({
        "tract_geoid": location_data["tract_geoid"],
        "state_fips": location_data["state_fips"],
        "county_fips": location_data["county_fips"],
        "median_income": income,
        "education_bachelor_pct": bachelor_pct
    })

    return {
        "tract_geoid": location_data["tract_geoid"],
        "median_income": income,
        "education_bachelor_pct": bachelor_pct
    }