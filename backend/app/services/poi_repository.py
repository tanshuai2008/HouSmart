from app.core.supabase_client import supabase


class POIRepository:

    def __init__(self):
        self.db = supabase

    def count_pois(self, latitude, longitude, radius_meters, osm_key, osm_values):

        response = self.db.rpc(
            "count_pois",
            {
                "lat": latitude,
                "lng": longitude,
                "radius_meters": radius_meters,
                "p_osm_key": osm_key,
                "p_osm_values": osm_values
            }
        ).execute()

        return response.data if response.data else 0

    def insert_poi(self, osm_key, osm_value, lat, lon):

        self.db.table("osm_poi_cache").insert({
            "osm_key": osm_key,
            "osm_value": osm_value,
            "latitude": lat,
            "longitude": lon,
            "location": f"SRID=4326;POINT({lon} {lat})"
        }).execute()

    def bulk_insert_pois(self, rows):

        if not rows:
            return

        self.db.table("osm_poi_cache").insert(rows).execute()