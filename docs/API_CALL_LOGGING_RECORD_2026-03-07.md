# API Call Logging Record

Date: March 7, 2026  
Project: HouSmart Backend (`backend/`)  
Scope: Centralized request/response logging for API endpoints

## 1) Objective

A centralized logging mechanism was added so each API call can be audited later with:

1. Endpoint and method
2. HTTP status code
3. Request payload
4. Response payload
5. Timestamp
6. Optional user linkage field (`user_id`) for future auth integration

This creates a durable historical trail for debugging, analytics, and later user-level attribution.

## 2) What Was Added

### 2.1 New database table

Migration file:

1. `backend/db/migrations/004_api_call_logs.sql`

Table:

1. `api_call_logs`

Columns:

1. `id` `bigserial primary key`
2. `endpoint` `text not null`
3. `method` `text not null`
4. `status_code` `integer not null`
5. `request_json` `jsonb`
6. `response_json` `jsonb`
7. `user_id` `text` (nullable for now)
8. `created_at` `timestamptz not null default now()`

Indexes:

1. `idx_api_call_logs_created_at` on `created_at desc`
2. `idx_api_call_logs_endpoint` on `endpoint`
3. `idx_api_call_logs_user_id` on `user_id`

### 2.2 New middleware

File:

1. `backend/app/middleware/api_call_logger.py`

Registration:

1. `backend/main.py` via `app.middleware("http")(api_call_logger_middleware)`

Package init:

1. `backend/app/middleware/__init__.py`

## 3) Runtime Behavior

For each request:

1. Read request body.
2. Execute endpoint handler.
3. Read response body produced by handler.
4. Insert a row into `api_call_logs`.
5. Rebuild and return response to client unchanged in content/status.

Skipped paths:

1. `/`
2. `/docs`
3. `/redoc`
4. `/openapi.json`

User linkage behavior (current placeholder):

1. `user_id` is read from request header `x-user-id` if present.
2. If absent, `user_id` remains `NULL`.

## 4) Current Data Shape

`request_json` and `response_json` capture parsed JSON where possible.

Fallback behavior:

1. If payload is not valid JSON, middleware stores `{ "raw": "<decoded string>" }`.
2. If body is empty, stored value is `NULL`.

## 5) Example Record

```json
{
  "id": 101,
  "endpoint": "/api/transit_score",
  "method": "POST",
  "status_code": 200,
  "request_json": {
    "address": "2960 Broadway, New York, NY 10027",
    "radius_meters": 800
  },
  "response_json": {
    "status": "success",
    "data": {
      "transit_score": 82.1,
      "api_used": "google_places"
    }
  },
  "user_id": null,
  "created_at": "2026-03-07T22:14:11.352Z"
}
```

## 6) Why This Design

1. Middleware-level logging avoids duplicating logging code in each route.
2. JSONB columns keep payloads queryable in SQL while preserving nested structure.
3. Nullable `user_id` enables future auth/user mapping without schema redesign.
4. Timestamp is DB-backed and indexed for timeline queries.

## 7) Operational Notes

1. This table can grow quickly; monitor size and retention.
2. Consider monthly partitioning or retention jobs if traffic increases.
3. Sensitive fields are currently not masked by default.
4. Logging failure does not block endpoint response; failures are warning-logged.

## 8) Security and Privacy Notes

Because request/response bodies are stored, review payloads for:

1. Passwords
2. Tokens
3. PII
4. Secrets

Recommended next hardening:

1. Add field-level redaction (e.g., `password`, `token`, `authorization`, API keys).
2. Optionally disable logging for selected auth endpoints.
3. Add retention policy (e.g., 30/60/90 days).

## 9) Verification Queries

Basic recent logs:

```sql
select id, created_at, endpoint, method, status_code, user_id
from api_call_logs
order by created_at desc
limit 50;
```

Endpoint-specific logs:

```sql
select created_at, status_code, request_json, response_json
from api_call_logs
where endpoint = '/api/amenity_score'
order by created_at desc
limit 20;
```

Failed requests:

```sql
select created_at, endpoint, method, status_code, response_json
from api_call_logs
where status_code >= 400
order by created_at desc
limit 50;
```

## 10) Future Extension Plan

Planned once full auth/user context is finalized:

1. Populate `user_id` from authenticated identity (JWT/session), not header placeholder.
2. Add foreign key to users table if/when user table schema is finalized.
3. Add tenant/account scoping fields if multi-tenant requirements appear.

