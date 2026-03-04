# Variable — Flood Risk Score

**Branch:** `Imene_FloodRiskScore`  
**Status:** ✅ Complete

---

## Description

This service computes a **Flood Risk Score (0–100)** for any US property address by querying the FEMA National Flood Hazard Layer (NFHL) API. It classifies properties into FEMA flood zones (AE, VE, X, etc.), assigns a risk score, and flags whether the property falls within a high-risk or moderate-risk flood zone. Results are persisted to Supabase and cached to avoid redundant API calls.

---

## Input & Output

### Input
| Field | Type | Required | Description |
|---|---|---|---|
| `address` | string | ✅ | Full street address e.g. `"1000 Main St, Houston, TX 77002"` |

### Output
```json
{
  "status": "success",
  "data": {
    "address": "1000 Main St, Houston, TX 77002",
    "property_lat": 29.7569,
    "property_lng": -95.3650,
    "fld_zone": "AE",
    "risk_label": "High Risk — 1% Annual Chance",
    "flood_score": 20,
    "in_flood_zone": true,
    "in_moderate_zone": false,
    "flood_data_unknown": false,
    "source": "FEMA National Flood Hazard Layer (NFHL)"
  }
}
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/flood/check/address` | **Main endpoint** — check flood zone by address |
| `POST` | `/flood/import` | Import flood zone by lat/lng into DB |
| `GET` | `/flood/check` | Check flood zone by raw lat/lng (read-only) |
| `GET` | `/flood/check/property/{property_id}` | Check flood zone by property ID from DB |
| `GET` | `/flood/check/all-properties` | Bulk scan all properties in DB |
| `GET` | `/flood/debug-fema` | Debug raw FEMA API response |

---

## Data Sources

| Source | Usage | Cost | Auth |
|---|---|---|---|
| **FEMA NFHL ArcGIS REST API** | Flood zone classification | FREE | None |
| **OSM Nominatim** | Geocode address → lat/lng | FREE | None |

> **FEMA API note:** FEMA blocks non-US IP addresses. The code always tries the real API first — if it fails it automatically falls back to a geography-based mock. Production on Render (US servers) uses real FEMA data with no config changes needed.

---

## Data Time Period

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

---

## Database Tables

| Table | Description |
|---|---|
| `flood_zones` | FEMA flood classification per location (zone, risk label, score) |
| `flood_risk_cache` | Supabase cache — 180-day TTL, keyed by `flood:{lat}:{lng}` |

---

## Caching

Results are cached in the `flood_risk_cache` Supabase table with a **180-day TTL**.  
Cache failures are caught and logged silently — the app always falls through to the live API if cache is unavailable.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Address not found by Nominatim | `422` with message `"Address not found: '...'"` |
| Address too short (< 5 chars) | `422` Pydantic validation error |
| Invalid lat/lng | `422` with clear message |
| Property ID not found | `404` |
| FEMA API blocked (non-US IP) | Falls back to geographic mock automatically |
| FEMA API timeout | Falls back to geographic mock automatically |
| Duplicate DB insert | Handled via `upsert on_conflict` |
| Cache unavailable | Caught and logged, falls through to API |
| Property missing coordinates | Skipped gracefully in bulk scan |

---

## Assumptions & Limitations

- **FEMA API geographic restriction:** FEMA's NFHL API is only accessible from US IP addresses. A geography-based mock is used for local development outside the US — results will be approximate. Production deployment on US servers returns real FEMA data.
- **Point-based query:** The flood zone is determined by a small bounding box (±0.001°, ~100m) around the property coordinates. Properties near zone boundaries may get the adjacent zone.
- **US properties only:** FEMA NFHL only covers US territories. Non-US addresses will return mock/minimal risk data.
- **Map currency:** Cached results are valid for 180 days. If a property's flood map is revised within that window, the cached result may be stale.

---

## Running Locally

```bash
cd backend && source venv/bin/activate
uvicorn app.main:app --reload
# Swagger UI → http://127.0.0.1:8000/docs
```

No additional services required. Caching uses Supabase.