# Rent Estimation Service

## Prerequisites
- Python 3.11+
- `.env` file in the project root with:
  - `RENT_ESTIMATE_API_KEY`
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY` (or `SUPABASE_KEY`)
  - Optional: `RENT_CACHE_TTL_SECONDS` and `RENT_CACHE_TABLE`
- Dependencies from `requirements.txt` installed (`pip install -r requirements.txt`)

## External API
- Provider: **Zyla Labs** – US Rental Estimation API
- Endpoint: `https://zylalabs.com/api/2827/us+rental+estimation+api/2939/get+estimation`
- Required parameters:
  1. `address`: full property address (Street, City, State, Zip)
  2. `propertyType`: property type string (single family, condo, etc.)
  3. `bedrooms`: integer count
  4. `bathrroms`: numeric count (supports partial baths)
  5. `squareFootage`: integer living area
- Response highlights: `rent`, `rentRangeLow`, `rentRangeHigh`, `listings` array with comparable listings.

## Caching Strategy
- Supabase table: **`rent_estimate_cache`**
- Columns: `request_hash` (PK), `address`, `request_payload`, `response_payload`, `updated_at_epoch`, `created_at`.
- Workflow:
  1. Normalize inputs and build deterministic hash.
  2. Look up Supabase row by `request_hash`.
  3. Cache hit ⇒ return stored JSON payload.
  4. Cache miss ⇒ call Zyla, store full JSON, return normalized result.
  5. TTL controlled by `RENT_CACHE_TTL_SECONDS` (default 6 hours).

## Runtime Flow
1. `fetch_rent_estimate()` validates the five inputs and trims/casts types.
2. Builds `request_hash` via `build_request_hash()` and checks Supabase via `get_cached_estimate()`.
3. On miss, `_call_zyla_api()` issues an HTTP GET with the same tuple and handles errors.
4. `_build_result()` normalizes rent values, `rent_range_low/high`, and currency before returning to callers.
5. `_persist_cache_entry()` stores the request payload and **raw Zyla JSON response** for future identical requests.

## Example CLI Run
From the `backend` directory:
```
python app/services/rent_estimate.py
```
This script loads the `.env`, initializes the shared Supabase client, calls `fetch_rent_estimate()` with sample inputs, and prints the result. Subsequent runs with the same parameters will hit the cache until TTL expiration.

## Key Files
- `app/services/rent_estimate.py`: main service, validation, API call, cache orchestration.
- `app/services/rent_cache.py`: Supabase hashing, TTL enforcement, upserts.
- `app/services/supabase_client.py`: cached Supabase SDK client.
- `docs/sql_query.md`: table definition for `rent_estimate_cache`.
