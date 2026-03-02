# NoiseScore Module

This folder is a standalone extraction from `KevinVariables` for noise-related features.

## What Was Changed

1. The original combined backend in `KevinVariables` contained multiple APIs.
2. Noise estimator route and service were copied into this module.
3. Road-map route and service were added to this module as requested.
4. `main.py` was updated to include only:
   - `health` route
   - `noise_estimator` route
   - `road_map` route
5. A module-specific `.env` was created with OSM/Nominatim and road-map settings.
6. Module-specific backend dependencies were reduced to noise/road-map packages.

## Backend Endpoints

- `GET /`  
  Root status message.
- `GET /api/health`  
  Health check.
- `GET /api/noise-estimate/address?address=<full_address>`  
  Geocodes address and returns noise score/level.
- `GET /api/noise-estimate/coordinates?lat=<lat>&lon=<lon>`  
  Returns noise score/level by coordinates.
- `GET /api/road-map?place=<city_or_area>`  
  Returns road-network summary for the place.

## Environment Variables

File: `backend/.env`

- `HOUSMART_NOMINATIM_URL`
- `HOUSMART_OVERPASS_URL`
- `HOUSMART_NOISE_USER_AGENT`
- `HOUSMART_NOMINATIM_TIMEOUT`
- `HOUSMART_OVERPASS_TIMEOUT`
- `HOUSMART_ROADMAP_USER_AGENT`
- `HOUSMART_ROADMAP_TIMEOUT`

## Key Files

- `backend/main.py`
- `backend/app/api/routes/noise_estimator.py`
- `backend/app/services/noise_estimator.py`
- `backend/app/api/routes/road_map.py`
- `backend/app/services/road_map.py`
- `backend/app/utils/cache_utils.py`

## Run Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

## Notes

- This module is designed to run independently from `KevinVariables` and `MedianHousePrice`.
- Noise and road-map APIs both use OpenStreetMap data through Nominatim/Overpass.