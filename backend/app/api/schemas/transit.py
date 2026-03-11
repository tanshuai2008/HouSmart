from pydantic import BaseModel, Field
from typing import Optional


class TransitStopImportRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude (-90 to 90)")
    lng: float = Field(..., ge=-180, le=180, description="Longitude (-180 to 180)")
    radius_meters: int = Field(
        default=800, ge=100, le=5000,
        description="Search radius in meters (100–5000). Default: 800m (walkable distance)"
    )

class AddressTransitRequest(BaseModel):
    address: Optional[str] = Field(
        default=None,
        min_length=5,
        description="Full street address e.g. '1000 Main St, Houston, TX 77002'",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for looking up property coordinates from user_properties.",
    )
    property_id: Optional[str] = Field(
        default=None,
        description="Property ID for looking up coordinates from user_properties.",
    )
    radius_meters: int = Field(
        default=800, ge=100, le=5000,
        description="Search radius in meters (100–5000). Default: 800m"
    )


class TransitStop(BaseModel):
    osm_id: str
    name: Optional[str] = None
    stop_type: str
    lat: float
    lng: float


class TransitScoreResponse(BaseModel):
    property_lat: float
    property_lng: float
    radius_meters: int
    bus_stop_count: int
    rail_station_count: int
    transit_score: float
    nearest_stop_meters: Optional[float] = None
    source: str = "OpenStreetMap (Overpass API)"


class PropertyTransitScoreResponse(BaseModel):
    property_id: str
    property_address: Optional[str] = None
    property_lat: float
    property_lng: float
    nearest_stop_meters: Optional[float] = None
    transit_score: float
    bus_stop_count: int
    rail_station_count: int
    source: str
