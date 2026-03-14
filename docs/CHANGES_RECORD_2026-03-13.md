# Changes Record (13 March 2026)

Date: 13 March 2026

## Summary

Today's work focused on four areas:
- consolidating the backend API surface around auth, onboarding, property analysis, dashboard, and market trends flows
- expanding LEAIC crosswalk storage and lookup logic to support richer raw-source matching
- tightening backend runtime configuration and setup documentation
- updating technical documentation to reflect the current mounted routes and internal service boundaries

## Backend changes

### API surface cleanup
- Removed the standalone score-specific route modules for:
  - education
  - income
  - amenity score
  - crime score
  - flood risk
  - transit score
  - rent estimate
  - noise estimate
  - median property price
  - school scores
- Removed now-unused schema modules that only supported those deleted route wrappers:
  - `location.py`
  - `rent_estimate.py`
  - `school_scores.py`
  - `transit.py`
- Simplified `backend/app/api/routes/__init__.py` so it exports only the currently mounted route packages.
- Updated `backend/main.py` to mount only the active routers:
  - health
  - auth
  - onboarding
  - analysis
  - market trends

### Runtime and deployment update
- Added `https://housmart.onrender.com` to the FastAPI CORS allowlist in `backend/main.py`.
- This keeps the deployed frontend aligned with the backend’s active origin configuration.

### Crime crosswalk lookup improvements
- Added `fetch_candidate_agencies(...)` in `backend/app/core/crime_scoring.py`.
- Added multi-match crosswalk resolution support through `resolve_crosswalk_for_fips_list(...)`.
- Expanded crosswalk row parsing so lookup logic can:
  - read additional ORI variants (`ori`, `ori7`, `ori9`)
  - read additional agency name fields such as `address_name`
  - normalize more agency-type variants such as municipal police, local police, and sheriff
- Refactored query helpers so schema-variant handling is clearer and missing-column errors are isolated from valid empty-result lookups.

### LEAIC loader update
- Updated `backend/app/services/leaic_crosswalk_loader.py` so normalized records now retain the lower-cased raw TSV columns in addition to the curated fields already stored.
- Added raw-value cleaning to avoid persisting blank strings.
- Updated the README loader example to point at the new in-repo TSV path:
  - `app/data/35158-0001-Data.tsv`

## Database changes

### LEAIC schema expansion
- Extended `leaic_crosswalk` in `backend/db/migrations/001_initial.sql` with raw-source columns from the LEAIC dataset, including:
  - alternate FIPS fields
  - alternate ORI fields
  - raw agency/type naming fields
  - address fields
  - metadata/source fields
  - geographic support fields
- Added new indexes for:
  - `fplace`
  - `fips`
  - `address_zip`
  - `(address_city, address_state)`
- Added `backend/db/migrations/015_leaic_crosswalk_raw_columns.sql` so existing databases can be upgraded to the same expanded schema without recreating the initial migration state.

### Data asset added
- Added `backend/app/data/35158-0001-Data.tsv` to keep the LEAIC source file directly accessible from the repo path used by the loader.

## Documentation changes

### Backend docs refreshed
- Updated `backend/README.md` to:
  - replace the old crosswalk loader path
  - list the current active API endpoints instead of the removed standalone score endpoints
- Updated `docs/BACKEND_TECHNICAL_REFERENCE.md` to:
  - describe the backend as an auth/onboarding/property-analysis API
  - document the currently mounted route set
  - clarify that the individual score sections now describe internal analysis services rather than public route wrappers

## Outcome

At the end of today's changes:
- the public backend API is narrower and more aligned with the orchestrated property-analysis workflow
- legacy standalone score endpoints have been removed from the mounted application surface
- LEAIC crosswalk ingestion and lookup now support a richer set of raw columns and matching paths
- backend docs and setup instructions reflect the current architecture more accurately
