# Backend (Integration)

This backend contains the merged FastAPI services (Transit + Flood + others). The canonical endpoint list is in `docs/README.md`.
| `GET` | `/flood/check` | Check flood zone by raw lat/lng (read-only) |
| `GET` | `/flood/check/property/{property_id}` | Check flood zone by property ID from DB |
| `GET` | `/flood/check/all-properties` | Bulk scan all properties in DB |
| `GET` | `/flood/debug-fema` | Debug raw FEMA API response |
>>>>>>> origin/Imene_FloodRiskScore

---

## Data Sources

| Source | Usage | Cost | Auth |
|---|---|---|---|
<<<<<<< HEAD
| **OpenStreetMap Overpass API** | Fetch transit stops | FREE | None |
| **OSM Nominatim** | Geocode address → lat/lng | FREE | None |

> 3 Overpass mirror servers are tried in sequence on timeout.  
> Nominatim requires a valid `User-Agent` header — configured in `settings.HTTP_USER_AGENT`.
=======
| **FEMA NFHL ArcGIS REST API** | Flood zone classification | FREE | None |
| **OSM Nominatim** | Geocode address → lat/lng | FREE | None |

> **FEMA API note:** FEMA blocks non-US IP addresses. The code always tries the real API first — if it fails it automatically falls back to a geography-based mock. Production on Render (US servers) uses real FEMA data with no config changes needed.
>>>>>>> origin/Imene_FloodRiskScore

---

## Data Time Period

<<<<<<< HEAD
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
=======
FEMA NFHL data reflects the **most current published flood maps** at the time of the API call. FEMA maps are updated periodically (new studies, amendments, Letter of Map Revisions). Results are cached for **180 days** in Supabase (`flood_risk_cache` table) since FEMA maps change infrequently.

---

## Flood Zone Scoring (0–100)

Higher score = safer property. Score of 100 = no flood risk.

| FEMA Zone | Risk Label | Score |
|---|---|---|
| VE, V | Very High Risk — Coastal Wave Action | 10 |
| AE, A | High Risk — 1% Annual Chance | 20 |
| AO, AH | High Risk — Shallow Flooding | 25 |
| A99, AR | High/Moderate Risk — Levee | 30 |
| X500, B | Moderate Risk — 0.2% Annual Chance | 60 |
| X, C | Minimal Risk | 95 |
| D | Undetermined Risk | 50 |

**Zone AE explained:** A 1% annual chance of flooding means the area is expected to flood once every 100 years on average — this is what FEMA classifies as a high-risk flood zone and typically requires flood insurance for federally-backed mortgages.
>>>>>>> origin/Imene_FloodRiskScore

---

## Database Tables

| Table | Description |
|---|---|
<<<<<<< HEAD
| `transit_stops` | Raw OSM stop locations (osm_id, name, type, lat, lng) |
| `transit_scores` | Computed score per location (score, counts, nearest distance) |
| `transit_cache` | Supabase cache — 30-day TTL, keyed by `transit:{lat}:{lng}:{radius}` |
=======
| `flood_zones` | FEMA flood classification per location (zone, risk label, score) |
| `flood_risk_cache` | Supabase cache — 180-day TTL, keyed by `flood:{lat}:{lng}` |
>>>>>>> origin/Imene_FloodRiskScore

---

## Caching

<<<<<<< HEAD
Results are cached in the `transit_cache` Supabase table with a **30-day TTL**.  
=======
Results are cached in the `flood_risk_cache` Supabase table with a **180-day TTL**.  
>>>>>>> origin/Imene_FloodRiskScore
Cache failures are caught and logged silently — the app always falls through to the live API if cache is unavailable.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Address not found by Nominatim | `422` with message `"Address not found: '...'"` |
| Address too short (< 5 chars) | `422` Pydantic validation error |
| Invalid lat/lng | `422` with clear message |
<<<<<<< HEAD
| Invalid radius | `422` — must be 100–5000m |
| Property ID not found | `404` |
| Overpass API timeout | Auto-retries across 3 mirror servers |
| Duplicate DB insert | Handled via `upsert on_conflict` |
| Cache unavailable | Caught and logged, falls through to API |
=======
| Property ID not found | `404` |
| FEMA API blocked (non-US IP) | Falls back to geographic mock automatically |
| FEMA API timeout | Falls back to geographic mock automatically |
| Duplicate DB insert | Handled via `upsert on_conflict` |
| Cache unavailable | Caught and logged, falls through to API |
| Property missing coordinates | Skipped gracefully in bulk scan |
>>>>>>> origin/Imene_FloodRiskScore

---

## Assumptions & Limitations

<<<<<<< HEAD
- **Stop count proxy:** Transit score is based on the number of nearby stops, not service frequency. A stop served once a day scores the same as one served every 5 minutes. Post-MVP improvement: use GTFS `stop_times.txt` to compute average headways.
- **800m default radius:** Based on WMATA/APTA standard for walkable transit access. Configurable up to 5000m.
- **US-centric:** Nominatim geocoding and OSM data work globally but scoring thresholds were calibrated against US cities.
- **Rural areas:** Properties with zero nearby stops return `nearest_stop_meters: null` and `transit_score: 5` (minimum).
=======
- **FEMA API geographic restriction:** FEMA's NFHL API is only accessible from US IP addresses. A geography-based mock is used for local development outside the US — results will be approximate. Production deployment on US servers returns real FEMA data.
- **Point-based query:** The flood zone is determined by a small bounding box (±0.001°, ~100m) around the property coordinates. Properties near zone boundaries may get the adjacent zone.
- **US properties only:** FEMA NFHL only covers US territories. Non-US addresses will return mock/minimal risk data.
- **Map currency:** Cached results are valid for 180 days. If a property's flood map is revised within that window, the cached result may be stale.
>>>>>>> origin/Imene_FloodRiskScore

---

## Running Locally

```bash
cd backend && source venv/bin/activate
uvicorn app.main:app --reload
# Swagger UI → http://127.0.0.1:8000/docs
```

<<<<<<< HEAD
No additional services required. Caching uses Supabase (already configured).
=======
No additional services required. Caching uses Supabase.
>>>>>>> origin/Imene_FloodRiskScore
