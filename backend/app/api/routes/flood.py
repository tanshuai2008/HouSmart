from fastapi import APIRouter, HTTPException
from app.api.schemas.flood import (
    AddressFloodRequest,
    AddressFloodResponse,
)
from app.services.analysis_repository import AnalysisRepository
from app.services.flood_service import (
    HIGH_RISK_ZONES,
    MODERATE_RISK_ZONES,
    get_flood_zone,
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
        result = None
        if request.user_id and request.property_id:
            property_row = AnalysisRepository.get_user_property_by_id(
                user_id=request.user_id,
                property_id=request.property_id,
            )
            if property_row:
                lat = property_row.get("latitude")
                lng = property_row.get("longitude")
                if lat is not None and lng is not None:
                    flood_data = await get_flood_zone(float(lat), float(lng))
                    fld_zone = flood_data["fld_zone"]
                    result = {
                        "address": request.address or property_row.get("address") or "",
                        "property_lat": float(lat),
                        "property_lng": float(lng),
                        "fld_zone": fld_zone,
                        "risk_label": flood_data["risk_label"],
                        "flood_score": flood_data["flood_score"],
                        "in_flood_zone": fld_zone in HIGH_RISK_ZONES,
                        "in_moderate_zone": fld_zone in MODERATE_RISK_ZONES,
                        "flood_data_unknown": flood_data["flood_data_unknown"],
                        "source": flood_data["source"],
                    }

        if result is None:
            if not request.address:
                raise ValueError(
                    "address is required when user_id/property_id is missing or has no stored coordinates"
                )
            result = await get_flood_zone_by_address(address=request.address)

        return {"status": "success", "data": AddressFloodResponse(**result)}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

