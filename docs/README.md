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

- `POST /api/rent-estimate`

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

## What it does

The **Noise Estimator** service estimates a simple **road-noise proxy** for a property using OpenStreetMap data.

The process works as follows:

1. The input address is geocoded into `(lat, lon, city, state)` using OpenStreetMap **Nominatim**.
2. The system queries OpenStreetMap **Overpass API** to find nearby roads tagged as `highway`.
3. The **nearest distance to a road** is calculated in meters using the Haversine formula.
4. The distance is converted into a **noise level classification**.
5. The result is stored in **Supabase** so that repeated queries return instantly from cache.

> This is a heuristic based on road proximity and does **not represent actual sound pressure levels (dB).**

---

# Noise Level Classification

Noise level is determined based on **distance to the nearest road**.

| Distance to Road | Noise Level |
|------------------|-------------|
| `< 20 m` | Very High |
| `< 50 m` | High |
| `< 100 m` | Moderate |
| `>= 100 m` | Low |
| `None` | Unknown |

---

# Example Output

Successful response:

```
{
 'address': '1 Apple Park Way, Cupertino, CA',
 'city': 'Cupertino',
 'state': 'CA',
 'noise_level': 'Moderate',
 'distance_to_road_m': 72.5,
 'source': 'OpenStreetMap'
}
```

If the result already exists in Supabase:

```
{
 'noise_level': 'Moderate',
 'distance_to_road_m': 72.5,
 'source': 'Supabase Cache'
}
```

---

# Error Responses

Possible error responses include:

```
{'error': 'Address required'}
```

```
{'error': 'Address not found'}
```

---

# APIs and Data Sources

## Geocoding
**OpenStreetMap Nominatim API**

Used to convert addresses into latitude and longitude.

Implemented in:

```
backend/app/services/geocode.py
```

Requests are restricted to:

```
countrycodes=us
```

---

## Road Data
**OpenStreetMap Overpass API**

Endpoint:

```
https://overpass-api.de/api/interpreter
```

Used to query nearby road geometries tagged with `highway`.

Implemented in:

```
backend/app/services/noise_estimator.py
```

---

# Caching (Supabase)

Noise estimation results are cached in **Supabase** to avoid repeated API calls.

Table used:

```
noise_scores
```

Cache key:

```
address
```

If a cached record is found, the response includes:

```
source: "Supabase Cache"
```

---

# Environment Variables

File:

```
backend/.env
```

Required variables:

```
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY

HOUSMART_NOMINATIM_URL
HOUSMART_OVERPASS_URL
HOUSMART_NOISE_USER_AGENT
HOUSMART_NOMINATIM_TIMEOUT
HOUSMART_OVERPASS_TIMEOUT
HOUSMART_ROADMAP_USER_AGENT
HOUSMART_ROADMAP_TIMEOUT
```

---

# Key Files

```
backend/main.py
backend/app/api/routes/noise_estimator.py
backend/app/services/noise_estimator.py
backend/app/api/routes/road_map.py
backend/app/services/road_map.py
backend/app/utils/cache_utils.py
```

---

# Running the Backend

```powershell
cd backend
python -m venv venv
## Manual Test (cURL)

```bash
curl -X POST "http://127.0.0.1:8000/api/rent-estimate" \
  -H "Content-Type: application/json" \
  -d "{\"address\":\"1300 N St Nw, Washington, DC 20005\",\"property_type\":\"single family\",\"bedrooms\":0,\"bathrooms\":1,\"square_footage\":655}"
```

<<<<<<< HEAD
## Related Docs

- `docs/rent_estimation_overview.md`
- `docs/sql_query.md`

>>>>>>> origin/Jhanvi_RentEstimation
=======
The API server will start locally and expose the NoiseScore endpoints.

---

# Assumptions and Limitations

- **US-only geocoding**: Nominatim requests are restricted to US addresses.
- **Rate limits**: OpenStreetMap Nominatim and Overpass APIs may rate-limit or fail intermittently.
- **Address-string caching**: small formatting differences in addresses may create separate cache entries.
- **Heuristic model**: distance to the nearest road is not equivalent to real noise exposure.
>>>>>>> origin/Kevin_NoiseScore
