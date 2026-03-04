# NoiseScore Module

The **NoiseScore Module** is a standalone extraction from `KevinVariables` that provides **noise estimation** and **road network analysis** features for the HouSmart backend.  
It uses **OpenStreetMap data** to estimate road-noise levels for a property and stores results in **Supabase** for caching and faster repeated queries.

---

# What Was Changed

1. The original combined backend in `KevinVariables` contained multiple APIs.
2. The **noise estimator route and service** were extracted into this standalone module.
3. The **road-map route and service** were added to this module.
4. `main.py` was simplified to include only:
   - `health` route
   - `noise_estimator` route
   - `road_map` route
5. A module-specific `.env` file was created for OpenStreetMap/Nominatim configuration.
6. Backend dependencies were reduced to only packages required for **noise estimation and road-map services**.

---

# Backend Endpoints

## Root
`GET /`

Returns a basic status message confirming the service is running.

---

## Health Check
`GET /api/health`

Returns backend health status.

---

## Noise Estimation by Address
`GET /api/noise-estimate/address?address=<full_address>`

- Geocodes the address
- Finds the nearest road using OpenStreetMap
- Calculates the distance to that road
- Converts the distance to a noise level classification

Example:

```
/api/noise-estimate/address?address=1 Apple Park Way, Cupertino, CA
```

---

## Noise Estimation by Coordinates
`GET /api/noise-estimate/coordinates?lat=<lat>&lon=<lon>`

Returns noise score based on provided coordinates.

Example:

```
/api/noise-estimate/coordinates?lat=37.3349&lon=-122.0090
```

---

## Road Map Summary
`GET /api/road-map?place=<city_or_area>`

Returns a summary of the road network in the given location.

Example:

```
/api/road-map?place=Austin, TX
```

---

# Noise Estimator (Backend Service)

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
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn main:app --reload
```

The API server will start locally and expose the NoiseScore endpoints.

---

# Assumptions and Limitations

- **US-only geocoding**: Nominatim requests are restricted to US addresses.
- **Rate limits**: OpenStreetMap Nominatim and Overpass APIs may rate-limit or fail intermittently.
- **Address-string caching**: small formatting differences in addresses may create separate cache entries.
- **Heuristic model**: distance to the nearest road is not equivalent to real noise exposure.
