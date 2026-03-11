from app.core.supabase_client import supabase


def get_schools_by_zip(zip_code: str):

    # find district for this zip
    district = (
        supabase
        .table("school_master")
        .select("district_id")
        .eq("zip_code", zip_code)
        .limit(1)
        .execute()
    )

    if not district.data:
        return []

    district_id = district.data[0]["district_id"]

    # get all schools in district
    schools = (
        supabase
        .table("school_master")
        .select(
            "school_name, level, housmart_school_score, s_academic, s_resource, s_equity"
        )
        .eq("district_id", district_id)
        .order("housmart_school_score", desc=True)
        .limit(10)
        .execute()
    )

    return schools.data