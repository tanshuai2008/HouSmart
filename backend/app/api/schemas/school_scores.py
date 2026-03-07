# from pydantic import BaseModel
# from typing import List, Optional

# class AddressRequest(BaseModel):
#     address: str

# class SchoolItem(BaseModel):
#     school_name: str
#     level: str
#     housmart_school_score: Optional[float]
#     s_academic: Optional[float]
#     s_resource: Optional[float]
#     s_equity: Optional[float]

# class SchoolScoreResponse(BaseModel):
#     address: str
#     total_schools_found: int
#     schools: List[SchoolItem]
#     message: Optional[str] = None

from pydantic import BaseModel, model_validator
from typing import List, Optional

class SchoolScoreRequest(BaseModel):
    address: Optional[str] = None
    zip_code: Optional[str] = None

    @model_validator(mode='after')
    def check_at_least_one(self):
        if not self.address and not self.zip_code:
            raise ValueError("You must provide either an 'address' or a 'zip_code'.")
        return self

class SchoolItem(BaseModel):
    school_name: str
    level: Optional[str] = None
    housmart_school_score: Optional[float] = None
    s_academic: Optional[float] = None
    s_resource: Optional[float] = None
    s_equity: Optional[float] = None

class SchoolScoreResponse(BaseModel):
    search_type: str
    search_value: str
    total_schools_found: int
    schools: List[SchoolItem]
    message: Optional[str] = None