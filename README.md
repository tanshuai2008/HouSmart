# HouSmart

HouSmart is a full-stack property intelligence platform for residential real-estate analysis. It combines user onboarding preferences, property-level facts, market context, and multiple external datasets to produce a dashboard that helps an investor understand whether a property looks attractive, risky, overpriced, under-rented, well-located, or operationally weak.

The repository contains:
- a `Next.js` frontend for authentication, onboarding, property search, analysis progress, and dashboard presentation
- a `FastAPI` backend that handles auth, onboarding persistence, property analysis orchestration, dashboard payload assembly, and market-trend APIs
- SQL migrations, ingestion scripts, and documentation for the datasets and derived scoring logic that feed the product

## What the product does

At a high level, HouSmart lets a user:
- create an account or sign in with email/password or Google
- complete onboarding that captures investing role, experience, goals, preferred markets, and ranked priorities
- search for a property and start an analysis run
- persist the run, derived property facts, metric scores, and comparable listings
- open a dashboard that brings together:
  - property context
  - verdict and risk/upside framing
  - financial metrics
  - location intelligence
  - market trends
  - comparable sales/listings

## Why the data is trustworthy

HouSmart is not built around a single opaque score. It combines multiple identifiable data providers and stores intermediate facts so the system can explain where numbers come from.

Primary trust mechanisms in the current codebase:
- external data is sourced from named providers rather than anonymous scraped payloads
- important intermediate outputs are persisted in database tables such as `property_facts`, `property_user_scores`, `comparable_properties`, and cache tables
- API request and response payloads are logged to `api_call_logs` for observability and auditability
- many metrics preserve source metadata in backend responses and stored analysis payloads
- the dashboard renders separate metrics instead of hiding everything behind one unexplained black-box number

## Data sources

The current backend and ingestion pipeline use the following data sources.

### Runtime external APIs

- `US Census Geocoder`
  - Used for address resolution in education, income, and amenity-related flows.
- `American Community Survey (ACS)`
  - Used for census-derived demographic and income metrics.
  - Current documented usage includes:
    - `B15003_001E` and `B15003_022E` for bachelor-percentage calculation
    - `B19013_001E` for median household income
- `Google Places`
  - Used for amenity POIs and transit-stop discovery.
  - Also supports location intelligence and amenity density logic.
- `Google Roads`
  - Used by the noise-estimation logic to estimate proximity to roads.
- `Geocodio`
  - Used in crime scoring flows to map addresses to place/county FIPS context.
- `FBI Crime Data Explorer (CDE)`
  - Used for offense-rate comparisons that drive the property safety score.
- `FEMA National Flood Hazard Layer (NFHL)`
  - Used for flood-zone lookups and flood-risk score mapping.
- `Nominatim`
  - Used for geocoding in flood, transit, noise, and median-price flows.
- `RentCast`
  - Used for rent estimates and comparables.

### Stored and ingested datasets

- `Redfin median sale price data`
  - Loaded into `redfin_median_prices`.
  - Used for median property price lookups and dashboard market-trend presentation.
- `LEAIC crosswalk data`
  - Loaded into `leaic_crosswalk`.
  - Maps FIPS geography to law-enforcement agencies/ORI identifiers for crime analysis.
- `NCES Common Core of Data (CCD)`
  - Used in the school data pipeline for school directory, enrollment, staffing, lunch-program, and school-characteristics fields.
- `Stanford Educational Opportunity Project (SEDA) v6.0`
  - Used in the school scoring pipeline for academic, growth, and math signals.
- `Supabase PostgreSQL`
  - Stores all application state, caches, analysis outputs, and derived tables.

### Derived internal datasets

HouSmart also creates its own derived facts and scores from those sources, including:
- rent-to-price
- affordability index
- tenant quality classification
- amenity score
- transit score
- safety score
- flood score
- property-level school score
- comparables ranking outputs

## Product flow

### 1. Authentication

Frontend:
- email/password sign-up and login
- Google sign-in via Firebase client auth

Backend:
- registration, login, token verification, and Google token exchange endpoints under `/auth/*`

### 2. Onboarding

The onboarding flow captures user profile and investment intent, including ranked priorities. Those priorities are not cosmetic; the backend uses them in the amenity-scoring logic to weight categories differently for different users.

### 3. Property analysis

When a user starts an analysis:
- the backend creates or updates the property record
- gathers external data across rent, price, income, education, crime, flood, transit, noise, amenities, and school context
- computes derived facts and scores
- persists facts and user-facing score outputs
- selects and stores comparables
- returns data needed for the dashboard

### 4. Dashboard

The dashboard currently combines:
- property verdict
- financial metrics
- property context
- location intelligence
- market trends
- comparable listings

