from app.core.supabase_client import supabase


def get_property_zip(address: str):

    response = (
        supabase
        .table("properties")
        .select("zip_code")
        .eq("formatted_address", address)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]["zip_code"]


def get_schools_by_zip(zip_code: str, limit: int = 10):

    response = (
        supabase
        .table("school_master")
        .select(
            "school_name, district_name, academic_score, academic_score_norm, zip_code"
        )
        .eq("zip_code", zip_code)
        .not_.is_("academic_score", None)
        .order("academic_score", desc=True)
        .limit(limit)
        .execute()
    )

    if not response.data:
        return []

    return response.data