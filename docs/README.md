# MedianHousePrice Module

This folder is a standalone extraction from `KevinVariables` for the median house price feature only.

## What Was Changed

1. The original combined backend in `KevinVariables` contained multiple APIs (median house price, noise score, road map).
2. Median-house-price route and service were copied into this module.
3. `main.py` was updated to include only:
   - `health` route
   - `median_house_price` route
4. A module-specific `.env` was created with only Redfin dataset config.
5. Module-specific backend dependencies were reduced to median-related packages.

## Backend Endpoints

- `GET /`  
  Root status message.
- `GET /api/health`  
  Health check.
- `GET /api/median-house-price?city=<city>&state=<state>`  
  Returns latest median sale price from Redfin parquet dataset.

## Environment Variables

File: `backend/.env`

- `HOUSMART_REDFIN_DATA_URL`  
  Redfin parquet dataset URL.

## Key Files

- `backend/main.py`
- `backend/app/api/routes/median_house_price.py`
- `backend/app/services/median_house_price.py`
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

- This module is designed to run independently from `KevinVariables` and `NoiseScore`.
- Cache file is shared format-compatible with the original implementation.