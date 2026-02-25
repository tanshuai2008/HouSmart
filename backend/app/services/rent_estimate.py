from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Any, TypedDict
import os
import requests
from dotenv import load_dotenv

from app.services.rent_cache import (
    RentCacheError,
    build_request_hash,
    get_cache_ttl_seconds,
    get_cached_estimate,
    upsert_cached_estimate,
)
from app.services.supabase_client import get_supabase
from app.utils.logging import get_logger
from supabase import Client

load_dotenv()
api_key = os.getenv("RENT_ESTIMATE_API_KEY")
ZYLA_ENDPOINT = "https://zylalabs.com/api/2827/us+rental+estimation+api/2939/get+estimation"
logger = get_logger(__name__)


class RentEstimateResult(TypedDict):
    rent: float
    rent_range_low: Optional[float]
    rent_range_high: Optional[float]
    currency: str
    address: str


class RentEstimateServiceError(Exception):
    """Raised when the Zyla request fails or returns invalid data."""


def _build_result(address: str, payload: dict[str, Any]) -> RentEstimateResult:
    rent_value = payload.get("rent")
    if rent_value is None:
        raise RentEstimateServiceError("Zyla response does not include rent")
    try:
        rent = float(rent_value)
    except (TypeError, ValueError) as exc:
        raise RentEstimateServiceError("Zyla response contained a non-numeric rent value") from exc

    rent_range_low = payload.get("rentRangeLow")
    if rent_range_low is not None:
        try:
            rent_range_low = float(rent_range_low)
        except (TypeError, ValueError) as exc:
            raise RentEstimateServiceError("Zyla response contained a non-numeric range value") from exc

    rent_range_high = payload.get("rentRangeHigh")
    if rent_range_high is not None:
        try:
            rent_range_high = float(rent_range_high)
        except (TypeError, ValueError) as exc:
            raise RentEstimateServiceError("Zyla response contained a non-numeric range value") from exc

    return {
        "rent": rent,
        "rent_range_low": rent_range_low,
        "rent_range_high": rent_range_high,
        "currency": str(payload.get("currency", "USD")),
        "address": address,
    }


def _validate_request_inputs(
    *,
    address: str,
    property_type: str,
    bedrooms: int,
    bathrooms: int,
    square_footage: int,
) -> dict[str, Any]:
    missing_fields: list[str] = []
    normalized_address = (address or "").strip()
    if not normalized_address:
        missing_fields.append("address")

    normalized_property_type = (property_type or "").strip()
    if not normalized_property_type:
        missing_fields.append("property_type")

    if bedrooms is None:
        missing_fields.append("bedrooms")

    if bathrooms is None:
        missing_fields.append("bathrooms")

    if square_footage is None:
        missing_fields.append("square_footage")

    if missing_fields:
        missing = ", ".join(missing_fields)
        raise ValueError(f"Missing required rent estimate parameters: {missing}")

    try:
        bedrooms_value = int(bedrooms)
    except (TypeError, ValueError) as exc:
        raise ValueError("bedrooms must be an integer") from exc

    try:
        bathrooms_value = float(bathrooms)
    except (TypeError, ValueError) as exc:
        raise ValueError("bathrooms must be numeric") from exc

    try:
        square_footage_value = int(square_footage)
    except (TypeError, ValueError) as exc:
        raise ValueError("square_footage must be an integer") from exc

    return {
        "address": normalized_address,
        "property_type": normalized_property_type,
        "bedrooms": bedrooms_value,
        "bathrooms": bathrooms_value,
        "square_footage": square_footage_value,
    }


