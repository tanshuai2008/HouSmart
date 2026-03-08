import re

from app.services.supabase_client import get_supabase


class SchoolScoreServiceError(Exception):
    pass


def fetch_school_scores(address: str) -> dict:
    normalized_address = address.strip()
    if not normalized_address:
        raise ValueError("Address is required")

    try:
        supabase = get_supabase()
        db_resp = supabase.rpc(
            "get_property_school_scores",
            {"search_address": normalized_address},
        ).execute()

        schools = db_resp.data or []
        search_type = "address"
        search_value = normalized_address

        if not schools:
            zip_match = re.search(r"\b(\d{5})(?:-\d{4})?\b", normalized_address)
            if zip_match:
                zip_code = zip_match.group(1)
                zip_resp = (
                    supabase.table("school_master")
                    .select("school_name, level, housmart_school_score, s_academic, s_resource, s_equity")
                    .eq("zip_code", zip_code)
                    .order("housmart_school_score", desc=True)
                    .execute()
                )
                schools = zip_resp.data or []
                search_type = "zip_code"
                search_value = zip_code

        if not schools:
            return {
                "search_type": search_type,
                "search_value": search_value,
                "message": f"No schools found for {search_type}: {search_value}",
                "total_schools_found": 0,
                "schools": [],
            }

        return {
            "search_type": search_type,
            "search_value": search_value,
            "total_schools_found": len(schools),
            "schools": schools,
        }
    except ValueError:
        raise
    except Exception as exc:
        raise SchoolScoreServiceError(f"Database query failed: {exc}") from exc
