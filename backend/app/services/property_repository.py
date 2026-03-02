# HouSmart/backend/app/services/property_repository.py
from app.core.supabase_client import supabase


class PropertyRepository:

    @staticmethod
    def create_property(data: dict):

        property_payload = {
            "formatted_address": data["formatted_address"],
            "street": data["street"],
            "city": data["city"],
            "state": data["state"],
            "zip_code": data["zip_code"],
            "county_fips": data["county_fips"],
            "tract_fips": data["tract_geoid"],
            "latitude": data["latitude"],
            "longitude": data["longitude"],
            "location": f"POINT({data['longitude']} {data['latitude']})"
        }

        response = supabase.table("properties").insert(property_payload).execute()

        if response.data:
            return response.data[0]

        return None