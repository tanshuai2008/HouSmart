import os

import requests
from fastapi import APIRouter, HTTPException, Query

from app.api.schemas.rent_estimate import RentEstimateResponse

router = APIRouter(prefix="/api")

@router.get("/rent-estimate", response_model=RentEstimateResponse)
def get_rent_estimate(
    address: str = Query(..., description="The full address for which to receive a rental estimate"),
    propertyType: str | None = Query(None, description="Property type (e.g., apartment)"),
    bedrooms: int | None = Query(None, ge=0, description="Number of bedrooms"),
    bathrroms: int | None = Query(None, ge=0, description="Number of bathrooms"),
    squareFootage: int | None = Query(None, ge=0, description="Square footage"),
):
    api_key = os.getenv("RentEstimate_ApiKey")
    if not api_key:
        raise HTTPException(
            status_code=500, 
            detail="RentEstimate_ApiKey not found in environment variables"
        )

    # Zyla Labs Rental Estimate API Endpoint
    url = "https://zylalabs.com/api/2827/us+rental+estimation+api/2939/get+estimation"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    params = {
        "address": address,
    }

    if propertyType is not None:
        params["propertyType"] = propertyType
    if bedrooms is not None:
        params["bedrooms"] = bedrooms
    if bathrroms is not None:
        params["bathrroms"] = bathrroms
    if squareFootage is not None:
        params["squareFootage"] = squareFootage

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Based on Zyla API response structure:
        # { "rent": 2225, "rent_range_low": 2045, ... }
        
        if "rent" not in data:
            raise HTTPException(
                status_code=404,
                detail="Rent data not available for the provided address."
            )

        return RentEstimateResponse(
            rent=data.get("rent"),
            rent_range_low=data.get("rent_range_low"),
            rent_range_high=data.get("rent_range_high"),
            currency=data.get("currency", "USD"),
            address=address
        )

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502, 
            detail=f"Error communicating with Zyla API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )
