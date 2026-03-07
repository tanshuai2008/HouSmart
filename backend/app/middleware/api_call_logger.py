import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from starlette.responses import Response

from app.core.supabase_client import supabase

logger = logging.getLogger(__name__)


def _to_json_value(raw: bytes) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        try:
            return {"raw": raw.decode("utf-8", errors="replace")}
        except Exception:
            return {"raw": "<unreadable>"}


async def api_call_logger_middleware(request: Request, call_next):
    path = request.url.path

    if path in ("/", "/docs", "/redoc", "/openapi.json"):
        return await call_next(request)

    request_body = await request.body()
    request_json = _to_json_value(request_body)

    response = await call_next(request)

    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk

    response_json = _to_json_value(response_body)

    # Placeholder for future auth integration. Keep nullable in DB for now.
    user_id = request.headers.get("x-user-id") or None

    log_row = {
        "endpoint": path,
        "method": request.method,
        "status_code": response.status_code,
        "request_json": request_json,
        "response_json": response_json,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        supabase.table("api_call_logs").insert(log_row).execute()
    except Exception as exc:
        logger.warning("Failed to write api_call_logs: %s", exc)

    filtered_headers = {
        key: value
        for key, value in response.headers.items()
        if key.lower() != "content-length"
    }

    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=filtered_headers,
        media_type=response.media_type,
    )
