from pydantic import BaseModel
from typing import Optional


class TransitStopImportRequest(BaseModel):
    lat: float
    lng: float
    radius_meters: int = 800  # standard walkable transit radius


class TransitStop(BaseModel):
    osm_id: str
    name: Optional[str] = None
    stop_type: str          # bus_stop, station, tram_stop, subway_entrance
    lat: float
    lng: float


class TransitScoreResponse(BaseModel):
    property_lat: float
    property_lng: float
    radius_meters: int
    bus_stop_count: int
    rail_station_count: int
    transit_score: float    # 0–100
    nearest_stop_meters: Optional[float] = None
    source: str = "OpenStreetMap (Overpass API)"