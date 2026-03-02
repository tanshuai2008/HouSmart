# HouSmart/backend/app/services/education_repository.py
from app.core.supabase_client import supabase


class EducationRepository:

    @staticmethod
    def upsert_tract_education(data: dict):

        tract_payload = {
            "tract_geoid": data["tract_geoid"],
            "state_fips": data["state_fips"],
            "county_fips": data["county_code"],
            "education_bachelor_pct": data["bachelor_percentage"]
        }

        response = (
            supabase
            .table("geo_tract_metrics")
            .upsert(tract_payload)
            .execute()
        )

        return response.data