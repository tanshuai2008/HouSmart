from fastapi import APIRouter, HTTPException, Query, status

from app.services.median_house_price import get_median_house_price

router = APIRouter(prefix="/api", tags=["median-house-price"])


@router.get("/median-house-price", status_code=status.HTTP_200_OK)
def median_house_price(
    city: str = Query(..., min_length=1),
    state: str = Query(..., min_length=1, max_length=10),
):
    result = get_median_house_price(city=city, state=state)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(result["error"]),
        )
    return result
