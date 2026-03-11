# System Changes Record (11 March 2026)

Date: 11 March 2026

## 1) What changed

This sprint introduced a full property analysis pipeline and aligned scoring/data capture across backend routes, services, schemas, migrations, and frontend integration.

### New analysis pipeline modules
- Added `backend/app/api/routes/analysis.py`
- Added `backend/app/api/schemas/analysis.py`
- Added `backend/app/services/analysis_orchestrator.py`
- Added `backend/app/services/analysis_repository.py`

### New DB migrations for analysis pipeline
- Added `backend/db/migrations/008_property_analysis_pipeline.sql`
- Added `backend/db/migrations/009_property_user_scores_noise_text.sql`
- Added `backend/db/migrations/010_user_properties_fips_columns.sql`
- Added `backend/db/migrations/011_property_facts_noise_numeric_fields.sql`

### API/service updates (existing files changed)
- Routes updated: flood, median house price, noise estimator, school scores, transit
- Schemas updated: flood, school scores, transit
- Core/service updates: crime scoring, rent estimate, census, FBI client, median house price, noise estimator, school score service, transit service, crosswalk resolver, main app routing
- SQL update: `backend/db/sql/score_match_rpc.sql`

### School pipeline adjustments
- Deleted source files:
  - `backend/app/scripts/pipelines/schools/compute_school_scores.py`
  - `backend/app/scripts/pipelines/schools/fetch_school_rankings.py`
- Updated:
  - `backend/app/scripts/pipelines/schools/nces_seda_ingest.py`

### Frontend integration updates
- Added `frontend/src/lib/api/analysis.ts`
- Updated analysis/search UI components for analysis flow and result consumption.

## 2) How it works (end-to-end)

1. Client calls `POST /api/property/analyze` with `user_id` and `address`.
2. Orchestrator resolves rent + subject property details, upserts `user_properties`, creates a `property_analysis_runs` row (`running`).
3. It fetches supporting data in parallel/safe wrappers:
- Median house price
- Census income and education
- Crime safety
- Amenity score
- Noise estimate
- School scores
- Flood + transit (lat/lng first when available; address fallback otherwise)
4. It computes derived facts (`rent_to_price`, `affordability_index`, `tenant_quality_index`, etc.) and upserts `property_facts`.
5. It stores top 3 rent comparables into `comparable_properties`.
6. It builds/stores per-user endpoint scores in `property_user_scores` (`scoring_version = v1`).
7. Run status is set to `completed` (or `failed` with error).
8. Dashboard pulls latest completed run via `GET /api/dashboard/property/{property_id}?user_id=...`.

## 3) Key behavior details

- Stage switch in orchestrator supports phased writes:
  - `user_properties_only`
  - `property_facts_only`
  - `full` (current)
- Geospatial-first strategy: when lat/lng is known, flood/transit/noise use coordinates for better consistency.
- Noise in `property_user_scores` is categorical text (`Very High/High/Moderate/Low/Unknown`), while `property_facts` stores numeric `noise_index` and `estimated_noise_db`.
- School property score is aggregated from district schools with valid `housmart_school_score` + `s_academic` and accepted levels.
