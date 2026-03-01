from datetime import datetime, timezone

from fastapi import APIRouter
from app.services.median_house_price import get_median_house_price

router = APIRouter(prefix="/housing", tags=["Housing"])


@router.get("/median-price")
def median_price(city: str, state: str):
    result = get_median_house_price(city, state)
    if not isinstance(result, dict) or result.get("error"):
        return result

    city_out = str(result.get("city") or city).strip()
    state_out = str(result.get("state") or state).strip().upper()
    return {
        "date": datetime.now(timezone.utc).date().isoformat(),
        "place_name": f"{city_out}, {state_out}",
        "period": result.get("period"),
        "median_price": result.get("median_sale_price"),
    }