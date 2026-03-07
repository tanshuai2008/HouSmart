import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

class SchoolScoreServiceError(Exception):
    """Custom exception for school score database errors."""
    pass

def fetch_school_scores(address: str) -> dict:
    try:
        db_resp = supabase.rpc(
            "get_property_school_scores",
            {"search_address": address}
        ).execute()

        schools = db_resp.data

        if not schools:
            return {
                "address": address,
                "message": "No schools found. Make sure the address exactly matches.",
                "total_schools_found": 0,
                "schools": []
            }

        return {
            "address": address,
            "total_schools_found": len(schools),
            "schools": schools
        }
    except Exception as e:
        raise SchoolScoreServiceError(f"Supabase RPC failed: {str(e)}") from e