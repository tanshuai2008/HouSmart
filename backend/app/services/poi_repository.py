from app.core.supabase_client import supabase
from postgrest.exceptions import APIError
import math
from app.utils.geo import haversine_meters


class POIRepository:

    def __init__(self):
        self.db = supabase

    def count_pois(self, latitude, longitude, radius_meters, osm_key, osm_values):
        """
        Calls a PostGIS function to count POIs matching a key and values within a radius of the given location.
        """
        lat = float(latitude)
        lng = float(longitude)
        radius = float(radius_meters)
        payload = {"lat": lat, "lng": lng, "radius_meters": radius, "p_osm_key": osm_key, "p_osm_values": osm_values}
        try:
            response = self.db.rpc("count_pois", payload).execute()
        except APIError as exc:
            # Fallback when PostgREST cannot resolve overloaded RPC signatures.
            if getattr(exc, "code", None) == "PGRST203":
                return self._count_pois_from_cache(lat, lng, radius, osm_key, osm_values)
            else:
                raise

        return response.data if response.data else 0

    def _count_pois_from_cache(self, latitude, longitude, radius_meters, osm_key, osm_values):
        lat_delta = radius_meters / 111320.0
        cos_lat = math.cos(math.radians(latitude))
        lng_delta = radius_meters / (111320.0 * max(abs(cos_lat), 1e-8))

        response = (
            self.db.table("osm_poi_cache")
            .select("latitude,longitude")
            .eq("osm_key", osm_key)
            .in_("osm_value", osm_values)
            .gte("latitude", latitude - lat_delta)
            .lte("latitude", latitude + lat_delta)
            .gte("longitude", longitude - lng_delta)
            .lte("longitude", longitude + lng_delta)
            .execute()
        )

        rows = response.data or []
        return sum(
            1
            for row in rows
            if haversine_meters(latitude, longitude, row["latitude"], row["longitude"]) <= radius_meters
        )

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
