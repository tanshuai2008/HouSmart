# Variable — Transit Score

**Branch:** `Imene_TransitScore`  
**Status:** ✅ Complete

---

## Description

This service computes a **Transit Score (0–100)** for any US property address. It fetches all nearby public transit stops (bus, rail, subway, tram) from OpenStreetMap within an 800-meter walkable radius, calculates the distance to the nearest stop using the Haversine formula, and generates a score based on stop count and transit type. Results are persisted to Supabase and cached to avoid redundant API calls.

---

## Input & Output

### Input
| Field | Type | Required | Description |
|---|---|---|---|
| `address` | string | ✅ | Full street address e.g. `"350 5th Ave, New York, NY 10118"` |
| `radius_meters` | integer | ❌ | Search radius (100–5000m). Default: **800m** |

### Output
```json
{
  "status": "success",
  "data": {
    "address": "350 5th Ave, New York, NY 10118",
    "property_lat": 40.7484,
    "property_lng": -73.9856,
    "radius_meters": 800,
    "nearest_stop_meters": 54.3,
    "transit_score": 100,
    "bus_stop_count": 171,
    "rail_station_count": 110,
    "source": "OpenStreetMap (Overpass API)"
  }
}
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/transit/score/address` | **Main endpoint** — score by address |
| `GET` | `/transit/score/property/{property_id}` | Score by property ID from DB |
| `GET` | `/transit/score` | Score by raw lat/lng |
| `POST` | `/transit/import-stops` | Bulk import stops into DB |

---

## Data Sources

| Source | Usage | Cost | Auth |
|---|---|---|---|
| **OpenStreetMap Overpass API** | Fetch transit stops | FREE | None |
| **OSM Nominatim** | Geocode address → lat/lng | FREE | None |

> 3 Overpass mirror servers are tried in sequence on timeout.  
> Nominatim requires a valid `User-Agent` header — configured in `settings.HTTP_USER_AGENT`.

---

## Data Time Period

OpenStreetMap data is **continuously updated by contributors worldwide** — no fixed time period. Data reflects the current state of transit infrastructure at the time of the API call. Results are cached for **30 days** in Supabase (`transit_cache` table).

---

## Scoring Logic

Default radius: **800m** — the standard walkable transit distance per WMATA/APTA guidelines.  
Rail stations give a **+15 bonus** on top of the base score.

| Bus Stops (within radius) | Rail Stations | Score |
|---|---|---|
| 20+ | 2+ | 100 |
| 15+ | 1+ | 100 |
| 10+ | 1+ | 90 |
| 8+ | 0 | 65 |
| 5+ | 0 | 50 |
| 3+ | 0 | 35 |
| 1+ | 0 | 20 |
| 0 | 0 | 5 |

---

## Database Tables

| Table | Description |
|---|---|
| `transit_stops` | Raw OSM stop locations (osm_id, name, type, lat, lng) |
| `transit_scores` | Computed score per location (score, counts, nearest distance) |
| `transit_cache` | Supabase cache — 30-day TTL, keyed by `transit:{lat}:{lng}:{radius}` |

---

## Caching

Results are cached in the `transit_cache` Supabase table with a **30-day TTL**.  
Cache failures are caught and logged silently — the app always falls through to the live API if cache is unavailable.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Address not found by Nominatim | `422` with message `"Address not found: '...'"` |
| Address too short (< 5 chars) | `422` Pydantic validation error |
| Invalid lat/lng | `422` with clear message |
| Invalid radius | `422` — must be 100–5000m |
| Property ID not found | `404` |
| Overpass API timeout | Auto-retries across 3 mirror servers |
| Duplicate DB insert | Handled via `upsert on_conflict` |
| Cache unavailable | Caught and logged, falls through to API |

---

## Assumptions & Limitations

- **Stop count proxy:** Transit score is based on the number of nearby stops, not service frequency. A stop served once a day scores the same as one served every 5 minutes. Post-MVP improvement: use GTFS `stop_times.txt` to compute average headways.
- **800m default radius:** Based on WMATA/APTA standard for walkable transit access. Configurable up to 5000m.
- **US-centric:** Nominatim geocoding and OSM data work globally but scoring thresholds were calibrated against US cities.
- **Rural areas:** Properties with zero nearby stops return `nearest_stop_meters: null` and `transit_score: 5` (minimum).

---

## Running Locally

```bash
cd backend && source venv/bin/activate
uvicorn app.main:app --reload
# Swagger UI → http://127.0.0.1:8000/docs
```

No additional services required. Caching uses Supabase (already configured).