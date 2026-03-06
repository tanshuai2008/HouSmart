from fastapi import APIRouter, HTTPException
from app.services.poi_service import POIService
from app.api.schemas.location import AddressRequest
from app.services.census_service import CensusService

router = APIRouter(prefix="/api", tags=["Amenity Score"])

poi_service = POIService()


@router.post("/amenity_score", summary="Compute category-wise amenity accessibility scores for an address")
def amenity_score_by_address(payload: AddressRequest):
    """
    Computes amenity accessibility scores by category for an input address.

    Input:
    - JSON body (AddressRequest):
      - address: full street address string.

    Output:
    - JSON containing:
      - status: "success"
      - data: category-wise amenity metrics returned by POIService (for example proximity/count/score signals).

    How it is calculated:
    - Resolves the address to latitude/longitude via CensusService geocoding.
    - Calls POIService.compute_all_categories on the resolved coordinates.
    - Aggregates per-category amenity signals into a single response payload.

    What can be extracted:
    - Walkability/lifestyle context by amenity type to compare neighborhoods and rank properties.
    """
    location_data = CensusService.get_location_data(payload.address)

    if not location_data:
        raise HTTPException(status_code=404, detail="Address not found")

    result = poi_service.compute_all_categories(
        location_data["latitude"],
        location_data["longitude"]
    )

    return {
        "status": "success",
        "data": result
    }
