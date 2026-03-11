from datetime import date

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

from app.services.analysis_repository import AnalysisRepository
from app.services.median_house_price import get_median_house_price

router = APIRouter(prefix="/api", tags=["median-house-price"])


class MedianHousePriceRequest(BaseModel):
    address: Optional[str] = Field(default=None, min_length=5)
    user_id: Optional[str] = None
    property_id: Optional[str] = None


@router.post(
    "/median_property_price",
    status_code=status.HTTP_200_OK,
    summary="Get median property price for the market of a given address",
)
def median_house_price_by_address(
    payload: MedianHousePriceRequest,
):
    """
    Returns median property price for the market corresponding to a provided address.

    Input:
    - JSON body (AddressRequest):
      - address: full street address string.

    Output:
    - JSON from median price service, typically including median price and location context used for lookup.
    - Returns 404 when address cannot be resolved to a supported market area.

    How it is calculated:
    - Resolves address to city/state or equivalent market key.
    - Looks up median housing price data for the resolved market in `get_median_house_price`.
    - Returns normalized pricing payload.

    What can be extracted:
    - Market baseline valuation context for affordability checks and pricing comparisons.
    """
    resolved_address = (payload.address or "").strip() or None
    resolved_from_user_property = False
    if payload.user_id and payload.property_id:
        property_row = AnalysisRepository.get_user_property_by_id(
            user_id=payload.user_id,
            property_id=payload.property_id,
        )
        if property_row:
            resolved_candidate = (
                property_row.get("normalized_address")
                or property_row.get("address")
                or resolved_address
            )
            resolved_address = (resolved_candidate or "").strip() or resolved_address
            resolved_from_user_property = bool(resolved_address)

    if not resolved_address:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="address is required when user_id/property_id is missing or has no stored address",
        )

    result = get_median_house_price(address=resolved_address)
    if isinstance(result, dict) and result.get("error"):
        error_text = str(result["error"])
        # Return non-fatal payload so aggregate/orchestrated flows can continue.
        if error_text == "Address not found":
            return {
                "date": date.today().isoformat(),
                "address": resolved_address,
                "median_price": None,
                "period": None,
                "source": "Unavailable",
                "status": "not_found",
                "reason": "address_geocode_failed",
                "message": "Median price lookup could not geocode the resolved address.",
                "used_user_property": resolved_from_user_property,
            }
        if error_text.startswith("No median price data found for "):
            return {
                "date": date.today().isoformat(),
                "address": resolved_address,
                "median_price": None,
                "period": None,
                "source": "Unavailable",
                "status": "not_found",
                "reason": "market_data_not_found",
                "message": "No Redfin median price market row exists for the resolved city/state.",
                "used_user_property": resolved_from_user_property,
                "upstream_error": error_text,
            }

        detail = {
            "error_code": "MEDIAN_PRICE_LOOKUP_FAILED",
            "message": "Median property price lookup failed.",
            "resolved_address": resolved_address,
            "used_user_property": resolved_from_user_property,
            "upstream_error": error_text,
        }
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )
    return result
