from __future__ import annotations
from typing import Any, Optional
import requests

from app.services.rent_cache import build_request_hash, get_cache_ttl_seconds
from app.services.rent_estimate import (
    RentEstimateResult,
    build_validated_payload,
    call_rentcast_api,
    persist_cache_entry,
    try_get_cached_result,
)
from app.services.supabase_client import get_supabase


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
) -> RentEstimateResult:
    """Fetch a rent estimate via RentCast, using core-level validation and caching."""

    cache_request_payload = build_validated_payload(
        address=address,
        city=city,
        state=state,
        propertyType=propertyType,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        compCount=compCount,
    )

    http = session or requests.Session()
    cache_key = build_request_hash(cache_request_payload)
    ttl_seconds = get_cache_ttl_seconds()
    supabase = get_supabase()

    cached_result = try_get_cached_result(
        address=cache_request_payload["address"],
        cache_key=cache_key,
        ttl_seconds=ttl_seconds,
        supabase_client=supabase,
    )
    if cached_result:
        return cached_result

    payload = call_rentcast_api(
        http=http,
        request_payload=cache_request_payload,
        timeout=timeout,
    )

    result: RentEstimateResult = {
        "rent": payload.get("rent"),
        "rent_range_low": payload.get("rentRangeLow"),
        "rent_range_high": payload.get("rentRangeHigh"),
        "currency": str(payload.get("currency", "USD")),
        "address": cache_request_payload["address"],
        "subject_property": payload.get("subjectProperty", {}) or {},
        "comparables": payload.get("comparables", []) or [],
    }
    persist_cache_entry(
        cache_key=cache_key,
        cache_request_payload=cache_request_payload,
        payload=payload,
        supabase_client=supabase,
    )
    return result


__all__ = ["fetch_rent_estimate"]
