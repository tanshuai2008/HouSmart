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

- Flood:
  - `POST /flood/check/address`
  - `POST /flood/import`
  - `GET /flood/check?lat=<lat>&lng=<lng>`
  - `GET /flood/check/property/{property_id}`
  - `GET /flood/check/all-properties`

## Run Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload
```
