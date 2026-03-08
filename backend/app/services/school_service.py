from app.services.school_repository import get_property_zip, get_schools_by_zip


def get_school_scores(address: str):

    zip_code = get_property_zip(address)

    if not zip_code:
        return {"error": "Zip code not found for this property"}

    schools = get_schools_by_zip(zip_code)

    return {
        "zip_code": zip_code,
        "schools": schools
    }