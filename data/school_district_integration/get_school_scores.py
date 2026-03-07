from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()
supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

class AddressRequest(BaseModel):
    address: str

@router.post("/property/school-scores")
async def get_school_scores(req: AddressRequest):
    try:
        # Pass the exact address string from the request to your new RPC
        db_resp = supabase.rpc(
            "get_property_school_scores",
            {"search_address": req.address}
        ).execute()

        schools = db_resp.data

        if not schools:
            return {
                "address": req.address,
                "message": "No schools found. Make sure the address exactly matches the 'formatted_address' in your database.",
                "schools": []
            }

        return {
            "address": req.address,
            "total_schools_found": len(schools),
            "schools": schools
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")