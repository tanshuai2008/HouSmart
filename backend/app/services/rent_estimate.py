from __future__ import annotations
from typing import Optional, Any, TypedDict
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
api_key = os.getenv("RENT_ESTIMATE_API_KEY_RentCast") or os.getenv("RENT_ESTIMATE_API_KEY")
RENTCAST_ENDPOINT = "https://api.rentcast.io/v1/avm/rent/long-term"

PROPERTY_TYPE_CANONICAL = {
    "house": "House",
    "singlefamily": "House",
    "singlefamilyhome": "House",
    "detached": "House",
    "condo": "Condo",
    "condominium": "Condo",
    "condominiums": "Condo",
    "apartment": "Apartment",
    "apt": "Apartment",
    "apartments": "Apartment",
    "townhouse": "Townhouse",
    "townhome": "Townhouse",
    "rowhouse": "Townhouse",
    "rowhome": "Townhouse",
    "manufactured": "Manufactured",
    "mobilehome": "Manufactured",
    "mobile": "Manufactured",
    "factorybuilt": "Manufactured",
    "prefab": "Manufactured",
    "multifamily": "Multi-Family",
    "multiunit": "Multi-Family",
    "duplex": "Multi-Family",
    "triplex": "Multi-Family",
    "fourplex": "Multi-Family",
    "quadplex": "Multi-Family",
    "land": "Land",
    "lot": "Land",
    "vacantland": "Land",
    "parcel": "Land",
}
PROPERTY_TYPE_LIST = ", ".join(
    ["House", "Apartment", "Condo", "Townhouse", "Manufactured", "Multi-Family", "Land"]
)

logger = get_logger(__name__)


class RentEstimateResult(TypedDict):
    rent: float
    rent_range_low: Optional[float]
    rent_range_high: Optional[float]
    currency: str
    address: str
    subject_property: dict[str, Any]
    comparables: list[dict[str, Any]]


class RentEstimateServiceError(Exception):
    """Raised when the rentcast request fails or returns invalid data."""


def _normalize_property_type(propertyType: Optional[str]) -> Optional[str]:
    if propertyType is None:
        return None
    normalized = propertyType.strip()
    if not normalized:
        return None
    key = "".join(ch for ch in normalized.lower() if ch.isalnum())
    if not key:
        return None
    canonical = PROPERTY_TYPE_CANONICAL.get(key)
    if not canonical:
        raise ValueError(f"propertyType must be one of: {PROPERTY_TYPE_LIST}")
    return canonical


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
        rent_value = cached_payload.get("rent")
        if rent_value is None:
            raise RentEstimateServiceError("RentCast response does not include rent")
        rent = float(rent_value)

        rent_range_low_value = cached_payload.get("rentRangeLow")
        rent_range_low = float(rent_range_low_value) if rent_range_low_value is not None else None
        rent_range_high_value = cached_payload.get("rentRangeHigh")
        rent_range_high = float(rent_range_high_value) if rent_range_high_value is not None else None

        cached_result: RentEstimateResult = {
            "rent": rent,
            "rent_range_low": rent_range_low,
            "rent_range_high": rent_range_high,
            "currency": str(cached_payload.get("currency", "USD")),
            "address": address,
            "subject_property": cached_payload.get("subjectProperty", {}) or {},
            "comparables": cached_payload.get("comparables", []) or [],
        }
    except RentEstimateServiceError as exc:
        logger.warning("Invalid cached rent payload for hash %s: %s", cache_key, exc)
        return None
    except (TypeError, ValueError) as exc:
        logger.warning("Invalid cached rent payload for hash %s: %s", cache_key, exc)
        return None

    logger.debug("Rent estimate cache hit for hash %s", cache_key)
    return cached_result


