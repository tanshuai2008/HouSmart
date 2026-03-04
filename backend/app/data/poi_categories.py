from typing import Dict, List


class POICategory:
    def __init__(self, osm_key: str, osm_values: List[str],
                 radius_meters: int, threshold: int, weight: float):

        self.osm_key = osm_key
        self.osm_values = osm_values
        self.radius_meters = radius_meters
        self.threshold = threshold
        self.weight = weight


POI_CATEGORIES: Dict[str, POICategory] = {
    """
    Defines the POI categories used for location intelligence scoring with their OSM tags, radii, thresholds, and weights.
    """

    "education": POICategory(
        osm_key="amenity",
        osm_values=["school", "college", "university", "library"],
        radius_meters=2400,
        threshold=5,
        weight=0.2
    ),

    "retail": POICategory(
        osm_key="shop",
        osm_values=["supermarket", "mall"],
        radius_meters=1600,
        threshold=8,
        weight=0.2
    ),

    "healthcare": POICategory(
        osm_key="amenity",
        osm_values=["hospital", "clinic", "dentist"],
        radius_meters=3200,
        threshold=4,
        weight=0.2
    ),

    "lifestyle": POICategory(
        osm_key="leisure",
        osm_values=["park"],
        radius_meters=1600,
        threshold=10,
        weight=0.2
    ),

    "transit": POICategory(
        osm_key="railway",
        osm_values=["station"],
        radius_meters=1200,
        threshold=6,
        weight=0.2
    ),
}