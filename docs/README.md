# Transit Score Service

Standalone backend service for HouSmart Variable 9 (Transit Score).

## What This Service Does

This service calculates transit accessibility using OpenStreetMap Overpass data:

- Imports nearby transit stops around a coordinate
- Computes distance to nearest stop
- Generates a 0-100 transit score
- Stores results in Supabase tables
- Caches API results in Supabase (`transit_cache`)

## Backend Structure

- `backend/main.py` - uvicorn entrypoint
- `backend/app/main.py` - FastAPI app and router registration
- `backend/app/api/routes/transit.py` - Transit endpoints
- `backend/app/api/schemas/transit.py` - Request/response models
- `backend/app/services/transit_service.py` - Core scoring + Overpass integration + cache
- `backend/app/core/config.py` - Environment settings
- `backend/app/core/supabase_client.py` - Supabase client

## Environment

Create or update `backend/.env`:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_or_service_key

TRANSIT_CACHE_TTL_SECONDS=2592000
OVERPASS_HTTP_TIMEOUT_SECONDS=30
OVERPASS_QUERY_TIMEOUT_SECONDS=25
OVERPASS_MIRRORS=https://overpass-api.de/api/interpreter,https://overpass.kumi.systems/api/interpreter,https://maps.mail.ru/osm/tools/overpass/api/interpreter
```

## Install and Run

From `TransitScore/backend`:

```powershell
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

Swagger docs:

- `http://127.0.0.1:8000/docs`

## API Endpoints

### Health

- `GET /api/health`

### Transit

- `POST /transit/import-stops`
  - Body: `{ "lat": 47.6062, "lng": -122.3321, "radius_meters": 800 }`
  - Imports transit stops into `transit_stops` (upsert on `osm_id`)

- `GET /transit/score?lat=47.6062&lng=-122.3321&radius_meters=800`
  - Calculates transit score for lat/lng
  - Saves into `transit_scores` (upsert on `property_lat,property_lng`)

- `GET /transit/score/property/{property_id}?radius_meters=800`
  - Reads property coordinates from `properties`
  - Calculates and stores transit score for that property

## Scoring Summary

Transit score is based on counts of nearby bus + rail stops in radius (default 800m), with bonus for rail presence. Final score range is 0-100.

## Required Supabase Tables

- `properties` (`id`, `formatted_address`, `latitude`, `longitude`)
- `transit_stops`
- `transit_scores`
- `transit_cache`

## Notes

- Overpass mirrors are tried in sequence for reliability.
- If cache read/write fails, the service still continues with live API fetch.
