import logging
from datetime import datetime, timezone
from typing import Dict
from app.data.poi_categories import POI_CATEGORIES
from app.services.google_places_service import GooglePlacesService
from app.services.poi_repository import POIRepository

logger = logging.getLogger(__name__)


class POIService:

    def __init__(self):
        self.repository = POIRepository()
        self.google_fetch_service = GooglePlacesService()

    def _calculate_score(self, count: int, threshold: int, weight: float) -> float:
        """
        Computes a normalized score for a category based on POI count, threshold, and weight.
        """

        ratio = min(count / threshold, 1.0)
        return round(ratio * weight, 4)

    def compute_all_categories(self, latitude: float, longitude: float) -> Dict:
        """
        Fetches POIs if not cached, counts category occurrences within defined radii, and returns weighted scores with a composite score.
        """
        
        results = {}
        total_score = 0.0
    
        max_radius = 2000
    
        existing = self.repository.count_pois(
            latitude,
            longitude,
            max_radius,
            "amenity",
            ["school"]
        )
    
        cache_hit = existing > 0
        source = "osm_poi_cache"
        api_used = "cache"

        if existing == 0:
            source = "google_places"
            api_used = "google_places"
            rows_to_insert = []
            try:
                rows_to_insert = self.google_fetch_service.fetch_all_pois(
                    latitude,
                    longitude,
                    max_radius
                )
                logger.info("Fetched POIs from Google Places: %s", len(rows_to_insert))
            except Exception as exc:
                logger.warning("Google Places fetch failed: %s", exc)

            self.repository.bulk_insert_pois(rows_to_insert)
            cache_hit = False
    
        for name, category in POI_CATEGORIES.items():
        
            count = self.repository.count_pois(
                latitude,
                longitude,
                category.radius_meters,
                category.osm_key,
                category.osm_values
            )
    
            score = self._calculate_score(
                count,
                category.threshold,
                category.weight
            )
    
            results[name] = {
                "count": count,
                "score": score
            }
    
            total_score += score
    
        results["composite_score"] = round(total_score, 4)
        latest_ts = self.repository.latest_poi_timestamp(latitude, longitude, max_radius)
        results["_meta"] = {
            "source": source,
            "api_used": api_used,
            "cache_hit": cache_hit,
            "data_updated_at": latest_ts or datetime.now(timezone.utc).isoformat(),
        }
    
        return results
