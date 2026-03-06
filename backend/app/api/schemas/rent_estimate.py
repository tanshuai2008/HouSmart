from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class RentEstimateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address: str = Field(..., min_length=1, description="Full property address")


class RentEstimateResponse(BaseModel):
    rent: float
    rent_range_low: float | None = None
    rent_range_high: float | None = None
    currency: str = "USD"
    address: str
    subject_property: dict[str, Any] | None = None
    comparables: list[dict[str, Any]] = Field(default_factory=list)
