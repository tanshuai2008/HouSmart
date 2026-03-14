from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.config.db import require_supabase

logger = logging.getLogger(__name__)


def cache_get_json(*, table: str, key: str) -> dict | None:
    """Best-effort read from a Supabase KV cache table.

    Expected schema (recommended):
      - key (text primary key)
      - value (jsonb)
      - expires_at (timestamptz)

    If the table/columns don't exist, returns None.
    """
    supabase = require_supabase()
    now = datetime.now(timezone.utc).isoformat()

    # Preferred path: honor expires_at TTL.
    try:
        response = (
            supabase.table(table)
            .select("value")
            .eq("key", key)
            .gt("expires_at", now)
            .limit(1)
            .execute()
        )
        if response.data:
            row = response.data[0]
            return row.get("value")
        return None
    except Exception as e:
        logger.debug(f"Supabase cache GET (ttl) failed for {table}:{key}: {e}")

    # Fallback path: table without expires_at.
    try:
        response = (
            supabase.table(table)
            .select("value")
            .eq("key", key)
            .limit(1)
            .execute()
        )
        if response.data:
            row = response.data[0]
            return row.get("value")
    except Exception as e:
        logger.debug(f"Supabase cache GET failed for {table}:{key}: {e}")

    return None


def cache_set_json(*, table: str, key: str, value: dict, ttl_seconds: int | None) -> None:
    """Best-effort write to a Supabase KV cache table.

    Silently ignores any failures (cache is an optimization).
    """
    supabase = require_supabase()

    payload: dict[str, Any] = {
        "key": key,
        "value": value,
    }

    if ttl_seconds is not None:
        payload["expires_at"] = (
            datetime.now(timezone.utc) + timedelta(seconds=int(ttl_seconds))
        ).isoformat()

    # Preferred: upsert with expires_at.
    try:
        supabase.table(table).upsert(payload).execute()
        return
    except Exception as e:
        logger.debug(f"Supabase cache SET (ttl) failed for {table}:{key}: {e}")

    # Fallback: table without expires_at.
    try:
        supabase.table(table).upsert({"key": key, "value": value}).execute()
    except Exception as e:
        logger.debug(f"Supabase cache SET failed for {table}:{key}: {e}")
