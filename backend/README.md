# HouSmart — Transit & Flood Risk Pipeline

> **Assigned to:** Boukhelkhal Imene
> **Variables:** 9 (Transit Score) · 10 (Flood Risk)
> **Branches:** `feature/transit-stop-import` · `feature/flood-polygon-import` · `feature/transit-distance-calculation` · `feature/property-flood-intersect`

---

## Overview

This module implements the **Transit Score** and **Flood Risk** data pipelines for the HouSmart property evaluation dashboard. It covers 4 tasks:

| # | Task | Endpoint | Status |
|---|---|---|---|
| 1 | Import transit stop locations | `POST /transit/import-stops` | ✅ Done |
| 2 | Import FEMA flood polygons into DB | `POST /flood/import` | ✅ Done |
| 3 | Calculate distance to nearest transit stop per property | `GET /transit/score/property/{id}` | ✅ Done |
| 4 | Check which properties intersect flood zones | `GET /flood/check/property/{id}` · `GET /flood/check/all-properties` | ✅ Done |

---

## Data Sources

| Variable | Source | Cost | Auth |
|---|---|---|---|
| Transit stops | OpenStreetMap Overpass API (3 mirror fallbacks) | FREE | None |
| Flood zones | FEMA National Flood Hazard Layer (NFHL) | FREE | None |

> **Note on FEMA API:** FEMA blocks non-US IP addresses. A geographic mock is used for local development outside the US. The code always tries the real FEMA API first — if it fails it falls back to the mock automatically. Production on Render (US servers) will use real FEMA data with no code or config changes needed.

---

## File Structure

```
backend/app/
├── api/
│   ├── routes/
│   │   ├── transit.py          # Transit endpoints
│   │   └── flood.py            # Flood endpoints
│   └── schemas/
│       ├── transit.py          # Pydantic request/response models
│       └── flood.py            # Pydantic request/response models
└── services/
    ├── transit_service.py      # OSM Overpass, Haversine distance, scoring, caching
    └── flood_service.py        # FEMA API, zone mapping, scoring, caching

workers/                        # Celery background tasks (pipeline integration)
├── celery_app.py
└── tasks/
    ├── transit_tasks.py
    └── flood_tasks.py
```

---

## Database Tables

### `transit_stops`
Stores all OSM transit stop locations imported within a radius.

