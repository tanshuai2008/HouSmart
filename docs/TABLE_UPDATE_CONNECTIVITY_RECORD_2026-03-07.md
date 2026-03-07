# Table Update and Connectivity Record (Current Code)

Date: 2026-03-07  
Scope: `backend/main.py` active routers + backend services/scripts currently in repo.

## 1. Active runtime write paths (API/middleware)

### 1.1 `api_call_logs`
- Table: `api_call_logs`
- Writer: `backend/app/middleware/api_call_logger.py`
- Trigger: Every HTTP request except `/`, `/docs`, `/redoc`, `/openapi.json`
- Operation: `insert`
- Payload persisted:
  - `endpoint`, `method`, `status_code`
  - `request_json`, `response_json`
  - `user_id` from `x-user-id` header (nullable)
  - `created_at` (UTC ISO timestamp)
- Connectivity:
  - Source data comes from request/response pipeline.
  - No upstream DB dependency.
  - Used for auditing/observability only (not read by app endpoints).

### 1.2 `geo_tract_metrics`
- Table: `geo_tract_metrics`
- Writers:
  - `backend/app/services/education_repository.py` (`upsert_tract_education`)
  - `backend/app/services/income_repository.py` (`upsert_tract_income`)
- Triggers:
  - `POST /api/education_level`
  - `POST /api/median_income`
- Operation: `upsert` (primary key: `tract_geoid`)
- Columns updated:
  - Education flow: `tract_geoid`, `state_fips`, `county_fips`, `education_bachelor_pct`
  - Income flow: `tract_geoid`, `state_fips`, `county_fips`, `median_income`
- Connectivity:
  - Input produced by `CensusService.get_education_by_address` / `get_income_by_address`.
  - Same tract row is incrementally enriched by two different endpoints.
  - No score value is computed in this table; it stores tract attributes used by clients.

### 1.3 `osm_poi_cache`
- Table: `osm_poi_cache`
- Writer: `backend/app/services/poi_repository.py` via `POIService`
- Trigger: `POST /api/amenity_score` when cache miss (`existing == 0` within 2000m school probe)
- Operation: `insert` (bulk)
- Columns inserted:
  - `osm_key`, `osm_value`, `provider` (default/explicit `google_places`)
  - `latitude`, `longitude`
  - `location` geography point
- Connectivity:
  - Upstream: Google Places in `GooglePlacesService.fetch_all_pois`.
  - Downstream reads:
    - `count_pois(...)` SQL function for category counts
    - `latest_poi_timestamp(...)` SQL function for freshness metadata
  - Directly drives amenity score outputs.

### 1.4 `flood_risk_cache`
- Table: `flood_risk_cache`
- Writer: `backend/app/services/flood_service.py` (`_cache_set`)
- Trigger: `POST /api/flood_risk_score` on cache miss after FEMA/mock result
- Operation: `upsert` on `key`
- Columns updated: `key`, `value` (jsonb), `expires_at`
- Connectivity:
  - Input: computed flood payload from FEMA NFHL (or mock fallback).
  - Used by `_cache_get` to avoid repeated API calls.
  - Feeds `save_flood_zone_to_db` result path.

### 1.5 `flood_zones`
- Table: `flood_zones`
- Writer: `backend/app/services/flood_service.py` (`save_flood_zone_to_db`)
- Trigger: `POST /api/flood_risk_score`
- Operation: `upsert` on `lat,lng`
- Columns updated:
  - `lat`, `lng`, `fld_zone`, `risk_label`, `flood_score`
  - `flood_data_unknown`, `source`
- Connectivity:
  - Upstream: `get_flood_zone` output.
  - Downstream: returned directly by flood endpoint response.
  - Acts as persistent flood snapshot store.

### 1.6 `transit_cache`
- Table: `transit_cache`
- Writer: `backend/app/services/transit_service.py` (`_cache_set`)
- Trigger: `POST /api/transit_score` on cache miss after Google transit fetch
- Operation: `upsert` on `key`
- Columns updated: `key`, `value` (jsonb), `expires_at`
- Connectivity:
  - Input: normalized transit stop payload + computed transit score.
  - Used by `_cache_get` to serve repeated requests quickly.
  - Feeds durable score persistence into `transit_scores`.

### 1.7 `transit_scores`
- Table: `transit_scores`
- Writer: `backend/app/services/transit_service.py` (`save_transit_score_to_db`)
- Trigger: `POST /api/transit_score`
- Operation: `upsert` on `property_lat,property_lng`
- Columns updated:
  - `property_lat`, `property_lng`, `radius_meters`
  - `bus_stop_count`, `rail_station_count`, `nearest_stop_meters`
  - `transit_score`, `source`
