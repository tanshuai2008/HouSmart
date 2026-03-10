# HouSmart Backend

This repository contains a FastAPI backend (under `backend/`) and a Next.js frontend (under `frontend/`).

Feature branches contribute additional API routes/services. The `kpi-dashboard-integration` branch is intended to merge these features into a single backend so the dashboard can call real APIs.

## Backend Endpoints

- `GET /`  
  Root status message.
- `GET /api/health`  
  Health check.
- `GET /api/median-house-price?city=<city>&state=<state>`  
  Returns latest median sale price from the Redfin parquet dataset.
- `GET /api/noise-estimate/address?address=<full_address>`  
  Geocodes address and returns noise score/level.
- `GET /api/noise-estimate/coordinates?lat=<lat>&lon=<lon>`  
  Returns noise score/level by coordinates.
- `GET /api/road-map?place=<city_or_area>`  
  Returns road-network summary for the place.

## Environment Variables

File: `backend/.env`

- `HOUSMART_REDFIN_DATA_URL`  
  Redfin parquet dataset URL.
- `HOUSMART_NOMINATIM_URL`
- `HOUSMART_OVERPASS_URL`
- `HOUSMART_NOISE_USER_AGENT`
- `HOUSMART_NOMINATIM_TIMEOUT`
- `HOUSMART_OVERPASS_TIMEOUT`
- `HOUSMART_ROADMAP_USER_AGENT`
- `HOUSMART_ROADMAP_TIMEOUT`

## Key Files

- `backend/main.py`
- `backend/app/api/routes/median_house_price.py`
- `backend/app/services/median_house_price.py`
- `backend/app/api/routes/noise_estimator.py`
- `backend/app/services/noise_estimator.py`
- `backend/app/api/routes/road_map.py`
- `backend/app/services/road_map.py`
- `backend/app/utils/cache_utils.py`
- `backend/median_price_cache.json`

## Run Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

## Notes

- The merged backend is intended for dashboard integration; individual feature branches may also run standalone.
- Noise and road-map APIs use OpenStreetMap data through Nominatim/Overpass.
