# HouSmart (Integration)

This repository contains a FastAPI backend (under `backend/`) and a Next.js frontend (under `frontend/`).

The `kpi-dashboard-integration` branch merges feature branches into a single backend so the dashboard can call real APIs.

## Backend Endpoints

- `GET /`
  Root status message.
- `GET /api/health`
  Health check.

- `GET /api/median-house-price?city=<city>&state=<state>`
  Latest city-level median sale price (Redfin).
- `GET /api/noise-estimate/address?address=<full_address>`
  Noise score/level by address.
- `GET /api/noise-estimate/coordinates?lat=<lat>&lon=<lon>`
  Noise score/level by coordinates.
- `GET /api/road-map?place=<city_or_area>`
  Road-network summary for a place.

- `POST /api/median-income`
  Median household income by address (US Census ACS).
- `POST /api/education-level`
  Education level (e.g. bachelor %) by address (US Census ACS).

- `POST /evaluation/amenity-score`
  Amenity scores by latitude/longitude.
- `GET /evaluation/{property_id}/location-intelligence`
  Amenity scores for a stored property.

- `POST /properties`
  Create a property record from an address (used by evaluation flow).

## Environment Variables

File: `backend/.env`

- `HOUSMART_REDFIN_DATA_URL` (if using parquet-based median price)
- `HOUSMART_NOMINATIM_URL`, `HOUSMART_OVERPASS_URL`, and related timeouts/user-agents (noise/road-map)
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (census/property/POI persistence)

## Run Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

```
backend/app/scripts/ingest_redfin.py
```

---

## Storage Layer

Database: **Supabase**

Table:

```
redfin_median_prices
```

Queried by:

```
backend/app/services/median_house_price.py
```

---

# Time Period of the Data

The system always uses the **latest available `PERIOD_END`** from the Redfin dataset.

During ingestion:

- Only the **latest snapshot** is stored
- The full historical time-series is **not kept**

---

# Environment Variables

File:

```
backend/.env
```

Required variables:

```
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
HOUSMART_REDFIN_DATA_URL=
```

Loaded by:

```
backend/app/config/db.py
```

---

# Key Files

```
backend/main.py
backend/app/api/routes/median_house_price.py
backend/app/services/median_house_price.py
backend/app/services/geocode.py
backend/app/scripts/ingest_redfin.py
```

---

# Running the Backend

```powershell
cd backend

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

python -m uvicorn main:app --reload
```

---

<<<<<<< HEAD
- The merged backend is intended for dashboard integration; individual feature branches may also run standalone.
- Noise and road-map APIs use OpenStreetMap data through Nominatim/Overpass.
=======
# Assumptions / Limitations

- **US-only**
  - Geocoding restricted to US addresses.
  - Redfin dataset used here is US-focused.

- **City-level metric**
  - Returns **city median sale price**, not neighborhood/ZIP/block or property-level estimate.

- **Canonical Redfin slice**
  - Ingestion filters:
    - `REGION_TYPE = place`
    - `PROPERTY_TYPE = All Residential`
    - latest `PERIOD_END`

- **Geocoder variability**
  - Some addresses may fail to geocode depending on formatting or Nominatim rate limits.

- **City matching risk**
  - City/state lookups are case-insensitive and may return a nearby match if naming differs.

- **Supabase credentials required**
  - Must set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.

---

# Other Notes

- On first run (or if the table is empty), the service **automatically triggers ingestion** to populate the Supabase table.
- Internet access is required during ingestion.
- CLI logging is suppressed to maintain the strict **two-line output format**.
>>>>>>> origin/Kevin_MedianHousePrice
