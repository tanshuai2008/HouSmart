from pydantic import BaseModel, Field


class RentEstimateRequest(BaseModel):
    address: str = Field(..., min_length=1, description="Full property address")
    property_type: str = Field(..., min_length=1, description="Property type")
    bedrooms: int = Field(..., ge=0, description="Number of bedrooms")
    bathrooms: float = Field(..., ge=0, description="Number of bathrooms")
    square_footage: int = Field(..., gt=0, description="Square footage of the unit")


class RentEstimateResponse(BaseModel):
    rent: float
    rent_range_low: float | None = None
    rent_range_high: float | None = None
    currency: str
    address: str
