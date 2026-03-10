# HouSmart (Integration)

This repository contains a FastAPI backend (under `backend/`) and a Next.js frontend (under `frontend/`).

The `kpi-dashboard-integration` branch merges feature branches into a single backend so the dashboard can call real APIs.

## Backend Endpoints (current)

- `GET /` and `GET /api/health`

- `GET /api/median-house-price?city=<city>&state=<state>`
- `GET /api/noise-estimate/address?address=<full_address>`
- `GET /api/noise-estimate/coordinates?lat=<lat>&lon=<lon>`
- `GET /api/road-map?place=<city_or_area>`

- `POST /api/median-income`
- `POST /api/education-level`

- `POST /api/crime-score/`

- `POST /evaluation/amenity-score`
- `GET /evaluation/{property_id}/location-intelligence`
- `POST /properties`

- Transit:
  - `POST /transit/score/address`
  - `GET /transit/score?lat=<lat>&lng=<lng>&radius_meters=800`
  - `GET /transit/score/property/{property_id}`
  - `POST /transit/import-stops`

## Run Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload
```
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
>>>>>>> origin/Imene_TransitScore
