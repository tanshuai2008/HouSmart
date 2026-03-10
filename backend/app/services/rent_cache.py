from __future__ import annotations

import json
import os
import time
from typing import TYPE_CHECKING, Any, Dict, Optional

from app.services.supabase_client import SupabaseConfigError, get_supabase
from app.utils.logging import get_logger

logger = get_logger(__name__)

CACHE_TABLE_NAME = os.getenv("RENT_CACHE_TABLE", "rent_estimate_cache")
DEFAULT_TTL_SECONDS = 6 * 60 * 60  # 6 hours


class RentCacheError(Exception):
    """Raised when Supabase cache operations fail."""


def get_cache_ttl_seconds() -> int:
    """Return the TTL for cache entries, falling back to DEFAULT_TTL_SECONDS."""
    raw_value = os.getenv("RENT_CACHE_TTL_SECONDS")
    if raw_value is None:
        return DEFAULT_TTL_SECONDS
    try:
        ttl = int(raw_value)
    except ValueError:
        logger.warning("Invalid RENT_CACHE_TTL_SECONDS value '%s'; falling back to default", raw_value)
        return DEFAULT_TTL_SECONDS
    return max(ttl, 0)


def build_request_hash(payload: Dict[str, Any]) -> str:
    """Create a deterministic hash for the request payload."""
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    import hashlib

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_cached_estimate(
    request_hash: str,
    ttl_seconds: Optional[int] = None,
    *,
    supabase_client,
) -> Optional[Dict[str, Any]]:
    ttl = DEFAULT_TTL_SECONDS if ttl_seconds is None else ttl_seconds
    client = supabase_client
    try:
        response = (
            client
            .table(CACHE_TABLE_NAME)
            .select("response_payload, updated_at_epoch")
            .eq("request_hash", request_hash)
            .limit(1)
            .execute()
        )
    except SupabaseConfigError as exc:
        raise RentCacheError(str(exc)) from exc
    except Exception as exc:  # Supabase SDK raises generic exceptions for HTTP errors
        raise RentCacheError(f"Supabase cache lookup failed: {exc}") from exc

    rows = response.data or []
    if not rows:
        return None

    row = rows[0]
    updated_at_epoch = row.get("updated_at_epoch")
    if isinstance(updated_at_epoch, (int, float)) and ttl > 0:
        if time.time() - float(updated_at_epoch) > ttl:
            logger.debug("Cache entry expired for hash %s", request_hash)
            return None

    cached_payload = row.get("response_payload")
    if cached_payload is None:
        logger.debug("Cache row missing response_payload for hash %s", request_hash)
    return cached_payload


def upsert_cached_estimate(
    request_hash: str,
    request_payload: Dict[str, Any],
    response_payload: Dict[str, Any],
    *,
    supabase_client,
) -> None:
    client = supabase_client
    row = {
        "request_hash": request_hash,
        "address": request_payload.get("address"),
        "request_payload": request_payload,
        "response_payload": response_payload,
        "updated_at_epoch": int(time.time()),
    }
    try:
        (
            client
            .table(CACHE_TABLE_NAME)
            .upsert(row)
            .execute()
        )
    except SupabaseConfigError as exc:
        raise RentCacheError(str(exc)) from exc
    except Exception as exc:
        raise RentCacheError(f"Supabase cache upsert failed: {exc}") from exc
