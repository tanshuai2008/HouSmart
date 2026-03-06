# HouSmart Backend - Detailed Technical Reference

## 1. System Overview

This backend is a FastAPI application that exposes address-based intelligence APIs for:
- Education signal
- Income signal
- Amenity accessibility scoring
- Crime safety scoring
- Flood risk scoring
- Transit accessibility scoring
- Rent estimate
- Noise estimate
- Median property price

Primary app entrypoint:
- `backend/main.py`

Active routers mounted by `main.py`:
- `/api/health`
- `/api/education_level`
- `/api/median_income`
- `/api/amenity_score`
- `/api/crime_score`
- `/api/flood_risk_score`
- `/api/transit_score`
- `/api/rent_estimate`
- `/api/noise_estimate_score`
- `/api/median_property_price`

Also available:
- `/` root heartbeat message

## 2. Runtime Layers and Responsibilities

### 2.1 Route Layer (`app/api/routes`)
Responsibilities:
- Request validation via Pydantic models
- Calling service/core functions
- Mapping exceptions to HTTP status codes

### 2.2 Service/Core Layer (`app/services`, `app/core`)
Responsibilities:
- External API calls (Census, OSM, FEMA, FBI, Geocodio, RentCast)
- Scoring logic
- Caching logic
- Supabase read/write operations

### 2.3 Data/Schema Layer
- API input/output schemas: `app/api/schemas`
- SQL schema and DB function creation: `db/migrations/001_initial.sql`
- Migration runner: `app/scripts/apply_migrations.py`

## 3. Configuration and Environment

