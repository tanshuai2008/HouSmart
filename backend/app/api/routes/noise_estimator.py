from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

from app.services.analysis_repository import AnalysisRepository
from app.services.noise_estimator import estimate_noise_from_address, estimate_noise_from_coordinates

router = APIRouter(prefix="/api", tags=["noise-estimator"])


class NoiseEstimateRequest(BaseModel):
    address: Optional[str] = Field(default=None, min_length=5)
    user_id: Optional[str] = None
    property_id: Optional[str] = None


@router.post(
    "/noise_estimate_score",
    status_code=status.HTTP_200_OK,
    summary="Estimate environmental noise score for an address",
)
def noise_estimate_by_address(
    payload: NoiseEstimateRequest,
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
    result = None
    if payload.user_id and payload.property_id:
        property_row = AnalysisRepository.get_user_property_by_id(
            user_id=payload.user_id,
            property_id=payload.property_id,
        )
        if property_row:
            lat = property_row.get("latitude")
            lng = property_row.get("longitude")
            if lat is not None and lng is not None:
                score_data = estimate_noise_from_coordinates(lat=float(lat), lon=float(lng))
                result = {
                    "address": payload.address or property_row.get("address") or "",
                    "noise_level": score_data.get("noise_level"),
                    "noise_index": score_data.get("noise_index"),
                    "estimated_noise_db": score_data.get("estimated_noise_db"),
                    "distance_to_road_m": score_data.get("distance_to_road_m"),
                    "source": score_data.get("source"),
                    "api_used": score_data.get("api_used"),
                    "latitude": score_data.get("latitude", float(lat)),
                    "longitude": score_data.get("longitude", float(lng)),
                }

    if result is None:
        if not payload.address:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="address is required when user_id/property_id is missing or has no stored coordinates",
            )
        result = estimate_noise_from_address(address=payload.address)

    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(result["error"]),
        )
    return result
