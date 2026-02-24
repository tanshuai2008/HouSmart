from app.core.supabase_client import supabase


class GeoRepository:

    @staticmethod
    def upsert_tract_income(data: dict):

        tract_payload = {
            "tract_fips": data["tract_geoid"],
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