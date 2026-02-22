from pydantic import BaseModel

class PropertyCreateRequest(BaseModel):
    address: str
