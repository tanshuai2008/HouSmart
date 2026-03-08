from fastapi import APIRouter, HTTPException
from app.api.schemas.transit import (
    AddressTransitRequest,
)
from app.services.transit_service import (
    get_transit_score_by_address,
)

router = APIRouter(prefix="/api", tags=["Transit"])


@router.post(
    "/transit_score",
    summary="Compute transit accessibility score and nearest-stop metrics for an address"
)
async def get_transit_score_by_address_endpoint(request: AddressTransitRequest):
    """
    Calculates an address-level transit score using nearby public transit stop density and distance.

    Input:
    - JSON body (AddressTransitRequest):
      - address: full street address string
      - radius_meters: optional search radius for nearby stops (service defaults if omitted).

    Output:
    - JSON with `status` and `data` containing transit score attributes.
    - Typical fields include overall transit score (0-100), nearest stop distance, and supporting counts/metadata.

    How it is calculated:
    - Geocodes address to latitude/longitude.
    - Finds transit stops within configured radius (Google Places transit search).
    - Scores accessibility based on proximity and stop availability; persists result to transit_scores.

    What can be extracted:
    - Commuter convenience signal, walk-to-transit friendliness, and comparative accessibility between properties.
    """
    try:
        result = await get_transit_score_by_address(
            address=request.address,
            radius_meters=request.radius_meters,
        )
        return {"status": "success", "data": result}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
