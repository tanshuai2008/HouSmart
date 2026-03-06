from fastapi import APIRouter, HTTPException, status

from app.api.schemas.rent_estimate import RentEstimateRequest, RentEstimateResponse
from app.core.rent_estimate import fetch_rent_estimate
from app.services.rent_estimate import RentEstimateServiceError

router = APIRouter(prefix="/api", tags=["rent-estimate"])


@router.post(
    "/rent_estimate",
    response_model=RentEstimateResponse,
    status_code=status.HTTP_200_OK,
    summary="Estimate market rent for a property address",
)
def get_rent_estimate(payload: RentEstimateRequest) -> RentEstimateResponse:
    """
    Estimates market rent for a given property address using the rent estimation service pipeline.

    Input:
    - JSON body (RentEstimateRequest):
      - address: full street address string.

    Output:
    - RentEstimateResponse model with estimated rent and associated metadata returned by core estimator logic.
    - Includes deterministic validation errors (400), provider/service errors (502), and unexpected errors (500).

    How it is calculated:
    - Delegates to `fetch_rent_estimate`, which normalizes address and queries/combines rent data sources.
    - Applies internal estimation logic and returns structured rent estimate payload.

    What can be extracted:
    - Baseline expected rent, supporting context, and confidence/coverage cues from provider metadata.
    """
    try:
        result = fetch_rent_estimate(
            address=payload.address,
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
