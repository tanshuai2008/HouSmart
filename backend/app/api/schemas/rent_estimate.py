from typing import Optional

from pydantic import BaseModel


class RentEstimateResponse(BaseModel):
    rent: float
    rent_range_low: Optional[float] = None
    rent_range_high: Optional[float] = None
    currency: str = "USD"
    address: str
