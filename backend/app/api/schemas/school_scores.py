from pydantic import BaseModel
from typing import List, Optional

class AddressRequest(BaseModel):
    address: str

class SchoolItem(BaseModel):
    school_name: str
    level: str
    housmart_school_score: Optional[float]
    s_academic: Optional[float]
    s_resource: Optional[float]
    s_equity: Optional[float]

class SchoolScoreResponse(BaseModel):
    address: str
    total_schools_found: int
    schools: List[SchoolItem]
    message: Optional[str] = None