def _call_rentcast_api(
    *,
    http: requests.Session,
    request_payload: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    if not api_key:
        raise ValueError("api_key is required")

    headers = {
        "X-Api-Key": api_key,
    }

    query: dict[str, object] = {
        "address": request_payload["address"],
    }
    if "city" in request_payload:
        query["city"] = request_payload["city"]
    if "state" in request_payload:
        query["state"] = request_payload["state"]
    if "propertyType" in request_payload:
        query["propertyType"] = request_payload["propertyType"]
    if "bedrooms" in request_payload:
        query["bedrooms"] = request_payload["bedrooms"]
    if "bathrooms" in request_payload:
        query["bathrooms"] = request_payload["bathrooms"]
    if "compCount" in request_payload:
        query["compCount"] = request_payload["compCount"]

    try:
        response = http.get(
            RENTCAST_ENDPOINT,
            headers=headers,
            params=query,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RentEstimateServiceError(f"Request to RentCast failed: {exc}") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise RentEstimateServiceError("RentCast returned a non-JSON response") from exc


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
    city: Optional[str] = None,
    state: Optional[str] = None,
    propertyType: Optional[str] = None,
    bedrooms: Optional[int] = None,
    bathrooms: Optional[float] = None,
    compCount: Optional[int] = None,
    session: Optional[requests.Session] = None,
    timeout: float = 15.0,
    supabase_client: Optional[Client] = None,
) -> RentEstimateResult:
    if not api_key:
        raise ValueError("api_key is required")

    normalized_address = (address or "").strip()
    if not normalized_address:
        raise ValueError("address is required")

    cache_request_payload: dict[str, Any] = {"address": normalized_address}

    normalized_city = (city or "").strip()
    if normalized_city:
        cache_request_payload["city"] = normalized_city

    normalized_state = (state or "").strip().upper()
    if normalized_state:
        if len(normalized_state) != 2:
            raise ValueError("state must be a 2-letter code")
        cache_request_payload["state"] = normalized_state

    normalized_property_type = _normalize_property_type(propertyType)
    if normalized_property_type:
        cache_request_payload["propertyType"] = normalized_property_type

    if bedrooms is not None:
        try:
            bedrooms_value = int(bedrooms)
        except (TypeError, ValueError) as exc:
            raise ValueError("bedrooms must be an integer") from exc
        if bedrooms_value < 0:
            raise ValueError("bedrooms must be greater than or equal to 0")
        cache_request_payload["bedrooms"] = bedrooms_value

    if bathrooms is not None:
        try:
            bathrooms_value = float(bathrooms)
        except (TypeError, ValueError) as exc:
            raise ValueError("bathrooms must be numeric") from exc
        if bathrooms_value < 0:
            raise ValueError("bathrooms must be greater than or equal to 0")
        cache_request_payload["bathrooms"] = bathrooms_value

    if compCount is not None:
        try:
            comp_count_value = int(compCount)
        except (TypeError, ValueError) as exc:
            raise ValueError("compCount must be an integer") from exc
        if comp_count_value <= 0:
            raise ValueError("compCount must be greater than 0")
        cache_request_payload["compCount"] = comp_count_value

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

    payload = _call_rentcast_api(
        http=http,
        request_payload=cache_request_payload,
        timeout=timeout,
    )
    try:
        rent_value = payload.get("rent")
        if rent_value is None:
            raise RentEstimateServiceError("RentCast response does not include rent")
        rent = float(rent_value)

        rent_range_low_value = payload.get("rentRangeLow")
        rent_range_low = float(rent_range_low_value) if rent_range_low_value is not None else None

        rent_range_high_value = payload.get("rentRangeHigh")
        rent_range_high = float(rent_range_high_value) if rent_range_high_value is not None else None
    except (TypeError, ValueError) as exc:
        raise RentEstimateServiceError("RentCast response contained a non-numeric value") from exc

    result: RentEstimateResult = {
        "rent": rent,
        "rent_range_low": rent_range_low,
        "rent_range_high": rent_range_high,
        "currency": str(payload.get("currency", "USD")),
        "address": cache_request_payload["address"],
        "subject_property": payload.get("subjectProperty", {}) or {},
        "comparables": payload.get("comparables", []) or [],
    }
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
            city="Washington",
            state="DC",
            propertyType="single family",
            bedrooms=0,
            bathrooms=1,
            compCount=5,
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