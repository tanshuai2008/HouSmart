# Google Maps Migration Record

Date: March 7, 2026  
Project: HouSmart Backend (`backend/`)  
Scope: Location-intelligence provider migration from OpenStreetMap Overpass to Google Maps Platform

## 1) Executive Summary

This migration replaced Overpass-based data retrieval with Google Maps APIs for all active location-intelligence features currently exposed by the backend API:

1. Amenity Score (`POST /api/amenity_score`)
2. Transit Score (`POST /api/transit_score`)
3. Noise Estimate Score (`POST /api/noise_estimate_score`)

The transition was done in phases:

1. Add Google path with runtime metadata.
2. Keep Overpass fallback temporarily for validation.
3. Validate output behavior.
4. Remove Overpass code and env/config dependencies.

Current state after migration:

1. Active API features are Google-only for these three services.
2. Overpass runtime references are removed from backend code and env template.
3. Response metadata was added to support source verification and debugging.

## 2) Endpoints and Current Behavior

### 2.1 Amenity Score

Endpoint: `POST /api/amenity_score`  
Route file: `backend/app/api/routes/amenity_score.py`

Current provider:

1. Google Places API only.

Current service path:

1. Address geocode via existing Census/geocode pipeline.
2. POIs fetched using Google Places Nearby Search.
3. Results normalized into existing POI cache schema.
4. Category scores computed from cached POIs using existing `count_pois(...)` function.

Current response metadata:

1. `_meta.source` (`google_places` or `osm_poi_cache`)
2. `_meta.api_used` (`google_places` or `cache`)
3. `_meta.cache_hit` (bool)
4. `_meta.data_updated_at` (latest POI timestamp near search point/radius)

### 2.2 Transit Score

Endpoint: `POST /api/transit_score`  
Route file: `backend/app/api/routes/transit.py`

Current provider:

1. Google Places API only.

Current service path:

1. Address geocoding.
2. Nearby transit retrieval via Google Places types:
   `transit_station`, `bus_station`, `train_station`, `subway_station`.
3. Pagination handling for Nearby Search (up to 3 pages/type with next-page token delay).
4. Stop deduplication by `place_id`.
5. Normalized transit scoring model (details in section 6).
6. Response cached in `transit_cache`.
7. Score persisted to `transit_scores`.

Current response metadata:

1. `source` (`Google Maps Places API`)
2. `api_used` (`google_places` or `cache`)

### 2.3 Noise Estimate Score

Endpoint: `POST /api/noise_estimate_score`  
Route file: `backend/app/api/routes/noise_estimator.py`

Current provider:

1. Google Roads API only (`nearestRoads`).

Current service path:

1. Address geocoding.
2. Nearest road lookup using Google Roads snapped points.
3. Haversine distance calculation from property point to snapped road point.
4. Existing qualitative noise-band classification retained.
5. Cached/persisted in `noise_scores`.

Current response metadata:

1. `source` (`Google Maps Roads API` or `Supabase Cache`)
2. `api_used` (`google_roads` or `cache`)

## 3) Provider Inventory Before vs After

### Before migration

1. Amenity: Overpass POI query
2. Transit: Overpass mirrors
3. Noise: Overpass nearest-road query
4. Legacy road map import service: Overpass

### After migration

1. Amenity: Google Places
2. Transit: Google Places
3. Noise: Google Roads
4. Legacy Overpass-only services removed from active backend codebase

## 4) Configuration Changes

Primary settings file: `backend/app/core/config.py`

### Added/used for Google

1. `GOOGLE_MAPS_API_KEY`
2. `GOOGLE_PLACES_HTTP_TIMEOUT_SECONDS`
3. `GOOGLE_ROADS_HTTP_TIMEOUT_SECONDS`

### Removed/deprecated Overpass/provider-toggle keys

1. `AMENITY_POI_PROVIDER`
2. `TRANSIT_PROVIDER`
3. `NOISE_PROVIDER`
4. `OVERPASS_HTTP_TIMEOUT_SECONDS`
5. `OVERPASS_QUERY_TIMEOUT_SECONDS`
6. `OVERPASS_MIRRORS`
7. `OVERPASS_URL`

Env template updated:

1. `backend/.env.example` now reflects Google-only runtime keys for migrated features.

## 5) Database and Cache Impact

### 5.1 Tables involved in migrated features

