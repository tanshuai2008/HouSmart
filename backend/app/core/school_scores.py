# import os
# from supabase import create_client, Client
# from dotenv import load_dotenv

# load_dotenv()

# supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

# class SchoolScoreServiceError(Exception):
#     """Custom exception for school score database errors."""
#     pass

# def fetch_school_scores(address: str) -> dict:
#     try:
#         db_resp = supabase.rpc(
#             "get_property_school_scores",
#             {"search_address": address}
#         ).execute()

#         schools = db_resp.data

#         if not schools:
#             return {
#                 "address": address,
#                 "message": "No schools found. Make sure the address exactly matches.",
#                 "total_schools_found": 0,
#                 "schools": []
#             }

#         return {
#             "address": address,
#             "total_schools_found": len(schools),
#             "schools": schools
#         }
#     except Exception as e:
#         raise SchoolScoreServiceError(f"Supabase RPC failed: {str(e)}") from e

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

class SchoolScoreServiceError(Exception):
    pass

def fetch_school_scores(address: str = None, zip_code: str = None) -> dict:
    try:
        schools = []
        search_type = ""
        search_value = ""

        # PATH A: They sent a ZIP code (Fast 1-Table Lookup)
        if zip_code:
            db_resp = supabase.table("school_master") \
                .select("school_name, level, housmart_school_score, s_academic, s_resource, s_equity") \
                .eq("zip_code", zip_code) \
                .order("housmart_school_score", desc=True) \
                .execute()
            
            schools = db_resp.data
            search_type = "zip_code"
            search_value = zip_code

        # PATH B: They sent an Address (Accurate 3-Table Join)
        elif address:
            db_resp = supabase.rpc(
                "get_property_school_scores",
                {"search_address": address}
            ).execute()
            
            schools = db_resp.data
            search_type = "address"
            search_value = address

        if not schools:
            return {
                "search_type": search_type,
                "search_value": search_value,
                "message": f"No schools found for {search_type}: {search_value}",
                "total_schools_found": 0,
                "schools": []
            }

        return {
            "search_type": search_type,
            "search_value": search_value,
            "total_schools_found": len(schools),
            "schools": schools
        }
    except Exception as e:
        raise SchoolScoreServiceError(f"Database query failed: {str(e)}") from e