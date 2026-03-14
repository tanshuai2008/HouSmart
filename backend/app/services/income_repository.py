# HouSmart/backend/app/services/income_repository.py
from app.core.supabase_client import supabase


class IncomeRepository:

    @staticmethod
    def upsert_tract_income(data: dict):

        tract_payload = {
            "tract_geoid": data["tract_geoid"],
            "state_fips": data["state_fips"],
            "county_fips": data["county_code"],
            "median_income": data["median_income"]
        }

        response = (
            supabase
            .table("geo_tract_metrics")
            .upsert(tract_payload)
            .execute()
        )

        return response.data