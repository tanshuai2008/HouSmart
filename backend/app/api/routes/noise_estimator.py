from fastapi import APIRouter, HTTPException, status

from app.api.schemas.location import AddressRequest
from app.services.noise_estimator import estimate_noise_from_address

router = APIRouter(prefix="/api", tags=["noise-estimator"])


@router.post(
    "/noise_estimate_score",
    status_code=status.HTTP_200_OK,
    summary="Estimate environmental noise score for an address",
)
def noise_estimate_by_address(
    payload: AddressRequest,
):
    """
    Estimates environmental noise score for a property address.

    Input:
    - JSON body (AddressRequest):
      - address: full street address string.

    Output:
    - JSON result from noise estimator service, typically including score/value bands and contextual attributes.
    - Returns 404 when required lookup context for estimation cannot be resolved.

    How it is calculated:
    - Normalizes/geocodes address through noise estimation pipeline.
    - Computes modeled noise characteristics for the resolved coordinates.
    - Returns structured score output from `estimate_noise_from_address`.

    What can be extracted:
    - Relative noise exposure signal for livability comparison and screening.
    """
    result = estimate_noise_from_address(address=payload.address)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(result["error"]),
        )
    return result
