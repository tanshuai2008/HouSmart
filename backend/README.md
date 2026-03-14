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
python -m app.services.leaic_crosswalk_loader --tsv_path app/data/35158-0001-Data.tsv
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
- `GET /api/onboarding/{user_id}`
- `PUT /api/onboarding/{user_id}`
- `POST /api/property/analyze`
- `GET /api/property/analyze/{run_id}`
- `GET /api/dashboard/property/{property_id}`
- `GET /api/property/recent-searches`
- `GET /api/market-trends`
