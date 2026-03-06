from pydantic import BaseModel, Field
from typing import Optional


class FloodCheckRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude (-90 to 90)")
    lng: float = Field(..., ge=-180, le=180, description="Longitude (-180 to 180)")

class AddressFloodRequest(BaseModel):
    address: str = Field(
        ...,
        min_length=5,
        description="Full street address e.g. '1000 Main St, Houston, TX 77002'"
    )


class FloodZoneResponse(BaseModel):
    property_lat: float
    property_lng: float
    fld_zone: Optional[str] = None
    risk_label: str
    flood_score: float
    flood_data_unknown: bool = False
    source: str = "FEMA National Flood Hazard Layer (NFHL)"


class PropertyFloodResponse(BaseModel):
    property_id: str
    property_address: Optional[str] = None
    property_lat: float
    property_lng: float
    fld_zone: Optional[str] = None
    risk_label: str
    flood_score: float
    in_flood_zone: bool
    in_moderate_zone: bool
    flood_data_unknown: bool
    source: str
class AddressFloodResponse(BaseModel):
    address: str
    property_lat: float
    property_lng: float
    fld_zone: Optional[str] = None
    risk_label: str
    flood_score: float
    in_flood_zone: bool
    in_moderate_zone: bool
    flood_data_unknown: bool
    source: str