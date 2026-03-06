from app.services.poi_service import POIService
from app.services.property_repository import PropertyRepository


class AmenityScoreService:

    def __init__(self):
        self.poi_service = POIService()
        self.property_repo = PropertyRepository()

    def run_location_stage(self, property_id):
        """
        Retrieves a property by ID and calculates location intelligence scores based on nearby POIs.
        """

        property = self.property_repo.get_by_id(property_id)

        if not property:
            return {"error": "Property not found"}

        poi_scores = self.poi_service.compute_all_categories(
            property["latitude"],
            property["longitude"]
        )

        return poi_scores
