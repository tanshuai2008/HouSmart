# Flood Risk Score Service

Standalone backend service for HouSmart Variable 10 (Flood Risk Score).

## What This Service Does

This service evaluates flood risk at property coordinates using FEMA NFHL data:

- Queries FEMA flood zones for coordinates
- Maps flood zone to risk label + score (0-100)
- Checks flood status for a specific property
- Bulk checks flood status for all properties
- Stores results in Supabase tables
- Caches flood lookup results in Supabase (`flood_risk_cache`)

## Backend Structure

- `backend/main.py` - uvicorn entrypoint
- `backend/app/main.py` - FastAPI app and router registration
- `backend/app/api/routes/flood.py` - Flood endpoints
- `backend/app/api/schemas/flood.py` - Request/response models
- `backend/app/services/flood_service.py` - FEMA integration + scoring + cache
- `backend/app/core/config.py` - Environment settings
- `backend/app/core/supabase_client.py` - Supabase client

## Environment

Create or update `backend/.env`:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_or_service_key

FLOOD_CACHE_TTL_SECONDS=15552000
FEMA_QUERY_URL=https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query
FEMA_HTTP_TIMEOUT_SECONDS=15
FEMA_DEBUG_TIMEOUT_SECONDS=30
HTTP_USER_AGENT=Mozilla/5.0 (compatible; HouSmart/1.0)
```

## Install and Run

From `FloodRiskScore/backend`:

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

### Flood

- `POST /flood/import`
  - Body: `{ "lat": 29.7604, "lng": -95.3698 }`
  - Stores lookup in `flood_zones` (upsert on `lat,lng`)

- `GET /flood/check?lat=29.7604&lng=-95.3698`
  - Returns flood zone, label, and flood score without DB write

- `GET /flood/check/property/{property_id}`
  - Looks up property from `properties`, evaluates flood risk

- `GET /flood/check/all-properties`
  - Evaluates flood risk for all properties and returns summary counts

- `GET /flood/debug-fema?lat=29.7604&lng=-95.3698`
  - Returns raw FEMA response (debug only)

## Scoring Summary

Flood score mapping follows FEMA zone classes (examples):

- `VE`, `V` -> very high risk (low safety score)
- `AE`, `A` -> high risk
- `X500`, `B` -> moderate risk
- `X`, `C` -> minimal risk (high safety score)
- `D` -> undetermined

## Required Supabase Tables

- `properties` (`id`, `formatted_address`, `latitude`, `longitude`)
- `flood_zones`
- `flood_risk_cache`

## Notes

- FEMA can be blocked from some non-US networks.
- This service includes a geographic fallback mock when FEMA is unreachable.
- If cache read/write fails, the service still continues with live API lookup.
