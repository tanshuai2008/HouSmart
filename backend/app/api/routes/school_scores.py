from fastapi import APIRouter
from pydantic import BaseModel
from app.services.school_service import get_school_scores

router = APIRouter()

class AddressRequest(BaseModel):
    address: str


@router.post("/property/school-scores")
def school_scores(body: AddressRequest):
    return get_school_scores(body.address)