# Score Calculations Detailed Record

Date: 2026-03-07  
Scope: all score-producing logic reachable from `backend/main.py` active routes.

## 1. Amenity Score (`POST /api/amenity_score`)

## 1.1 Entry point and flow
- Route: `backend/app/api/routes/amenity_score.py`
- Service: `backend/app/services/poi_service.py` (`compute_all_categories`)
- Geocoding source: `CensusService.get_location_data(address)`
- Data source hierarchy:
  1. Check nearby POI cache viability (school count probe in 2000m via `count_pois` RPC).
  2. If miss: fetch POIs from Google Places and insert into `osm_poi_cache`.
  3. For each configured category, compute count + score from cached rows using `count_pois`.

## 1.2 Category configuration (weights, thresholds, radii)
- Defined in `backend/app/data/poi_categories.py`.
- `education`: radius 2400m, threshold 5, weight 0.2
- `retail`: radius 1600m, threshold 8, weight 0.2
- `healthcare`: radius 3200m, threshold 4, weight 0.2
- `lifestyle`: radius 1600m, threshold 10, weight 0.2
- `transit`: radius 1200m, threshold 6, weight 0.2

## 1.3 Formula
- Per-category:
  - `ratio = min(count / threshold, 1.0)`
  - `category_score = round(ratio * weight, 4)`
- Composite:
  - `composite_score = round(sum(category_score_i), 4)`
- Practical range:
  - Each category in `[0, 0.2]`
  - Composite in `[0, 1.0]`

## 1.4 Outputs and usage
- Returned as:
  - `data.<category>.count`
  - `data.<category>.score`
  - `data.composite_score`
  - `data._meta` with `source`, `api_used`, `cache_hit`, `data_updated_at`
- Persistence usage:
  - Score itself is not stored in a dedicated score table.
  - Underlying POIs are persisted in `osm_poi_cache` and recomputed per request.

## 2. Transit Score (`POST /api/transit_score`)

## 2.1 Entry point and flow
- Route: `backend/app/api/routes/transit.py`
- Service: `backend/app/services/transit_service.py`
- Flow:
  1. Geocode address -> `lat,lng`
  2. Read cached transit payload from `transit_cache` by rounded key (`lat:.4f`, `lng:.4f`, radius)
  3. On miss, fetch stops from Google Places by transit types and dedupe by `place_id`
  4. Count bus/rail, compute nearest stop distance
  5. Compute `transit_score`
  6. Upsert result into `transit_scores`

## 2.2 Transit formula
- Function: `_compute_transit_score(bus_count, rail_count, nearest_meters, radius_meters)`
- Constants:
  - Bus saturation point: `20`
  - Rail saturation point: `8`
  - Weights: bus `40%`, rail `40%`, proximity `20%`
  - Hard minimum score floor: `5.0`
- Steps:
  - If `bus_count <= 0` and `rail_count <= 0`: return `5.0`
  - `bus_norm = min(bus_count / 20.0, 1.0)`
  - `rail_norm = min(rail_count / 8.0, 1.0)`
  - If nearest distance missing or radius invalid: `proximity_norm = 0.0`
  - Else: `proximity_norm = max(0.0, 1.0 - nearest_meters/radius_meters)`
  - `raw = (bus_norm * 40.0) + (rail_norm * 40.0) + (proximity_norm * 20.0)`
  - `transit_score = round(clamp(raw, 5.0, 100.0), 1)`
- Range: `[5.0, 100.0]`

## 2.3 Outputs and usage
- Returned in API:
  - `transit_score`, `bus_stop_count`, `rail_station_count`, `nearest_stop_meters`, `radius_meters`, `source`, `api_used`
- Persisted in DB:
  - `transit_scores.transit_score` with supporting counts/distances

## 3. Flood Risk Score (`POST /api/flood_risk_score`)

## 3.1 Entry point and flow
- Route: `backend/app/api/routes/flood.py`
- Service: `backend/app/services/flood_service.py`
- Flow:
  1. Geocode address -> `lat,lng`
  2. Cache lookup in `flood_risk_cache`
  3. Query FEMA NFHL API (or fallback mock)
  4. Resolve flood zone key
  5. Map zone to label + numeric score
  6. Cache payload and upsert `flood_zones`

## 3.2 Flood zone score mapping
- Defined in `FLOOD_ZONE_MAP`:
  - `AE`, `A` -> `20`
  - `AO`, `AH` -> `25`
  - `A99`, `AR` -> `30`
  - `VE`, `V` -> `10`
  - `X500`, `B` -> `60`
  - `X`, `C` -> `95`
  - `D` -> `50`
