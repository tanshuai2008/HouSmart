from app.core.supabase_client import supabase


class POIRepository:

    def __init__(self):
        self.db = supabase

    def count_pois(self, latitude, longitude, radius_meters, osm_key, osm_values):
        """
        Calls a PostGIS function to count POIs matching a key and values within a radius of the given location.
        """

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
        """
        Inserts a single POI record into the osm_poi_cache table with geographic coordinates.
        """

        self.db.table("osm_poi_cache").insert({
            "osm_key": osm_key,
            "osm_value": osm_value,
            "latitude": lat,
            "longitude": lon,
            "location": f"SRID=4326;POINT({lon} {lat})"
        }).execute()

    def bulk_insert_pois(self, rows):
        """
        Inserts multiple POI records into the cache table in a single database operation.
        """

        if not rows:
            return

        self.db.table("osm_poi_cache").insert(rows).execute()

    def latest_poi_timestamp(self, latitude, longitude, radius_meters):
        """
        Returns latest created_at for cached POIs within the given radius.
        """
        try:
            response = self.db.rpc(
                "latest_poi_timestamp",
                {
                    "lat": latitude,
                    "lng": longitude,
                    "radius_meters": radius_meters,
                }
            ).execute()
            return response.data
        except Exception:
            return None
