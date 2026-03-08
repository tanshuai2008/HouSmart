from fastapi import APIRouter, HTTPException, status
from app.api.schemas.property import PropertyCreateRequest
from app.api.schemas.school_scores import SchoolScoreResponse
from app.services.school_scores_service import (
    SchoolScoreServiceError,
    fetch_school_scores,
)

router = APIRouter(prefix="/api", tags=["School"])


@router.post(
    "/school_scores",
    response_model=SchoolScoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Get school scores for a property address",
)
def get_school_scores(payload: PropertyCreateRequest) -> SchoolScoreResponse:
    """
    Returns nearby/matched school scores for a provided property address.

    Input:
    - JSON body (PropertyCreateRequest):
      - address: full street address string.

    Output:
    - SchoolScoreResponse model containing:
      - search_type: lookup mode used ("address" or ZIP fallback)
      - search_value: the resolved lookup value
      - total_schools_found: number of schools returned
      - schools: list of school score objects
      - message: optional no-results context
    - Error handling:
      - 400 for invalid input (e.g., empty address)
      - 502 for upstream/service/database query failures
      - 500 for unexpected internal failures

    How it is calculated:
    - Normalizes the input address and calls `get_property_school_scores` RPC.
    - If no direct address match is found, extracts ZIP from address and queries `school_master`.
    - Returns ranked/available school score rows from the data store.

    What can be extracted:
    - School quality signal for location comparison, family-fit scoring, and neighborhood decisioning.
    """
    try:
        result = fetch_school_scores(address=payload.address)
        return SchoolScoreResponse(**result)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except SchoolScoreServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error fetching school scores: {exc}",
        ) from exc
