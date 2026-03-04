# MedianHousePrice Module

This folder is a **standalone extraction from `KevinVariables`** containing only the **Median House Price backend service**.

The module was separated so the **median price logic can run independently** without the Noise Score or Road Map APIs.

---

# Median House Price (Backend Service)

## What it does

The **Median House Price** service returns the **latest available city-level median sale price** for the city/state that a given address resolves to.

This is **not a property appraisal**.  
It provides the **market-level median house price for the surrounding city**.

---

# What Was Changed

1. The original `KevinVariables` backend contained multiple APIs:
   - Median House Price
   - Noise Score
   - Road Map services

2. The **Median House Price logic was extracted into this standalone module**.

3. The backend was simplified so `main.py` includes only:
   - `health` route
   - `median_house_price` route

4. A **module-specific `.env` file** was created with only the required configuration.

5. Backend dependencies were **reduced to only median-price related packages**.

6. The service now queries **Redfin median sale price data stored in Supabase**.

---

# Backend Endpoints

### Root
```
GET /
```

Returns service status.

---

### Health Check
```
GET /api/health
```

Used to confirm the backend is running correctly.

---

### Median House Price
```
GET /api/median-house-price?city=<city>&state=<state>
```

Returns the **latest median sale price** for the specified city and state.

Example:

```
/api/median-house-price?city=Charlotte&state=North Carolina
```

---

# CLI Usage

You can also run the service **directly from the command line**.

From the repo root:

```
cd backend
python -m app.services.median_house_price "<full address>"
```

Example:

```
python -m app.services.median_house_price "100 N Tryon St, Charlotte, North Carolina"
```

---

# Input Format

A **single address string**.

Example:

```
"100 N Tryon St, Charlotte, North Carolina"
```

---

# Output Format

The CLI prints **exactly two lines**:

```
place:- <input address>
median house price:- <integer price>
```

Example:

```
place:- 100 N Tryon St, Charlotte, North Carolina
median house price:- 387000
```

---

# Error Case

If the address cannot be resolved or no data exists, the service prints:

```
place:- <input address>
median house price:-
```

The program exits with a **non-zero status code**.

---

# APIs / Data Sources Used

## Geocoding

OpenStreetMap **Nominatim API**

Used to convert an address into:

```
(latitude, longitude, city, state)
```

Implementation:

```
backend/app/services/geocode.py
```

Restriction:

```
countrycodes=us
```

---

## Median Price Dataset

Source: **Redfin Data Center**

Dataset:

```
city_market_tracker.tsv000.gz
```

Downloaded and processed by:

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
