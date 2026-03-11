# Tables, Connectivity, and Dependencies (11 March 2026)

Date: 11 March 2026

## 1) New/updated tables

### `user_properties`
- Primary user-property identity and normalized subject property snapshot.
- Added FIPS fields in migration 010:
  - `state_fips varchar(2)`
  - `county_fips varchar(5)`
- Key relationship:
  - `user_id -> users(id)`

### `property_analysis_runs`
- One run record per analysis execution.
- Tracks `status`, `started_at`, `completed_at`, and `error_message`.
- Key relationship:
  - `property_id -> user_properties(property_id)`

### `property_facts`
- One row per run (`run_id` unique).
- Stores derived market/census/crime/flood/transit/noise/school facts.
- Added numeric noise fields in migration 011:
  - `noise_index numeric(5,1)`
  - `estimated_noise_db numeric(5,1)`
- Composite FK:
  - `(run_id, property_id) -> property_analysis_runs(run_id, property_id)`

### `comparable_properties`
- Top comparable rental properties per run.
- Stores listing/property metadata + `correlation_score`.

### `property_user_scores`
- Stores user-scoped endpoint scores for each run.
- `noise_score` changed to text in migration 009:
  - `varchar(80)`
- Unique scope:
  - `(user_id, property_id, run_id)`

## 2) Connectivity graph

- `users` -> `user_properties`
- `user_properties` -> `property_analysis_runs`
- `property_analysis_runs` -> `property_facts`
- `property_analysis_runs` -> `comparable_properties`
- `property_analysis_runs` + `user_properties` + `users` -> `property_user_scores`

## 3) Runtime dependency flow (analysis)

Primary orchestrator dependencies:
- Rent/value:
  - Rent estimate service
  - Median house price service
- Census:
  - Income
  - Education
- Safety:
  - Crime scoring core + FBI + geocoder + crosswalk table
- Location quality:
  - Amenity POI service (cache + Google Places fallback)
  - Transit service (Google Places + transit cache + transit_scores)
  - Flood service (FEMA NFHL + flood cache + flood_zones)
  - Noise estimator (Google Roads + local cache table)
- Schools:
  - `school_master` table via school score service

## 4) API and app wiring

- New endpoints:
  - `POST /api/property/analyze`
  - `GET /api/property/analyze/{run_id}`
  - `GET /api/dashboard/property/{property_id}?user_id=...`
- Router registration:
  - `analysis.router` is now included in `backend/main.py`.

## 5) Important operational notes

- `analysis_orchestrator` catches partial service failures and continues where possible (`_safe_call` / `_safe_async_call`).
- Final run status is authoritative for UI polling.
- Caches reduce external API pressure (`flood_risk_cache`, `transit_cache`, `noise_scores`, `crime_score_cache`).
