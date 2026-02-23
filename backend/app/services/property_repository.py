from app.core.supabase_client import supabase

class PropertyRepository:

    @staticmethod
    def create_property(data: dict):

        data["location"] = f"POINT({data['longitude']} {data['latitude']})"

        response = supabase.table("properties").insert(data).execute()

        if response.data:
            return response.data[0]

        return None