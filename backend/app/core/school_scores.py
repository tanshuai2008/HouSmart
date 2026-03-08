import os
import re
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

class SchoolScoreServiceError(Exception):
    pass


def extract_zip(address: str):
    match = re.search(r"\b\d{5}\b", address or "")
    return match.group(0) if match else None


def fetch_school_scores(address=None, zip_code=None):

    try:

        schools = []

        # ZIP SEARCH (fastest)
        if zip_code:

            res = supabase.table("school_master") \
                .select("school_name,level,housmart_school_score,s_academic,s_resource,s_equity") \
                .eq("zip_code", zip_code) \
                .order("housmart_school_score", desc=True) \
                .execute()

            schools = res.data

            if schools:
                return {
                    "search_type": "zip_code",
                    "search_value": zip_code,
                    "total_schools_found": len(schools),
                    "schools": schools
                }

        # ADDRESS RPC
        if address:

            res = supabase.rpc(
                "get_property_school_scores",
                {"search_address": address}
            ).execute()

            schools = res.data

            if schools:
                return {
                    "search_type": "address",
                    "search_value": address,
                    "total_schools_found": len(schools),
                    "schools": schools
                }

        # ZIP FALLBACK
        if address:

            zip_guess = extract_zip(address)

            if zip_guess:

                res = supabase.table("school_master") \
                    .select("school_name,level,housmart_school_score,s_academic,s_resource,s_equity") \
                    .eq("zip_code", zip_guess) \
                    .order("housmart_school_score", desc=True) \
                    .execute()

                schools = res.data

                if schools:
                    return {
                        "search_type": "zip_fallback",
                        "search_value": zip_guess,
                        "total_schools_found": len(schools),
                        "schools": schools
                    }

        return {
            "search_type": "none",
            "search_value": address or zip_code,
            "total_schools_found": 0,
            "schools": [],
            "message": "No schools found"
        }

    except Exception as e:
        raise SchoolScoreServiceError(str(e))