- Connectivity:
  - Upstream: `fetch_transit_stops` (cache or live Google fetch).
  - Downstream: same values returned in endpoint response.
  - Persistent snapshot table for transit scoring outcomes.

### 1.8 `noise_scores`
- Table: `noise_scores`
- Writer: `backend/app/services/noise_estimator.py`
- Trigger: `POST /api/noise_estimate_score` on address cache miss
- Operation: `insert`
- Columns inserted:
  - `address`, `latitude`, `longitude`
  - `distance_to_road`, `noise_level`
- Connectivity:
  - Upstream: geocode + nearest road lookup.
  - Downstream:
    - Same table queried first on subsequent exact-address requests.
    - response returns cached/computed noise result.

### 1.9 `rent_estimate_cache`
- Table: `rent_estimate_cache` (or env override `RENT_CACHE_TABLE`)
- Writer: `backend/app/services/rent_cache.py` (`upsert_cached_estimate`)
- Trigger: `POST /api/rent_estimate` when cache miss and API success
- Operation: `upsert` on `request_hash`
- Columns updated:
  - `request_hash`, `address`
  - `request_payload`, `response_payload`
  - `updated_at_epoch`
- Connectivity:
  - Upstream: RentCast response payload.
  - Downstream: `get_cached_estimate` for TTL-aware cache retrieval.

### 1.10 `users`
- Table: `users` (not created in current migrations; expected pre-existing in Supabase)
- Writer: `backend/app/services/auth_service.py`
- Triggers:
  - `POST /auth/register` -> `insert`
  - `POST /auth/google` (new user path) -> `insert`
  - `POST /auth/login` and `/auth/google` -> `update` (`last_login`)
- Connectivity:
  - Upstream: Firebase identity workflows.
  - Downstream: read by auth endpoints for user lookup/session responses.

## 2. Non-runtime/manual-or-script write paths

### 2.1 `schema_migrations`
- Table: `schema_migrations`
- Writer: `backend/app/scripts/apply_migrations.py`
- Trigger: manual migration run
- Operation: `insert ... on conflict do nothing`
- Connectivity:
  - Tracks applied SQL files in `backend/db/migrations/*.sql`.

### 2.2 `leaic_crosswalk`
- Table: `leaic_crosswalk`
- Writer: `backend/app/services/leaic_crosswalk_loader.py`
- Trigger: manual data load script execution
- Operation: batched `upsert`
- Connectivity:
  - Downstream critical read dependency for `POST /api/crime_score` ORI resolution.

### 2.3 `redfin_median_prices`
- Table: `redfin_median_prices`
- Writer: `backend/app/scripts/ingest_redfin.py`
- Trigger: manual script run OR auto-trigger from median price service when table empty
- Operation:
  - full-table `delete` (`neq("id", 0)`) then batched `insert`
- Connectivity:
  - Downstream read by median house price endpoint/service.

## 3. End-to-end connectivity map (runtime)

1. `/api/education_level` -> Census -> `geo_tract_metrics` upsert (education fields).  
2. `/api/median_income` -> Census -> `geo_tract_metrics` upsert (income fields).  
3. `/api/amenity_score` -> Census geocode -> cache probe via `count_pois` -> optional Google fetch -> `osm_poi_cache` insert -> scoring reads via RPC -> response.  
4. `/api/flood_risk_score` -> geocode -> `flood_risk_cache` read/write -> zone mapping -> `flood_zones` upsert -> response.  
5. `/api/transit_score` -> geocode -> `transit_cache` read/write -> scoring -> `transit_scores` upsert -> response.  
6. `/api/noise_estimate_score` -> geocode -> `noise_scores` read, then insert on miss -> response.  
7. `/api/rent_estimate` -> `rent_estimate_cache` read/write around RentCast API call -> response.  
8. All above endpoints (and most auth routes) -> middleware writes `api_call_logs`.

## 4. Connectivity notes and constraints

- `users` and `properties` are referenced in code, but `properties` is not currently wired into `main.py` routers and neither table is created by the listed migration files.
- `transit_scores` primary key is `(property_lat, property_lng)`; repeated requests with different `radius_meters` overwrite the same row for that coordinate pair.
- `noise_scores` cache key behavior is exact string match on `address`; differently formatted equivalent addresses create separate rows.
- Amenity cache warm check is based only on nearby `"amenity":"school"` count within 2000m, not on all category tags.
