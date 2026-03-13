# Backend Structure

## Runtime API code (`backend/app/`)
- `api/routes/`: FastAPI routes for health, auth, education, income, amenity, crime, flood, transit, rent, noise, median price, school scores.
- `api/schemas/`: request/response Pydantic models.
- `services/`: domain services (POI, transit, flood, school, geocoding, rent, etc.).
- `core/`: shared clients/config and core scoring helpers.
- `middleware/api_call_logger.py`: middleware that logs request/response payloads to DB.

## Entrypoint
- `backend/main.py`: app creation, middleware registration, router mounting.

## Database and SQL
- `backend/db/migrations/001_initial.sql`: base schema and `count_pois` function.
- `backend/db/migrations/002_poi_latest_timestamp_fn.sql`: latest POI timestamp RPC.
- `backend/db/migrations/003_poi_provider_metadata.sql`: POI provider metadata updates.
- `backend/db/migrations/004_api_call_logs.sql`: `api_call_logs` table/indexes.
- `backend/db/sql/score_match_rpc.sql`: `get_property_school_scores(search_address)` school RPC.

## Offline/ops scripts
- `backend/app/scripts/apply_migrations.py`: applies SQL migrations.
- `backend/app/scripts/ingest_redfin.py`: loads `redfin_median_prices`.
- `backend/app/scripts/pipelines/*`: school master ingestion and score computation.
- `backend/app/scripts/boundaries/*`: school boundary import/inspection utilities.

## Key DB tables touched at runtime
- `geo_tract_metrics`, `osm_poi_cache`, `leaic_crosswalk`, `flood_risk_cache`, `flood_zones`, `transit_cache`, `transit_scores`, `rent_estimate_cache`, `noise_scores`, `redfin_median_prices`, `school_master`, `api_call_logs`, `users`.
