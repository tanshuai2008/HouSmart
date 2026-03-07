from fastapi import APIRouter, HTTPException, status
from app.api.schemas.school_scores import AddressRequest, SchoolScoreResponse
from app.core.school_scores import fetch_school_scores, SchoolScoreServiceError

router = APIRouter(prefix="/api", tags=["school-scores"])

@router.post("/property/school-scores", response_model=SchoolScoreResponse, status_code=status.HTTP_200_OK)
def get_school_scores(payload: AddressRequest) -> SchoolScoreResponse:
    try:
        result = fetch_school_scores(
            address=payload.address
        )
        return SchoolScoreResponse(**result)
        
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