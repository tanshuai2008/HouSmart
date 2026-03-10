from app.services.school_repository import get_schools_by_zip
from app.services.geocode_service import get_zip_from_address


def get_school_scores(address: str):

    zip_code = get_zip_from_address(address)

    if not zip_code:
        return {"error": "Zip code not found"}

    zip_code = zip_code[:5]

    schools = get_schools_by_zip(zip_code)

    # fallback search
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

    return {
        "zip_code": zip_code,
        "schools": schools
    }