The dashboard loading flow was recently updated so it:
- fetches the dashboard property payload and market-trend payload in parallel
- shows a structured skeleton while data is loading
- renders the main dashboard only when the required responses are ready

## Scoring model overview

HouSmart stores per-metric scores rather than forcing everything into one hidden total score.

Current persisted score families include:
- `amenity_score`
- `transit_score`
- `noise_score`
- `school_score`
- `safety_score`
- `flood_score`

The precise scoring formulas, weighting rules, and normalization logic are proprietary. At the product level, the important point is that these scores are grounded in identifiable datasets, persisted intermediate facts, and repeatable backend processing rather than manual opinion.

## Repository structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- middleware/
|   |   |-- scripts/
|   |   `-- services/
|   |-- db/
|   |   |-- migrations/
|   |   `-- sql/
|   `-- requirements.txt
|-- frontend/
|   |-- src/
|   |   |-- app/
|   |   |-- assets/
|   |   |-- components/
|   |   |-- lib/
|   |   |-- providers/
|   |   `-- types/
|   `-- package.json
`-- docs/
```

Useful references:
- `backend/`
- `frontend/`

## Tech stack

### Frontend

- `Next.js 16.1.6`
- `React 19.2.3`
- `TypeScript`
- `Tailwind CSS v4`
- `Recharts`
- `Firebase Web Auth`
- `lucide-react`
- `@dnd-kit/*`

### Backend

- `FastAPI 0.129.0`
- `Uvicorn`
- `Pydantic v2`
- `Supabase Python client`
- `SQLAlchemy`
- `psycopg2`
- `pandas`
- `numpy`
- `httpx`
- `firebase-admin`

### Platform services

- `Supabase` for data storage and API-backed table access
- `Firebase` for frontend auth integration

## Database and persistence

The backend uses SQL migrations plus Supabase-backed tables for both source caches and product-facing outputs.

Important runtime tables include:
- `geo_tract_metrics`
- `flood_risk_cache`
- `flood_zones`
- `transit_cache`
- `transit_scores`
- `noise_scores`
- `redfin_median_prices`
- `rent_estimate_cache`
- `leaic_crosswalk`
- `osm_poi_cache`
- `school_master`
- `api_call_logs`

Product analysis persistence includes:
- `user_properties`
- `property_analysis_runs`
- `property_facts`
- `property_user_scores`
- `comparable_properties`

## API surface

Current active backend endpoints documented in the repo:
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

The score-specific route wrappers for education, income, amenity, crime, flood, transit, rent, noise, median price, and school scoring are no longer mounted as public routes, but their underlying logic is still used by the analysis pipeline.

## Local development

### Prerequisites

- `Node.js` for the frontend
- `Python` for the backend
- access to Supabase
- Firebase project credentials for frontend auth
- API keys for the external services you intend to exercise locally

### Backend setup

Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env` from your environment template and configure at least:

```env
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
DATABASE_URL=...
CENSUS_API_KEY=...
RENTCAST_API_KEY=...
GEOCODIO_API_KEY=...
FBI_API_KEY=...
```

Run migrations:

```bash
python app/scripts/apply_migrations.py
```

Optional but strongly recommended data loaders:

```bash
python -m app.services.leaic_crosswalk_loader --tsv_path app/data/35158-0001-Data.tsv
python app/scripts/ingest_redfin.py
```

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

### Frontend setup

Install dependencies:

```bash
cd frontend
npm install
```

Create `frontend/.env` with:

```env
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=...
NEXT_PUBLIC_FIREBASE_PROJECT_ID=...
NEXT_PUBLIC_FIREBASE_APP_ID=...
```

Start the frontend:

```bash
npm run dev
```

Default local app URL:
- `http://localhost:3000`

## Observability and auditability

The backend includes centralized API call logging middleware that writes request/response payloads to `api_call_logs`.

That gives the project:
- endpoint-level audit history
- easier debugging of failed or malformed payloads
- a path to later user-level attribution

Important caveat:
- logged payloads can contain sensitive information if redaction is not added, so production hardening should include masking and retention controls

## Known implementation notes

- The dashboard market-trend charts currently consume backend-provided trend payloads and scale their axes dynamically.
- The backend retains score-service logic internally even though those routes are no longer exposed directly.

## Current status

This repository already contains the core plumbing for:
- authenticated users
- onboarding persistence
- property analysis orchestration
- cached and persisted property intelligence signals
- dashboard rendering with market trends and comparables

The strongest part of the system is that the scores are tied back to named data providers and stored intermediate facts rather than being presented as unsupported opinion. That is the main reason the data story is credible: the platform can point to where the data came from, how it was transformed, and where it was stored.
