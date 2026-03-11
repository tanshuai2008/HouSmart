from app.services.school_repository import get_schools_by_zip
from app.services.geocode_service import get_zip_from_address


def get_school_scores(address: str):

    zip_code = get_zip_from_address(address)

    if not zip_code:
        return {"error": "Zip code not found"}

    zip_code = zip_code[:5]

    schools = get_schools_by_zip(zip_code)

    # fallback ZIP search
    if not schools:

        nearby_zips = [
            str(int(zip_code) + 1),
            str(int(zip_code) - 1),
            str(int(zip_code) + 2)
        ]

        for z in nearby_zips:

            schools = get_schools_by_zip(z)

            if schools:
                zip_code = z
                break

    # round scores
    for s in schools:

        if s["housmart_school_score"]:
            s["housmart_school_score"] = round(s["housmart_school_score"], 2)

        if s["s_academic"]:
            s["s_academic"] = round(s["s_academic"], 2)

        if s["s_equity"]:
            s["s_equity"] = round(s["s_equity"], 2)

    return {
        "zip_code": zip_code,
        "total_schools": len(schools),
        "schools": schools
    }