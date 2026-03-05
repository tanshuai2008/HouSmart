from typing import Any
from pydantic import BaseModel, Field

class RentEstimateRequest(BaseModel):
    address: str = Field(..., min_length=1, description="Full property address")
    city: str | None = Field(default=None, min_length=1, description="City for the property")
    state: str | None = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="Two-letter state code (e.g., CA, NY)",
    )
    propertyType : str | None = Field(
        default=None,
        min_length=1,
        description=(
            "Property type (Single Family-detached houses, Condo-individual units, Townhouse-attached homes, "
            "Manufactured-factory built/mobile homes, Multi-Family-2-4 units, Apartment-5+ unit complexes, Land-vacant)."
        ),
    )
    bedrooms: int | None = Field(default=None, ge=0, description="Number of bedrooms (0 for studio)")
    bathrooms: float | None = Field(default=None, ge=0, description="Number of bathrooms")
    compCount: int | None = Field(
        default=None,
        ge=1,
        description="Number of comparable rentals to include (1-10 recommended)",
    )


class RentEstimateResponse(BaseModel):
    rent: float
    rent_range_low: float | None = None
    rent_range_high: float | None = None
    currency: str = "USD"
    address: str
    subject_property: dict[str, Any] | None = None
    comparables: list[dict[str, Any]] = Field(default_factory=list)
