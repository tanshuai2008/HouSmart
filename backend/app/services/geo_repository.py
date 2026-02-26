from app.core.supabase_client import supabase


class GeoRepository:

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


    @staticmethod
    def upsert_tract_metrics(data: dict):

        tract_payload = {
            "tract_geoid": data["tract_geoid"],
            "state_fips": data["state_fips"],
            "county_fips": data["county_fips"],
            "median_income": data["median_income"],
            "education_bachelor_pct": data["education_bachelor_pct"]
        }

        response = (
            supabase
            .table("geo_tract_metrics")
            .upsert(tract_payload)
            .execute()
        )

        return response.data