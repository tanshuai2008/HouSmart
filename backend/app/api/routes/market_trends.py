from fastapi import APIRouter
from pydantic import BaseModel


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
def get_market_trends():
    """Returns the chart time series used by the dashboard Market Trends graphs.

    Note: This endpoint currently returns a stable default series (same shape as the
    existing frontend mock data). It exists to let the UI charts fetch from the backend.
    """

    price_trend = [
        {"month": "2021", "property": 98.4, "market": 0},
        {"month": "H2 21", "property": 99.1, "market": 0},
        {"month": "2022", "property": 101.4, "market": 0},
        {"month": "H2 22", "property": 100.8, "market": 0},
        {"month": "2023", "property": 99.0, "market": 0},
        {"month": "H2 23", "property": 98.6, "market": 0},
        {"month": "2024", "property": 99.4, "market": 0},
    ]

    median_sale_price = [
        {"month": "2021", "revenue": 850000, "expenses": 0},
        {"month": "H2 21", "revenue": 920000, "expenses": 0},
        {"month": "2022", "revenue": 1050000, "expenses": 0},
        {"month": "H2 22", "revenue": 1010000, "expenses": 0},
        {"month": "2023", "revenue": 980000, "expenses": 0},
        {"month": "H2 23", "revenue": 995000, "expenses": 0},
        {"month": "2024", "revenue": 1025000, "expenses": 0},
    ]

    return {
        "priceTrend": price_trend,
        "revenueExpenses": median_sale_price,
    }