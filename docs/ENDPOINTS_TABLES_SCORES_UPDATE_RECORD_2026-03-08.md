# Endpoints, Tables, and Scores Update Record

Date: 2026-03-08  
Project: HouSmart Backend (`backend/`)  
Scope: Documentation refresh for new/active endpoints, POI counting behavior, and runtime table/score coverage.

## 1) Why this update

Documentation was updated to reflect:
- active school endpoint (`POST /api/school_scores`)
- auth endpoints mounted at `/auth/*`
- amenity POI counting fallback when RPC overload ambiguity occurs (`PGRST203`)
- runtime table-touch map including `api_call_logs` middleware writes

## 2) Endpoint inventory (current)

- `GET /api/health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/google`
- `POST /auth/verify`
- `POST /api/education_level`
- `POST /api/median_income`
- `POST /api/amenity_score`
- `POST /api/crime_score`
- `POST /api/flood_risk_score`
- `POST /api/transit_score`
- `POST /api/rent_estimate`
- `POST /api/noise_estimate_score`
- `POST /api/median_property_price`
- `POST /api/school_scores`

## 3) Amenity endpoint behavior (important)

`/api/amenity_score` now documents a two-path count strategy:

1. Primary: `count_pois` RPC  
2. Fallback: direct `osm_poi_cache` query with bounding box + haversine filtering when PostgREST returns `PGRST203` (overloaded function ambiguity)

This fallback is implemented in:
- `backend/app/services/poi_repository.py`

## 4) School endpoint behavior

`/api/school_scores` flow:

1. RPC lookup via `get_property_school_scores(search_address)`  
2. ZIP fallback query on `school_master` if direct match is empty  
3. Returns `housmart_school_score`, `s_academic`, `s_resource`, `s_equity` per row

## 5) Runtime table touch summary

- `geo_tract_metrics`
- `osm_poi_cache`
- `leaic_crosswalk`
- `flood_risk_cache`
- `flood_zones`
- `transit_cache`
- `transit_scores`
- `rent_estimate_cache`
- `noise_scores`
- `redfin_median_prices`
- `school_master`
- `api_call_logs`
- `users`

## 6) Scoring inventory summary

Numeric:
- amenity `composite_score` (0.0 to 1.0)
- school `housmart_school_score` (returned per school row)
- transit `transit_score` (5.0 to 100.0)
- flood `flood_score` (discrete mapped scale; higher is safer)
- crime `safety_score` (0.0 to 100.0)

Categorical:
- noise `noise_level` (`Unknown`, `Very High`, `High`, `Moderate`, `Low`)

Non-score outputs:
- rent estimate values
- education/income census metrics

## 7) Files updated in this doc refresh

- `docs/BACKEND_TECHNICAL_REFERENCE.md`
- `docs/SCORE_CALCULATIONS_DETAILED_RECORD_2026-03-07.md`
- `docs/STRUCTURE.md`
- `backend/README.md`
- `docs/ENDPOINTS_TABLES_SCORES_UPDATE_RECORD_2026-03-08.md` (this file)
