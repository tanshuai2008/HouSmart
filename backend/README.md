# Backend Setup

Detailed backend behavior reference:
- `docs/BACKEND_TECHNICAL_REFERENCE.md`

## 1) Install dependencies

```bash
pip install -r requirements.txt
```

## 2) Configure environment

Copy `.env.example` to `.env` and fill values.

Required for startup:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY` (or `SUPABASE_ANON_KEY`)

Required for full endpoint coverage:
- `DATABASE_URL` (for SQL migrations)
- `CENSUS_API_KEY`
- `RENTCAST_API_KEY`
- `GEOCODIO_API_KEY`
- `FBI_API_KEY`

## 3) Apply database migrations

```bash
python app/scripts/apply_migrations.py
```

This creates all currently-used backend tables and the `count_pois` SQL function.

Note:
- If your database has multiple overloaded `count_pois` functions, PostgREST can return `PGRST203` ambiguity errors.
- The backend currently includes a repository fallback for amenity counts, but DB cleanup (single function signature) is recommended.

## 4) Optional data loaders

Crime score crosswalk requires data in `leaic_crosswalk`:

```bash
python -m app.services.leaic_crosswalk_loader --tsv_path app/data/ICPSR_35158-V2/ICPSR_35158/DS0001/35158-0001-Data.tsv
```

Median price endpoint relies on `redfin_median_prices`:

```bash
python app/scripts/ingest_redfin.py
```

## 5) Run API

```bash
uvicorn main:app --reload --port 8000
```

## 6) Active API endpoints

- `GET /api/health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/google`
- `POST /auth/verify`
- `POST /api/education_level`
- `POST /api/median_income`
- `POST /api/amenity_score`
- `POST /api/crime_score`
- `POST /api/flood_risk_score`
- `POST /api/transit_score`
- `POST /api/rent_estimate`
- `POST /api/noise_estimate_score`
- `POST /api/median_property_price`
- `POST /api/school_scores`
