from __future__ import annotations
from typing import Any, Optional, TypedDict
import os
import requests
from dotenv import load_dotenv

from app.services.rent_cache import (
    RentCacheError,
    get_cached_estimate,
    upsert_cached_estimate,
)
from app.utils.logging import get_logger

load_dotenv()
api_key = os.getenv("RENT_ESTIMATE_API_KEY_RentCast")
RENTCAST_ENDPOINT = "https://api.rentcast.io/v1/avm/rent/long-term"


PROPERTY_TYPE_LIST =[
    "Single Family",
    "Condo",
    "Townhouse",
    "Manufactured",
    "Multi-Family",
    "Apartment"
]

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
    """Raised when the RentCast request fails or returns invalid data."""


def build_validated_payload(
    *,
    address: str,
    city: Optional[str],
    state: Optional[str],
    propertyType: Optional[str],
    bedrooms: Optional[int],
    bathrooms: Optional[float],
    compCount: Optional[int],
) -> dict[str, Any]:
    normalized_address = (address or "").strip()
    if not normalized_address:
        raise ValueError("address is required")

    payload: dict[str, Any] = {"address": normalized_address}

    normalized_city = (city or "").strip()
    if normalized_city:
        payload["city"] = normalized_city

    normalized_state = (state or "").strip().upper()
    if normalized_state:
        if len(normalized_state) != 2:
            raise ValueError("state must be a 2-letter code")
        payload["state"] = normalized_state

    normalized_property_type = normalize_property_type(propertyType)
    if normalized_property_type:
        payload["propertyType"] = normalized_property_type

    if bedrooms is not None:
        try:
            bedrooms_value = int(bedrooms)
        except (TypeError, ValueError) as exc:
            raise ValueError("bedrooms must be an integer") from exc
        if bedrooms_value < 0:
            raise ValueError("bedrooms must be greater than or equal to 0")
        payload["bedrooms"] = bedrooms_value

    if bathrooms is not None:
        try:
            bathrooms_value = float(bathrooms)
        except (TypeError, ValueError) as exc:
            raise ValueError("bathrooms must be numeric") from exc
        if bathrooms_value < 0:
            raise ValueError("bathrooms must be greater than or equal to 0")
        payload["bathrooms"] = bathrooms_value

    if compCount is not None:
        try:
            comp_count_value = int(compCount)
        except (TypeError, ValueError) as exc:
            raise ValueError("compCount must be an integer") from exc
        if comp_count_value <= 0:
            raise ValueError("compCount must be greater than 0")
        payload["compCount"] = comp_count_value

    return payload

def normalize_property_type(propertyType: Optional[str]) -> Optional[str]:
    if propertyType is None:
        return None
    propertyType = propertyType.strip()
    if propertyType in PROPERTY_TYPE_LIST:
        return propertyType



def try_get_cached_result(
    *,
    address: str,
    cache_key: str,
    ttl_seconds: int,
    supabase_client
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


def call_rentcast_api(
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
    optional_fields = ("city", "state", "propertyType", "bedrooms", "bathrooms", "compCount")
    for field in optional_fields:
        if field in request_payload:
            query[field] = request_payload[field]

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


def persist_cache_entry(
    *,
    cache_key: str,
    cache_request_payload: dict[str, Any],
    payload: dict[str, Any],
    supabase_client
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




__all__ = [
    "RentEstimateResult",
    "RentEstimateServiceError",
    "call_rentcast_api",
    "persist_cache_entry",
    "try_get_cached_result",
    "normalize_property_type",
    "build_validated_payload",
]
