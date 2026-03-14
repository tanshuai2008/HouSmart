# Changes Record (12 March 2026)

Date: 12 March 2026

## Summary

Today's work focused on four areas:
- expanding the property analysis pipeline and dashboard data flow
- refining scoring and persistence logic in the backend
- improving dashboard and search UX in the frontend
- documenting formulas, schema changes, and project structure

## Backend changes

### Property analysis API and data access
- Added/updated analysis request and response schemas for:
  - starting a property analysis run
  - checking run status
  - loading dashboard property payloads
  - listing recent searches
- Extended the analysis routes with:
  - `POST /api/property/analyze`
  - `GET /api/property/analyze/{run_id}`
  - `GET /api/dashboard/property/{property_id}`
  - `GET /api/property/recent-searches`
- Added repository support for:
  - upserting `user_properties`
  - creating and updating `property_analysis_runs`
  - upserting `property_facts`
  - upserting `property_user_scores`
  - replacing and ranking `comparable_properties`
  - loading completed dashboard payloads
  - listing a user's recent searched properties

### Analysis orchestration and scoring
- Expanded the main analysis orchestrator to run the full property pipeline end to end.
- Persisted subject property metadata from rent estimate results into `user_properties`, including:
  - normalized address
  - lat/lng
  - rent and currency
  - property type
  - beds/baths/square footage
  - year built
  - last sale date and price
  - state and county FIPS
- Added lat/lng-first orchestration so flood, transit, and noise services use resolved coordinates when available.
- Stored derived `property_facts` values including:
  - median property price
  - median income
  - bachelor percentage
  - rent-to-price
  - affordability index
  - tenant quality index
  - crime indices
  - flood zone and risk label
  - transit support fields
  - noise support fields
  - school count
- Added weighted amenity scoring driven by onboarding priorities.
- Standardized user score persistence under `scoring_version = v1`.
- Added source tracking in the analysis response for rent, price, income, education, crime, amenity, noise, school, flood, and transit inputs.

### Service logic updates
- Updated transit scoring to use availability-aware weighting:
  - proximity fixed at 20%
  - bus and rail split the remaining 80% only across active modes
- Added Google Places pagination handling and cache refresh behavior for empty transit payloads.
- Continued noise scoring migration toward numeric storage and coordinate-based explainability fields.

### New market trends endpoint
- Added `backend/app/api/routes/market_trends.py` with a backend endpoint for dashboard chart data.
- Registered the market trends router in `backend/main.py` and route exports.
- Endpoint currently serves stable default chart series so the frontend can fetch dashboard trend data from the backend instead of relying only on local mocks.

## Database changes

### Noise score migration
- Added `012_property_user_scores_noise_numeric.sql` to convert `property_user_scores.noise_score` from text to `numeric(5,1)`.
- Added label-to-numeric mapping during conversion:
  - `Low -> 25.0`
  - `Moderate -> 50.0`
  - `High -> 75.0`
  - `Very High -> 90.0`
- Added `013_backfill_property_user_scores_noise_from_facts.sql` to backfill missing user noise scores from `property_facts.noise_index`.

### Comparable listings enhancements
- Added `014_comparable_properties_status_days_on_market.sql`.
- Extended `comparable_properties` with:
  - `status`
  - `days_on_market`
- Backfilled existing comparable rows so status is normalized to active/inactive and days on market is inferred where possible.
- Updated repository logic to:
  - normalize RentCast-style correlation scores to percentages
  - prioritize active listings
  - compute/fill listed date and days on market
  - persist the top comparable set in ranked order

## Frontend changes

### Property search flow
- Updated the property search hero to:
  - load recent searches for the signed-in user
  - display a recent searches section
  - route selected or typed addresses into the analysis flow
  - handle unauthenticated submission states more clearly

### Dashboard data integration
- Added frontend analysis API helpers for:
  - starting an analysis
  - polling run status
  - loading dashboard property data
  - loading recent searches
- Updated the dashboard page to fetch backend property payloads using `property_id`.
- Mapped backend payloads into the UI for:
  - property context
  - location intelligence scores
  - financial metrics
  - comparable listings
- Added backend fetch for market trends and fallback to local mock data when the API is unavailable.

### Dashboard UI refinement
- Updated chart components and dashboard trend components to consume typed backend-compatible data.
- Improved comparable listings presentation with:
  - status badges
  - listed date
  - days ago / days on market context
  - similarity percentage formatting
- Refined dashboard presentation components such as the property verdict and related layout elements.
- Updated dashboard styling assets and global/layout styles during the same pass.

### Environment configuration
- Updated the frontend environment configuration to include a Google Maps public API key variable for map/location-driven UI and service integration.

## Documentation changes created today

- `docs/SCORING_FORMULAS_RECORD_2026-03-12.md`
  - documents current scoring formulas, derived indices, and schema changes
- `docs/STRUCTURE.md`
  - records the current backend structure and key runtime/data script locations

## Outcome

At the end of today's changes:
- the backend can run and persist a fuller property analysis workflow
- the frontend can load recent searches and dashboard data from backend APIs
- dashboard charts can fetch trend series from a dedicated endpoint
- comparable listing records now carry status and days-on-market metadata
- noise scoring storage is aligned with numeric score handling
- the new formulas and structure changes are documented in `docs/`