### 3.1 Settings Model (`app/core/config.py`)
Core env-backed settings include:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_KEY` / `SUPABASE_ANON_KEY`
- `CENSUS_API_KEY`
- Flood settings: FEMA endpoint/timeouts, flood cache TTL
- Transit settings: Overpass mirrors/timeouts, transit cache TTL
- Nominatim settings: URL + timeout

### 3.2 Supabase Clients
There are two active client modules:
- `app/core/supabase_client.py`: used by most endpoint services, reads Pydantic settings.
- `app/services/supabase_client.py`: used by rent/crime helper services and loader scripts, reads raw env and validates strictly.

Both target Supabase API access, but through different wrappers.

## 4. Database Objects and Why They Exist

Defined in `db/migrations/001_initial.sql`.

### 4.1 `geo_tract_metrics`
Purpose:
- Persistent tract-level cache for education and income outputs.

Columns used by code:
- `tract_geoid` (PK)
- `state_fips`, `county_fips`
- `median_income`
- `education_bachelor_pct`

Writes:
- Education endpoint upserts `education_bachelor_pct`
- Income endpoint upserts `median_income`

### 4.2 `flood_risk_cache`
Purpose:
- Cache flood computation payload by lat/lng cache key with expiry.

Columns:
- `key` (PK)
- `value` (jsonb)
- `expires_at`

### 4.3 `flood_zones`
Purpose:
- Durable storage of computed flood results by coordinate pair.

Columns:
- PK `(lat, lng)`
- `fld_zone`, `risk_label`, `flood_score`, `flood_data_unknown`, `source`

### 4.4 `transit_cache`
Purpose:
- Cache raw transit stop-derived scoring payloads by coordinate + radius.

Columns:
- `key` (PK)
- `value` (jsonb)
- `expires_at`

### 4.5 `transit_scores`
Purpose:
- Durable storage of transit score outputs.

Columns:
- PK `(property_lat, property_lng)`
- `radius_meters`, `bus_stop_count`, `rail_station_count`, `nearest_stop_meters`, `transit_score`, `source`

### 4.6 `noise_scores`
Purpose:
- Address-level noise result cache.

Columns:
- `address`, `latitude`, `longitude`, `distance_to_road`, `noise_level`

### 4.7 `redfin_median_prices`
Purpose:
- Market median sale-price dataset used by median-property-price endpoint.

Columns:
- `city`, `state`, `period`, `median_price`

### 4.8 `rent_estimate_cache`
Purpose:
- Hash-addressed rent estimate cache.

Columns:
- `request_hash` (PK)
- `address`, `request_payload`, `response_payload`, `updated_at_epoch`

### 4.9 `leaic_crosswalk`
Purpose:
- Maps place/county FIPS to law-enforcement ORI for crime endpoint.

Columns:
- `ori` (PK)
- `agency_name`, `agency_type`, `place_fips`, `county_fips`, `state_abbr`

### 4.10 `osm_poi_cache` + `count_pois(...)`
Purpose:
- Stores fetched OSM POIs with geography point.
- SQL function `count_pois` does radius-based POI counting using `ST_DWithin`.

This is mandatory for amenity scoring.

## 5. Endpoint-by-Endpoint Deep Dive

### 5.1 GET `/api/health`
Behavior:
- Returns static JSON:
  - `status: "ok"`
  - `service: "HouSmart Backend"`

Dependencies:
- None

Failure modes:
- None expected unless framework/runtime failure.

### 5.2 POST `/api/education_level`
Input model:
- `PropertyCreateRequest` with `address: str`

Execution flow:
1. `CensusService.get_education_by_address(address)`
2. Inside Census service:
- Geocode with US Census Geocoder (`get_location_data`)
- Resolve tract identifiers
- Query ACS 2024 (`B15003_001E`, `B15003_022E`)
- Compute `bachelor_percentage = bachelor_count / total_20_plus * 100`
- Round to 2 decimals
3. If no location match: returns null payload fields
4. If found: upsert tract metrics to `geo_tract_metrics`

DB write:
- Upserts `{tract_geoid, state_fips, county_fips, education_bachelor_pct}`

Output fields:
- `address`, `bachelor_percentage`, `state_fips`, `county_fips`, `tract_geoid`, `source`

### 5.3 POST `/api/median_income`
Input model:
- `PropertyCreateRequest` with `address: str`

Execution flow:
1. `CensusService.get_income_by_address(address)`
2. Internals:
- Geocode via Census Geocoder
- Query ACS 2024 variable `B19013_001E`
- Parse as integer median income
3. If no location match: returns null payload fields
4. Upsert to `geo_tract_metrics`

DB write:
- Upserts `{tract_geoid, state_fips, county_fips, median_income}`

Output fields:
- `address`, `median_income`, `currency`, `state_fips`, `county_fips`, `tract_geoid`, `source`

### 5.4 POST `/api/amenity_score`
Input model:
- `AddressRequest` with `address: str`

Execution flow:
1. Address geocoding via Census Geocoder (`CensusService.get_location_data`)
2. `POIService.compute_all_categories(lat, lng)`

POI service algorithm:
1. Calls DB function `count_pois` with a sentinel check (`amenity=school`, radius 2000m)
2. If 0 existing POIs in area:
- Fetch POIs from Overpass API via `OSMFetchService.fetch_all_pois`
- Normalize and insert rows into `osm_poi_cache`
3. For each category in `POI_CATEGORIES`, count POIs in category radius
4. Category score formula:
- `ratio = min(count / threshold, 1.0)`
- `score = round(ratio * weight, 4)`
5. `composite_score = round(sum(category_scores), 4)`

Current category definitions:
- education: weight 0.2, threshold 5, radius 2400m
- retail: weight 0.2, threshold 8, radius 1600m
- healthcare: weight 0.2, threshold 4, radius 3200m
- lifestyle: weight 0.2, threshold 10, radius 1600m
- transit: weight 0.2, threshold 6, radius 1200m

Output shape:
- `status: success`
- `data.<category>.count`
- `data.<category>.score`
- `data.composite_score`

### 5.5 POST `/api/crime_score`
Input model:
- `CrimeScoreRequest` with `address: str` (min length 3)

Execution flow:
1. `compute_crime_safety_score(address)`
2. `fetch_ori_metadata`:
- Geocode via Geocodio (`GeocodeClient`), retrieving census fields
- Extract `place_fips` and/or `county_fips`
- Resolve ORI in `leaic_crosswalk` using place first, county second
3. For each offense alias/code in mapping:
- Request FBI summarized agency data (`FbiCrimeDataClient.fetch_summarized_data`)
- Build breakdown entry with weighted rates

Offense aliases and FBI codes:
- violent_crime: V
- rape: RPE
- robbery: ROB
- aggravated-assault: ASS
- burglary: BUR
- larceny: LAR
- motor-vehicle-theft: MVT
- arson: ARS
- property_crime: P
- homicide: HOM

Weights:
- violent_crime 10.0, rape 9.5, robbery 8.0, aggravated-assault 7.0, burglary 6.0, larceny 3.0, motor-vehicle-theft 5.0, arson 6.0, property_crime 4.0, homicide 10.0

Rate processing:
- Detect local rate key as `<agency_name> Offenses` (fallback: first key ending with ` Offenses` excluding United States)
- Average positive numeric values for local and national series
- Per-offense weighted metrics:
  - `weighted_local_rate = local_avg * weight`
  - `weighted_national_rate = national_avg * weight`
- Aggregate:
  - `local_crime_index = sum(weighted_local_rate)`
  - `national_crime_index = sum(weighted_national_rate)`
  - `relative_crime_ratio = local_crime_index / national_crime_index`

Safety score formula:
- `raw = 100 * exp(-0.75 * relative_crime_ratio)`
- Clamp to `[0,100]`

Safety category:
- `Green` if score > 75
- `Yellow` if score >= 40
- `Red` otherwise

No-data behavior:
- If no valid offense breakdowns or invalid national index:
  - `data_available = false`
  - `safety_score = 0`
  - `safety_category = "No Data"`

### 5.6 POST `/api/flood_risk_score`
Input model:
- `AddressFloodRequest` with `address: str`, min length 5

Execution flow:
1. Async geocode via Nominatim (`geocoding_service.geocode_address`) => `(lat,lng)`
2. `save_flood_zone_to_db(lat,lng)`
3. `get_flood_zone(lat,lng)`:
- Cache lookup in `flood_risk_cache` with key `flood:{lat:.5f}:{lng:.5f}` and expiry filter
- If miss: query FEMA NFHL endpoint (`FLD_ZONE`, `ZONE_SUBTY`)
- Normalize X+0.2 subtype to `X500`
- If FEMA call fails: deterministic geographic mock zone fallback
4. Map FEMA zone to label + score using `FLOOD_ZONE_MAP`
5. Upsert row into `flood_zones` by conflict `(lat,lng)`

Zone-to-score mapping currently used:
- Very high/high zones (A/AE/AO/AH/A99/AR/VE/V): scores 10-30
- Moderate zones (X500/B): score 60
- Minimal zones (X/C): score 95
- Unknown (D): score 50

Derived booleans:
- `in_flood_zone`: zone in `{A,AE,AO,AH,A99,AR,VE,V}`
- `in_moderate_zone`: zone in `{X500,B}`

### 5.7 POST `/api/transit_score`
Input model:
- `AddressTransitRequest`
- `address: str`
- `radius_meters: int` (default 800, min 100, max 5000)

Execution flow:
1. Async geocode via Nominatim -> `(lat,lng)`
2. `save_transit_score_to_db(lat,lng,radius)`
3. `fetch_transit_stops(lat,lng,radius)`:
- Cache lookup key: `transit:{lat:.4f}:{lng:.4f}:{radius}` in `transit_cache`
- If miss: query Overpass mirrors in configured order
- Parse stops and classify types

Transit parsing details:
- Rail when `tags.railway in {station, subway_entrance, halt}`
- Otherwise counted as bus
- Nearest stop computed by haversine distance in meters

Transit score rubric:
- Base score starts at 5
- First matching tuple in rubric `(min_bus, min_rail, score)` applies:
  - (20,2)->95
  - (15,1)->85
  - (10,1)->75
  - (8,0)->65
  - (5,0)->50
  - (3,0)->35
  - (1,0)->20
  - (0,0)->5
- If `rail_count > 0`, add +15, cap at 100

Persistence:
- Upsert to `transit_scores` on `(property_lat,property_lng)`

### 5.8 POST `/api/rent_estimate`
Input model:
- `RentEstimateRequest` with `address: str`

Execution flow:
1. `fetch_rent_estimate(address)`
2. Build validated request payload
3. Build deterministic hash (`sha256` of canonical JSON payload)
4. Cache lookup in `rent_estimate_cache` using `request_hash`
5. On miss: call RentCast AVM endpoint
6. Normalize output into:
- `rent`, `rent_range_low`, `rent_range_high`, `currency`, `address`, `subject_property`, `comparables`
7. Upsert payload into cache table

TTL:
- `RENT_CACHE_TTL_SECONDS`, default 6 hours

### 5.9 POST `/api/noise_estimate_score`
Input model:
- `AddressRequest` with `address: str`

Execution flow:
1. Sync Nominatim geocoding (`app/services/geocode.py`) -> `(lat,lon,city,state)`
2. Cache lookup in `noise_scores` by exact `address`
3. If miss:
- Query Overpass for highways within 200m
- Iterate way geometry points
- Compute minimum haversine distance to any road point
- Classify noise level

Noise classification thresholds:
- distance is None -> `Unknown`
- `< 20m` -> `Very High`
- `< 50m` -> `High`
- `< 100m` -> `Moderate`
- otherwise -> `Low`

Persistence:
- Insert into `noise_scores`

### 5.10 POST `/api/median_property_price`
Input model:
- `AddressRequest` with `address: str`

Execution flow:
1. Geocode via Nominatim (`app/services/geocode.py`) to get city/state
2. Query `redfin_median_prices` by city/state (ILIKE variants)
3. If table empty, auto-run Redfin ingest script (`ingest_redfin()`)
4. Return latest record by `period desc`

City normalization strategy:
- Tries variants like `Saint`/`St.` and removal of `City of` prefix

## 6. Error Handling and Failure Characteristics

- Route-level handlers convert expected domain errors to HTTP status in crime/rent/flood/transit/noise/median modules.
- Census routes do less exception wrapping and can return raw 500s for upstream failures.
- Flood/transit include cache layers with TTL expiry checks.
- Amenity depends on Overpass availability and DB SQL function `count_pois`.

## 7. Cache Keys and Expiration

- Flood cache key: `flood:{lat:.5f}:{lng:.5f}`
- Transit cache key: `transit:{lat:.4f}:{lng:.4f}:{radius}`
- Rent cache key: SHA-256 of normalized request payload JSON
- Noise cache: direct by exact address row match

TTL controls:
- `FLOOD_CACHE_TTL_SECONDS` default: 180 days
- `TRANSIT_CACHE_TTL_SECONDS` default: 30 days
- `RENT_CACHE_TTL_SECONDS` default: 6 hours

## 8. Data Loading Prerequisites

### 8.1 Crime endpoint prerequisite
`leaic_crosswalk` must be populated. Loader:
- `python -m app.services.leaic_crosswalk_loader --tsv_path <path>`

### 8.2 Median price endpoint prerequisite
`redfin_median_prices` should be populated. Service auto-ingests if empty, but preloading is preferred:
- `python app/scripts/ingest_redfin.py`

### 8.3 Migrations
Run before app start in a fresh environment:
- `python app/scripts/apply_migrations.py`

## 9. External API Dependency Matrix

- Education/Income/Amenity geocoding: US Census Geocoder
- Education/Income metrics: Census ACS
- Amenity POIs: OSM Overpass
- Crime geocoding: Geocodio
- Crime rates: FBI CDE
- Flood geocoding: Nominatim
- Flood zones: FEMA NFHL
- Transit geocoding: Nominatim
- Transit stops: OSM Overpass mirrors
- Rent: RentCast
- Noise geocoding + roads: Nominatim + Overpass
- Median price geocoding: Nominatim

## 10. DB Touch Matrix by Endpoint

- `/education_level`: `geo_tract_metrics` (upsert)
- `/median_income`: `geo_tract_metrics` (upsert)
- `/amenity_score`: `osm_poi_cache` (insert/read) + `count_pois` RPC
- `/crime_score`: `leaic_crosswalk` (read)
- `/flood_risk_score`: `flood_risk_cache` (read/upsert), `flood_zones` (upsert)
- `/transit_score`: `transit_cache` (read/upsert), `transit_scores` (upsert)
- `/rent_estimate`: `rent_estimate_cache` (read/upsert)
- `/noise_estimate_score`: `noise_scores` (read/insert)
- `/median_property_price`: `redfin_median_prices` (read; ingest flow writes)
