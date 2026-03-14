from fastapi import APIRouter, HTTPException, status

from app.api.schemas.rent_estimate import RentEstimateRequest, RentEstimateResponse
from app.core.rent_estimate import fetch_rent_estimate
from app.services.rent_estimate import RentEstimateServiceError

router = APIRouter(prefix="/api", tags=["rent-estimate"])


@router.post("/rent-estimate", response_model=RentEstimateResponse, status_code=status.HTTP_200_OK)
def get_rent_estimate(payload: RentEstimateRequest) -> RentEstimateResponse:
    try:
        result = fetch_rent_estimate(
            address=payload.address,
            city=payload.city,
            state=payload.state,
            propertyType=payload.propertyType,
            bedrooms=payload.bedrooms,
            bathrooms=payload.bathrooms,
            compCount=payload.compCount,
        )
        return RentEstimateResponse(**result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RentEstimateServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error fetching rent estimate: {exc}",
        ) from exc
