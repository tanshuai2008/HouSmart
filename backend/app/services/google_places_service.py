import logging
from typing import Dict, List, Tuple

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)

GOOGLE_PLACES_NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"


class GooglePlacesService:
    """Fetch nearby POIs from Google Places and normalize into existing OSM cache schema."""

    # (osm_key, osm_value) -> list of Google place types to query
    TYPE_MAPPING: Dict[Tuple[str, str], List[str]] = {
        ("amenity", "school"): ["school"],
        ("amenity", "college"): ["university"],
        ("amenity", "university"): ["university"],
        ("amenity", "library"): ["library"],
        ("shop", "supermarket"): ["supermarket"],
        ("shop", "mall"): ["shopping_mall"],
        ("amenity", "hospital"): ["hospital"],
        ("amenity", "clinic"): ["doctor"],
        ("amenity", "dentist"): ["dentist"],
        ("leisure", "park"): ["park"],
        ("railway", "station"): ["transit_station", "train_station", "subway_station", "bus_station"],
    }

    def fetch_all_pois(self, latitude: float, longitude: float, radius_meters: int) -> List[dict]:
        if not settings.GOOGLE_MAPS_API_KEY:
            logger.warning("Google Maps API key is not configured; skipping Google Places fetch")
            return []

        seen_place_ids = set()
        normalized_rows: List[dict] = []

        for (osm_key, osm_value), place_types in self.TYPE_MAPPING.items():
            for place_type in place_types:
                params = {
                    "key": settings.GOOGLE_MAPS_API_KEY,
                    "location": f"{latitude},{longitude}",
                    "radius": radius_meters,
                    "type": place_type,
                }
                try:
                    response = requests.get(
                        GOOGLE_PLACES_NEARBY_URL,
                        params=params,
                        timeout=settings.GOOGLE_PLACES_HTTP_TIMEOUT_SECONDS,
                    )
                    response.raise_for_status()
                    payload = response.json()
                except Exception as exc:
                    logger.warning("Google Places request failed for type '%s': %s", place_type, exc)
                    continue

                status = payload.get("status")
                if status not in ("OK", "ZERO_RESULTS"):
                    logger.warning("Google Places returned status '%s' for type '%s'", status, place_type)
                    continue

                for result in payload.get("results", []):
                    place_id = result.get("place_id")
                    geometry = result.get("geometry", {})
                    location = geometry.get("location", {})
                    lat = location.get("lat")
                    lon = location.get("lng")
                    if not place_id or lat is None or lon is None:
                        continue

                    dedupe_key = (place_id, osm_key, osm_value)
                    if dedupe_key in seen_place_ids:
                        continue
                    seen_place_ids.add(dedupe_key)

                    normalized_rows.append(
                        {
                            "osm_key": osm_key,
                            "osm_value": osm_value,
                            "latitude": lat,
                            "longitude": lon,
                            "location": f"SRID=4326;POINT({lon} {lat})",
                        }
                    )

        return normalized_rows
