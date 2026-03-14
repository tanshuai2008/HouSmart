from app.core.supabase_client import supabase


def get_schools_by_zip(zip_code: str):

    response = (
        supabase
        .table("school_master")
        .select("school_name, district_name, academic_score_norm, zip_code")
        .eq("zip_code", zip_code)
        .not_.is_("academic_score_norm", "null")
        .order("academic_score_norm", desc=True)
        .limit(10)
        .execute()
    )

    if not response.data:
        return []

    return response.data