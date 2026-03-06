from fastapi import APIRouter, HTTPException, status

from app.api.schemas.location import AddressRequest
from app.services.median_house_price import get_median_house_price

router = APIRouter(prefix="/api", tags=["median-house-price"])


@router.post(
    "/median_property_price",
    status_code=status.HTTP_200_OK,
    summary="Get median property price for the market of a given address",
)
def median_house_price_by_address(
    payload: AddressRequest,
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
    result = get_median_house_price(address=payload.address)
    if isinstance(result, dict) and result.get("error"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(result["error"]),
        )
    return result
