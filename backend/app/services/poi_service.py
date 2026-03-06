from typing import Dict
from app.data.poi_categories import POI_CATEGORIES
from app.services.poi_repository import POIRepository
from app.services.osm_fetch_service import OSMFetchService


class POIService:

    def __init__(self):
        self.repository = POIRepository()
        self.fetch_service = OSMFetchService()

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
    
        if existing == 0:
        
            pois = self.fetch_service.fetch_all_pois(
                latitude,
                longitude,
                max_radius
            )
    
            print("Fetched POIs:", len(pois))
    
            rows_to_insert = []
    
            for poi in pois:
            
                if "tags" not in poi:
                    continue
                
                for key in ["amenity", "shop", "leisure", "railway"]:
                
                    if key in poi["tags"]:
                    
                        rows_to_insert.append({
                            "osm_key": key,
                            "osm_value": poi["tags"][key],
                            "latitude": poi["lat"],
                            "longitude": poi["lon"],
                            "location": f"SRID=4326;POINT({poi['lon']} {poi['lat']})"
                        })
    
            self.repository.bulk_insert_pois(rows_to_insert)
    
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
    
        return results