```sql
CREATE TABLE transit_stops (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    osm_id TEXT UNIQUE NOT NULL,
    name TEXT,
    stop_type TEXT,       -- bus_stop, station, subway_entrance, tram_stop
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### `transit_scores`
Stores computed transit score per property location.

```sql
CREATE TABLE transit_scores (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    property_lat DOUBLE PRECISION NOT NULL,
    property_lng DOUBLE PRECISION NOT NULL,
    radius_meters INTEGER DEFAULT 800,
    bus_stop_count INTEGER,
    rail_station_count INTEGER,
    nearest_stop_meters DOUBLE PRECISION,
    transit_score DOUBLE PRECISION,     -- 0-100
    source TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (property_lat, property_lng)
);
```

### `flood_zones`
Stores FEMA flood zone classification per property location.

```sql
CREATE TABLE flood_zones (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    fld_zone TEXT,               -- AE, X, VE, etc.
    risk_label TEXT,
    flood_score DOUBLE PRECISION,    -- 0-100 (100 = safest)
    flood_data_unknown BOOLEAN DEFAULT FALSE,
    source TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (lat, lng)
);
```

### `transit_cache`
Supabase cache for Variable 9 transit data. TTL: 30 days.

```sql
CREATE TABLE transit_cache (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_transit_cache_expires ON transit_cache (expires_at);
```

### `flood_risk_cache`
Supabase cache for Variable 10 flood data. TTL: 180 days.

```sql
CREATE TABLE flood_risk_cache (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX idx_flood_risk_cache_expires ON flood_risk_cache (expires_at);
```

---

## Scoring Logic

### Transit Score (0–100)
Default radius: **800m** (WMATA/APTA walkable transit standard). Rail stations give +15 bonus.

| Bus Stops | Rail Stations | Score |
|---|---|---|
| 20+ | 2+ | 100 |
| 10+ | 1+ | 90 |
| 8+ | 0 | 65 |
| 5+ | 0 | 50 |
| 1+ | 0 | 20 |
| 0 | 0 | 5 |

### Flood Score (0–100)

| FEMA Zone | Risk | Score |
|---|---|---|
| VE, V | Very High — Coastal | 10 |
| AE, A | High — 1% Annual Chance | 20 |
| AO, AH | High — Shallow Flooding | 25 |
| X500, B | Moderate | 60 |
| X, C | Minimal | 95 |
| D | Undetermined | 50 |

---

## Caching (Supabase)

Caching is handled directly inside `transit_service.py` and `flood_service.py` using two dedicated Supabase tables — no Redis required.

| Table | Variable | TTL | Reason |
|---|---|---|---|
| `transit_cache` | Transit Score | 30 days | Transit infrastructure changes slowly |
| `flood_risk_cache` | Flood Risk | 180 days | FEMA maps updated infrequently |

Cache failures are caught and logged — the app falls through to the real API if the cache is unavailable.

---

## API Endpoints

### Transit

#### `POST /transit/import-stops`
Fetches all transit stops within a radius from OSM and saves them to the `transit_stops` table.

**Request:**
```json
{ "lat": 47.6062, "lng": -122.3321, "radius_meters": 800 }
```
**Response:**
```json
{
  "status": "success",
  "data": {
    "inserted": 247,
    "transit_score": 100,
    "bus_stops": 227,
    "rail_stations": 20,
    "nearest_stop_meters": 49.7
  }
}
```

---

#### `GET /transit/score/property/{property_id}`
Looks up a property from the `properties` table, computes transit distance and score, saves to `transit_scores`.

**Example:**
```
GET /transit/score/property/54ac71d9-8d0c-4c81-bfef-67d8bb1dd9d1
```
**Response:**
```json
{
  "status": "success",
  "data": {
    "property_id": "54ac71d9-...",
    "property_address": "1600 PENNSYLVANIA AVE NW, WASHINGTON, DC, 20500",
    "nearest_stop_meters": 131.1,
    "transit_score": 100,
    "bus_stop_count": 116,
    "rail_station_count": 23,
    "source": "OpenStreetMap (Overpass API)"
  }
}
```

---

### Flood Risk

#### `POST /flood/import`
Queries FEMA NFHL API for a lat/lng and saves the flood zone to `flood_zones` table.

**Request:**
```json
{ "lat": 29.7604, "lng": -95.3698 }
```
**Response:**
```json
{
  "status": "success",
  "data": {
    "fld_zone": "AE",
    "risk_label": "High Risk — 1% Annual Chance",
    "flood_score": 20,
    "flood_data_unknown": false
  }
}
```

---

#### `GET /flood/check/property/{property_id}`
Looks up property coordinates and returns its FEMA flood zone classification.

**Response:**
```json
{
  "status": "success",
  "data": {
    "property_address": "1000 MAIN ST, HOUSTON, TX, 77002",
    "fld_zone": "AE",
    "risk_label": "High Risk — 1% Annual Chance",
    "flood_score": 20,
    "in_flood_zone": true,
    "in_moderate_zone": false
  }
}
```

---

#### `GET /flood/check/all-properties`
Scans all properties in DB and returns a flood risk summary.

**Response:**
```json
{
  "status": "success",
  "data": {
    "total": 18,
    "high_risk_count": 1,
    "moderate_risk_count": 0,
    "minimal_risk_count": 17,
    "skipped_count": 0,
    "results": [...]
  }
}
```

---

## Running Locally

```bash
# Terminal 1 — Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload
# Swagger UI → http://127.0.0.1:8000/docs

# Terminal 2 — Celery workers
cd HouSmart && source backend/venv/bin/activate
celery -A workers.celery_app worker --loglevel=info
```

> Redis is no longer required locally. Caching is handled via Supabase.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Invalid lat/lng (e.g. `lat=999`) | `422` with clear message |
| Invalid radius (e.g. `99999m`) | `422` with clear message |
| Property not found | `404` |
| Overpass timeout | Auto-retries across 3 mirror servers |
| FEMA blocked (non-US IP) | Falls back to geographic mock |
| Duplicate DB insert | Handled via `upsert on_conflict` |
| Cache unavailable | Caught and logged, falls through to API |
| Property missing coordinates | Skipped gracefully in bulk scan |

---

## Known Limitations

- **FEMA API** is blocked from non-US IP addresses. A geographic mock is used for local development. Production deployment on Render (US) will use real FEMA data automatically — no config changes needed.
- **Overpass API** can time out under heavy load. Three mirror servers are tried in sequence as fallback.
- Transit score uses **stop count proxy** for MVP. Post-MVP improvement: parse `stop_times.txt` from GTFS feeds to compute average headways for more accurate service quality scoring.