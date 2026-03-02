# RentEstimate Backend Guide

This document summarizes the current RentEstimate backend setup, including the new rent-estimate API endpoint, environment variables, cache behavior, and file organization.

## What Was Added/Updated

- Added a dedicated API endpoint for rent estimation:
  - `POST /api/rent-estimate`
- Added request/response API schemas:
  - `backend/app/api/schemas/rent_estimate.py`
- Added route handler:
  - `backend/app/api/routes/rent_estimate.py`
- Registered the route in the FastAPI app:
  - `backend/main.py`
- Updated route/schema package exports:
  - `backend/app/api/routes/__init__.py`
  - `backend/app/api/schemas/__init__.py`
- Updated `.env` template with required variable names:
  - `backend/.env`

## API Endpoints

- `GET /`
  - Health-style root message.
- `GET /api/health`
  - Basic service health check.
- `POST /api/rent-estimate`
  - Calls the rent estimation service and returns normalized rent data.

### `POST /api/rent-estimate` Request Body

```json
{
  "address": "1300 N St Nw, Washington, DC 20005",
  "property_type": "single family",
  "bedrooms": 0,
  "bathrooms": 1,
  "square_footage": 655
}
```

### Response Shape

```json
{
  "rent": 2100.0,
  "rent_range_low": 1900.0,
  "rent_range_high": 2300.0,
  "currency": "USD",
  "address": "1300 N St Nw, Washington, DC 20005"
}
```

### Error Mapping

- `400 Bad Request`
  - Input or configuration validation errors (`ValueError`).
- `502 Bad Gateway`
  - External rent-estimate provider/API failures (`RentEstimateServiceError`).
- `500 Internal Server Error`
  - Unexpected unhandled server errors.

## Environment Variables

Set these in `backend/.env`:

- `RENT_ESTIMATE_API_KEY`
  - API key for rent estimation provider (required).
- `SUPABASE_URL`
  - Supabase project URL (required).
- `SUPABASE_SERVICE_ROLE_KEY` or `SUPABASE_KEY`
  - Supabase access key (at least one required).
- `RENT_CACHE_TABLE`
  - Cache table name.
  - Default used by code: `rent_estimate_cache`.
- `RENT_CACHE_TTL_SECONDS`
  - Cache TTL in seconds.
  - Default used by code: `21600` (6 hours).
- `LOG_LEVEL`
  - Python logging level.
  - Default used by code: `INFO`.
- `ZYLA_ENDPOINT`
  - Endpoint URL for the external API.
  - Note: code currently uses a constant endpoint in `rent_estimate.py`; this env var is present as a template variable.

## Cache and Data Flow

1. Request arrives at `POST /api/rent-estimate`.
2. Inputs validated by Pydantic schema (`RentEstimateRequest`) and service-level validation.
3. Request hash generated from normalized payload.
4. Supabase cache checked (`rent_cache.py`):
   - If hit and not expired: cached value returned.
   - If miss/expired: external API is called.
5. External response normalized into `RentEstimateResponse` shape.
6. Response persisted into Supabase cache table.
7. API returns normalized response.

## File Organization (Backend)

- `backend/main.py`
  - FastAPI app initialization and router registration.
- `backend/app/api/routes/health.py`
  - Health endpoint route.
- `backend/app/api/routes/rent_estimate.py`
  - Rent estimate endpoint route.
- `backend/app/api/schemas/rent_estimate.py`
  - Request/response Pydantic models.
- `backend/app/services/rent_estimate.py`
  - Core rent-estimation business logic and provider call.
- `backend/app/services/rent_cache.py`
  - Supabase cache read/write and TTL logic.
- `backend/app/services/supabase_client.py`
  - Supabase client bootstrap and env validation.
- `backend/app/utils/logging.py`
  - Centralized logger setup.

## Run Locally

From `RentEstimate/backend`:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:

- Swagger UI: `http://127.0.0.1:8000/docs`
- Redoc: `http://127.0.0.1:8000/redoc`

## Manual Test (cURL)

```bash
curl -X POST "http://127.0.0.1:8000/api/rent-estimate" \
  -H "Content-Type: application/json" \
  -d "{\"address\":\"1300 N St Nw, Washington, DC 20005\",\"property_type\":\"single family\",\"bedrooms\":0,\"bathrooms\":1,\"square_footage\":655}"
```

## Related Docs

- `docs/rent_estimation_overview.md`
- `docs/sql_query.md`

