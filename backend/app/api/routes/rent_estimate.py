from fastapi import APIRouter, HTTPException, status

from app.api.schemas.rent_estimate import RentEstimateRequest, RentEstimateResponse
from app.services.rent_estimate import RentEstimateServiceError, fetch_rent_estimate
from app.services.supabase_client import get_supabase

router = APIRouter(prefix="/api", tags=["rent-estimate"])


@router.post("/rent-estimate", response_model=RentEstimateResponse, status_code=status.HTTP_200_OK)
def get_rent_estimate(payload: RentEstimateRequest) -> RentEstimateResponse:
    try:
        supabase_client = get_supabase()
        result = fetch_rent_estimate(
            address=payload.address,
            city=payload.city,
            state=payload.state,
            propertyType=payload.propertyType,
            bedrooms=payload.bedrooms,
            bathrooms=payload.bathrooms,
            compCount=payload.compCount,
            supabase_client=supabase_client,
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