- Unknown/unsupported zone keys are coerced to `D` mapping.
- Interpretation:
  - Lower score => higher flood risk.
  - Higher score => lower flood risk.

## 3.3 Outputs and usage
- Returned in API:
  - `flood_score`, `fld_zone`, `risk_label`, `in_flood_zone`, `in_moderate_zone`, metadata fields
- Persisted in DB:
  - `flood_zones.flood_score` and context fields

## 4. Crime Safety Score (`POST /api/crime_score`)

## 4.1 Entry point and flow
- Route: `backend/app/api/routes/crime_score.py`
- Core logic: `backend/app/core/crime_scoring.py`
- Flow:
  1. Geocode and resolve jurisdiction identifiers
  2. Resolve ORI via `leaic_crosswalk`
  3. For each offense alias, fetch FBI summarized rates for local agency + U.S.
  4. Compute per-offense averages and weighted components
  5. Aggregate to local and national crime indices
  6. Convert relative ratio to `safety_score` using exponential decay
  7. Classify into `Green/Yellow/Red`

## 4.2 Offense weights and codes
- Weights (`CRIME_WEIGHTS`):
  - violent_crime `10.0`
  - rape `9.5`
  - robbery `8.0`
  - aggravated-assault `7.0`
  - burglary `6.0`
  - larceny `3.0`
  - motor-vehicle-theft `5.0`
  - arson `6.0`
  - property_crime `4.0`
  - homicide `10.0`
- FBI offense codes (`CRIME_OFFENSE_CODES`) mapped per alias (`V`, `RPE`, `ROB`, `ASS`, `BUR`, `LAR`, `MVT`, `ARS`, `P`, `HOM`).

## 4.3 Per-offense computation
- For an offense:
  - `local_avg = average(positive monthly local rates per 100k)`
  - `national_avg = average(positive monthly U.S. rates per 100k)`
  - Skip offense if either average missing or `national_avg <= 0`
  - `rate_ratio = local_avg / national_avg`
  - `weighted_local_rate = local_avg * weight`
  - `weighted_national_rate = national_avg * weight`

## 4.4 Aggregate score formula
- `local_crime_index = sum(weighted_local_rate_i)`
- `national_crime_index = sum(weighted_national_rate_i)`
- If no valid offense data or national index non-positive:
  - `safety_score = 0.0`
  - `safety_category = "No Data"`
  - `data_available = False`
- Else:
  - `relative_crime_ratio = local_crime_index / national_crime_index`
  - `safety_score = clamp(100 * exp(-0.75 * relative_crime_ratio), 0, 100)`
  - Classification:
    - `Green` if score `> 75`
    - `Yellow` if score `>= 40`
    - `Red` otherwise

## 4.5 Outputs and usage
- Returned in API:
  - `safety_score`, `safety_category`, indices, ratio, offense breakdown, data flags
- Persistence usage:
  - No dedicated DB table currently stores crime score outputs.
  - Dependency table `leaic_crosswalk` is read-only at runtime.

## 5. Noise Estimate Score (`POST /api/noise_estimate_score`)

## 5.1 Entry point and flow
- Route: `backend/app/api/routes/noise_estimator.py`
- Service: `backend/app/services/noise_estimator.py`
- Flow:
  1. Geocode address
  2. Exact-address cache lookup in `noise_scores`
  3. On miss, call Google Roads nearest-road API
  4. Compute distance and map to noise band
  5. Insert row into `noise_scores`

## 5.2 Noise classification formula
- Input: `distance_to_road_m`
- Function: `classify_noise(distance)`
- Mapping:
  - `None` -> `"Unknown"`
  - `< 20` -> `"Very High"`
  - `< 50` -> `"High"`
  - `< 100` -> `"Moderate"`
  - `>= 100` -> `"Low"`
- Output type:
  - This endpoint uses a categorical noise score (`noise_level`) rather than numeric 0-100 score.

## 5.3 Outputs and usage
- Returned in API:
  - `noise_level`, `distance_to_road_m`, `source`, `api_used`, location context
- Persisted in DB:
  - `noise_scores.noise_level` and `distance_to_road`

## 6. Score inventory summary

1. Numeric scores:
   - `amenity composite_score` (0.0 to 1.0)
   - `transit_score` (5.0 to 100.0)
   - `flood_score` (discrete mapped values, higher is safer)
   - `crime safety_score` (0.0 to 100.0)
2. Categorical score:
   - `noise_level` (`Unknown`, `Very High`, `High`, `Moderate`, `Low`)
3. Not score-based:
   - `rent_estimate` endpoint returns rent values (estimation, not score)
   - education/income endpoints return census metrics (not score)