def _try_get_cached_result(
    *,
    address: str,
    cache_key: str,
    ttl_seconds: int,
    supabase_client: Optional[Client],
) -> Optional[RentEstimateResult]:
    try:
        cached_payload = get_cached_estimate(
            cache_key,
            ttl_seconds,
            supabase_client=supabase_client,
        )
    except RentCacheError as exc:
        logger.warning("Rent estimate cache lookup failed: %s", exc)
        return None

    if not cached_payload:
        logger.debug("Rent estimate cache miss for hash %s", cache_key)
        return None

    try:
        cached_result = _build_result(address, cached_payload)
    except RentEstimateServiceError as exc:
        logger.warning("Invalid cached rent payload for hash %s: %s", cache_key, exc)
        return None

    logger.debug("Rent estimate cache hit for hash %s", cache_key)
    return cached_result


def _call_zyla_api(
    *,
    http: requests.Session,
    request_payload: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    if not api_key:
        raise ValueError("api_key is required")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    query: dict[str, object] = {
        "address": request_payload["address"],
        "propertyType": request_payload["property_type"],
        "bedrooms": request_payload["bedrooms"],
        "bathrroms": request_payload["bathrooms"],
        "squareFootage": request_payload["square_footage"],
    }

    try:
        response = http.get(
            ZYLA_ENDPOINT,
            headers=headers,
            params=query,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RentEstimateServiceError(f"Request to Zyla failed: {exc}") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise RentEstimateServiceError("Zyla returned a non-JSON response") from exc


def _persist_cache_entry(
    *,
    cache_key: str,
    cache_request_payload: dict[str, Any],
    payload: dict[str, Any],
    supabase_client: Optional[Client],
) -> None:
    try:
        upsert_cached_estimate(
            cache_key,
            cache_request_payload,
            payload,
            supabase_client=supabase_client,
        )
    except RentCacheError as exc:
        logger.warning("Rent estimate cache upsert failed: %s", exc)


def fetch_rent_estimate(
    *,
    address: str,
    property_type: str,
    bedrooms: int,
    bathrooms: int,
    square_footage: int,
    session: Optional[requests.Session] = None,
    timeout: float = 15.0,
    supabase_client: Optional[Client] = None,
) -> RentEstimateResult:
    if not api_key:
        raise ValueError("api_key is required")

    cache_request_payload = _validate_request_inputs(
        address=address,
        property_type=property_type,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        square_footage=square_footage,
    )

    http = session or requests.Session()
    cache_key = build_request_hash(cache_request_payload)
    ttl_seconds = get_cache_ttl_seconds()

    cached_result = _try_get_cached_result(
        address=cache_request_payload["address"],
        cache_key=cache_key,
        ttl_seconds=ttl_seconds,
        supabase_client=supabase_client,
    )
    if cached_result:
        return cached_result

    payload = _call_zyla_api(
        http=http,
        request_payload=cache_request_payload,
        timeout=timeout,
    )
    result = _build_result(cache_request_payload["address"], payload)
    _persist_cache_entry(
        cache_key=cache_key,
        cache_request_payload=cache_request_payload,
        payload=payload,
        supabase_client=supabase_client,
    )
    return result


def main() -> None:

    try:
        supabase_client = get_supabase()
    except Exception as exc:
        print(f"Failed to initialize Supabase client: {exc}")
        return

    try:
        result = fetch_rent_estimate(
            address="1300 N St Nw, Washington, DC 20005",
            property_type="single family",
            bedrooms=0,
            bathrooms=1,
            square_footage=655,
            supabase_client=supabase_client,
        )
    except RentEstimateServiceError as exc:
        print(f"Failed to fetch rent estimate: {exc}")
        return
    print(result)
    print("Rent estimate fetched successfully:")
    print(f"  Address: {result['address']}")
    print(f"  Rent: ${result['rent']:,.2f}")
    if result["rent_range_low"] is not None:
        print(f"  Range Low: ${result['rent_range_low']:,.2f}")
    if result["rent_range_high"] is not None:
        print(f"  Range High: ${result['rent_range_high']:,.2f}")
    print(f"  Currency: {result['currency']}")


if __name__ == "__main__":
    main()