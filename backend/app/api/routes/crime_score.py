from __future__ import annotations

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.crime_scoring import compute_crime_safety_score
from app.services.fbi_crime_data import FbiCrimeDataClient
from app.services.geocode_client import GeocodeClient
from app.utils.errors import CrimeSafetyServiceError
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["crime-score"])
_geocode_client = GeocodeClient()
_fbi_client = FbiCrimeDataClient()


class CrimeScoreRequest(BaseModel):
    address: str = Field(..., min_length=3, description="Full mailing address to evaluate")


class AgencyModel(BaseModel):
    ori: str
    name: str
    type: str


class CrimeBreakdownModel(BaseModel):
    alias: str
    offense_code: str
    weight: float
    local_rate_per_100k: float
    national_rate_per_100k: float
    rate_ratio: float
    months_with_data: int
    weighted_local_rate: float
    weighted_national_rate: float


class CrimeScoreResponse(BaseModel):
    normalized_address: str
    agency: AgencyModel
    date_range: Dict[str, str]
    months_analyzed: int
    local_crime_index: float
    national_crime_index: float
    relative_crime_ratio: float
    safety_score: float
    safety_category: str
    offense_breakdown: List[CrimeBreakdownModel]
    data_available: bool
    message: Optional[str]


@router.post(
    "/crime_score",
    response_model=CrimeScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Compute neighborhood crime safety score from address-level geocoding and FBI agency data",
)
def resolve_crime_score(payload: CrimeScoreRequest) -> CrimeScoreResponse:
    """
    Calculates a normalized safety score for an address using local-vs-national FBI crime rates.

    Input:
    - JSON body (CrimeScoreRequest):
      - address: full mailing address string (min length 3).

    Output:
    - CrimeScoreResponse with:
      - normalized_address, agency, date_range, months_analyzed
      - local_crime_index, national_crime_index, relative_crime_ratio
      - safety_score, safety_category
      - offense_breakdown (weighted offense-level details), data_available, message

    How it is calculated:
    - Geocodes address to location/jurisdiction.
    - Maps to reporting agency and pulls FBI crime data.
    - Computes weighted offense indices and scales them into a safety score.

    What can be extracted:
    - Relative safety positioning, dominant contributing offenses, and data coverage quality.
    """
    try:
        result = compute_crime_safety_score(
            payload.address,
            geocode_client=_geocode_client,
            fbi_client=_fbi_client,
        )
    except CrimeSafetyServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error while computing crime score")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to compute crime score") from exc

    return CrimeScoreResponse(**result)
