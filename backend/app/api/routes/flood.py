from fastapi import APIRouter, HTTPException
from app.api.schemas.flood import (
    AddressFloodRequest,
    AddressFloodResponse,
)
from app.services.flood_service import (
    get_flood_zone_by_address,
)

router = APIRouter(prefix="/api", tags=["Flood Risk"])


@router.post(
    "/flood_risk_score",
    summary="Return FEMA flood risk classification and score for a property address"
)
async def check_flood_by_address(request: AddressFloodRequest):
    """
    Resolves an address to coordinates and returns FEMA flood-zone risk details plus normalized risk score.

    Input:
    - JSON body (AddressFloodRequest):
      - address: full street address string.

    Output:
    - JSON payload in `data` (AddressFloodResponse) including flood zone metadata and score fields.
    - Typical fields include zone classification, risk score, and lookup coordinates/source identifiers.

    How it is calculated:
    - Geocodes address (OSM Nominatim flow in flood service layer).
    - Queries FEMA NFHL data for flood-zone intersection at resolved coordinates.
    - Converts FEMA zone into application risk interpretation/score and persists lookup result.

    What can be extracted:
    - Whether the property is in a high/moderate/low flood-risk area, and structured evidence for underwriting.
    """
    try:
        result = await get_flood_zone_by_address(address=request.address)
        return {"status": "success", "data": AddressFloodResponse(**result)}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

