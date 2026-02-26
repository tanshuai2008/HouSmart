from pydantic import BaseModel
from typing import Optional


class FloodCheckRequest(BaseModel):
    lat: float
    lng: float


class FloodZoneResponse(BaseModel):
    property_lat: float
    property_lng: float
    fld_zone: Optional[str] = None      # e.g. "AE", "X", "VE"
    risk_label: str                      # e.g. "High Risk", "Minimal Risk"
    flood_score: float                   # 0–100 (100 = safest)
    flood_data_unknown: bool = False
    source: str = "FEMA National Flood Hazard Layer (NFHL)"