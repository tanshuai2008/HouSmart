# HouSmart/backend/app/api/schemas/property.py
from pydantic import BaseModel

class PropertyCreateRequest(BaseModel):
    address: str
