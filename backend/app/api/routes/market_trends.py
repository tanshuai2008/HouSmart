from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel

from app.services.market_trends_service import MarketTrendsError, get_market_trends_for_property


router = APIRouter(prefix="/api", tags=["Market Trends"])


class PriceTrendPoint(BaseModel):
    month: str
    property: float
    market: float = 0


class MedianSalePricePoint(BaseModel):
    month: str
    revenue: int
    expenses: int = 0


class MarketTrendsResponse(BaseModel):
    priceTrend: list[PriceTrendPoint]
    revenueExpenses: list[MedianSalePricePoint]


@router.get("/market-trends", response_model=MarketTrendsResponse)
def get_market_trends(
    response: Response,
    property_id: str = Query(..., min_length=1),
    months: int = Query(36, ge=1, le=60),
):
    """Returns the chart time series used by the dashboard Market Trends graphs.

    This endpoint is property-specific:
    - Looks up the property in `user_properties`
    - Uses that property address to derive city/state
    - Queries Redfin/Supabase trends for that city/state
    - Returns time series in the exact shape the frontend charts expect
    """

    try:
        response.headers["Cache-Control"] = "no-store"
        payload = get_market_trends_for_property(property_id=property_id, months=months)
        # The response_model only includes the two chart series.
        return {
            "priceTrend": payload.get("priceTrend", []),
            "revenueExpenses": payload.get("revenueExpenses", []),
        }
    except MarketTrendsError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        # e.g. missing Supabase credentials
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