1. `osm_poi_cache`  
   Used by amenity scoring as POI cache/input dataset.

2. `transit_cache`  
   TTL cache for transit responses.

3. `transit_scores`  
   Persisted transit score snapshot per coordinate key.

4. `noise_scores`  
   Address-based noise cache/persistence table.

### 5.2 Migration files touched

1. `backend/db/migrations/001_initial.sql`  
   POI provider default aligned to Google metadata default.

2. `backend/db/migrations/002_poi_latest_timestamp_fn.sql`  
   Added function `latest_poi_timestamp(...)` used for amenity freshness metadata.

3. `backend/db/migrations/003_poi_provider_metadata.sql`  
   Provider default/backfill aligned to Google metadata default.

### 5.3 Caching characteristics

1. Amenity cache behavior: location/radius-driven via POI cache lookups.
2. Transit cache behavior: provider-specific key path now effectively Google-only.
3. Noise cache behavior: address-keyed via `noise_scores`.

Operational note:

1. During testing, old cache rows can mask new logic.
2. Use targeted row deletes or temporary test addresses/radii when validating code changes.

## 6) Scoring Model Changes

### 6.1 Amenity scoring

No formula change.  
Only POI source changed from Overpass tags to Google Places mapped categories.

### 6.2 Transit scoring

Transit scoring was updated from threshold-style behavior to normalized weighted scoring.

Current formula (0-100, clamped to 5-100):

1. Bus density component: `min(bus_count / 20, 1) * 40`
2. Rail density component: `min(rail_count / 8, 1) * 40`
3. Proximity component: `max(0, 1 - nearest_stop_meters / radius_meters) * 20`
4. Final score: rounded and clamped

Why changed:

1. Prior threshold logic produced unintuitive output in rail-dominant areas.
2. Google stop typing can differ from OSM tagging distributions.
3. Normalization improves continuity and ranking behavior.

### 6.3 Noise classification

No band change:

1. `<20m` = `Very High`
2. `<50m` = `High`
3. `<100m` = `Moderate`
4. `>=100m` = `Low`
5. `None` = `Unknown`

Only nearest-road data source changed to Google Roads.

## 7) Files Added / Updated / Removed

### Added

1. `backend/app/services/google_places_service.py`
2. `backend/db/migrations/002_poi_latest_timestamp_fn.sql`

### Updated (key)

1. `backend/app/services/poi_service.py`
2. `backend/app/services/poi_repository.py`
3. `backend/app/services/transit_service.py`
4. `backend/app/services/noise_estimator.py`
5. `backend/app/core/config.py`
6. `backend/.env.example`
7. `backend/db/migrations/001_initial.sql`
8. `backend/db/migrations/003_poi_provider_metadata.sql`

### Removed

1. `backend/app/services/osm_fetch_service.py`
2. `backend/app/services/road_map.py`

## 8) What Did Not Change

1. Endpoint paths and main route wiring.
2. Flood, crime, education, income, rent, median price, auth, health service behavior.
3. Core database table set for non-migrated domains.
4. Existing geocoding dependencies for address resolution where already in use.

## 9) Validation Done During Migration

1. Code-level scans to confirm Overpass references removed from active backend code.
2. Syntax parsing checks on modified Python modules.
3. API response metadata added to verify live-vs-cache path (`api_used`) during testing.
4. Transit logic corrected for Google pagination to reduce undercounting risk.

## 10) Known Follow-ups / Hygiene

1. Route docstrings in some files still mention OSM/Overpass semantics and should be text-updated to Google wording.
2. If old caches exist, results can appear stale during regression testing.
3. Ensure Google quotas/alerts are configured in GCP to avoid unexpected spend.

## 11) Recommended Operational Runbook

After deploy/restart:

1. Validate `/api/amenity_score` with a fresh address.
2. Validate `/api/transit_score` with a fresh radius to avoid old cached rows.
3. Validate `/api/noise_estimate_score` with non-cached address.
4. Confirm metadata fields:
   - Amenity: `_meta.api_used`
   - Transit: `api_used`
   - Noise: `api_used`
5. If stale responses appear, clear targeted cache rows first before investigating logic.

## 12) Security Note

A Google API key is present in environment configuration.  
Best practice:

1. Keep key server-side only.
2. Restrict key to required APIs only.
3. Restrict usage by backend egress/IP where possible.
4. Rotate the key if it has been exposed in logs/chat/screenshots.

