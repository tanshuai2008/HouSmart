# Scoring and Schema Reference (12 March 2026)

Date: 12 March 2026

## 0) Schema and migration updates

### `property_user_scores.noise_score` type change
- Column changed from text to numeric:
  - `noise_score numeric(5,1)`
- Migration:
  - `012_property_user_scores_noise_numeric.sql`
- Legacy value handling during conversion:
  - `Low -> 25.0`
  - `Moderate -> 50.0`
  - `High -> 75.0`
  - `Very High -> 90.0`
  - numeric-looking text is cast directly
  - unknown text becomes `NULL`

### Backfill for already-migrated environments
- Migration:
  - `013_backfill_property_user_scores_noise_from_facts.sql`
- Behavior:
  - Backfills `property_user_scores.noise_score` from `property_facts.noise_index`
  - Applies where `noise_score IS NULL` and a matching `(run_id, property_id)` facts row exists.

### `property_facts` noise support fields
- Numeric support columns are available:
  - `noise_index numeric(5,1)`
  - `estimated_noise_db numeric(5,1)`
- Migration:
  - `011_property_facts_noise_numeric_fields.sql`

## 1) Derived indices in `property_facts`

### Rent-to-Price
- Formula:
  - `rent_to_price = (monthly_rent / median_property_price) * 100`
- Stored with 3-decimal rounding.

### Affordability Index
- Formula:
  - `affordability_index = ((monthly_rent * 12) / median_income) * 100`
- Stored with 3-decimal rounding.
- Lower value means lower rent burden relative to income.

### Tenant Quality Index
- Input: `bachelor_percentage`
- Rules:
  - `>= 40` -> `High`
  - `>= 25 and < 40` -> `Medium`
  - `< 25` -> `Low`

## 2) Stored user scores (`property_user_scores`, `scoring_version = v1`)

Current v1 stores per-metric scores (not a single blended overall score):
- `amenity_score` (priority-weighted, numeric 0-100)
- `transit_score` (numeric 0-100)
- `noise_score` (numeric `noise_index`, 0-100)
- `school_score`
- `safety_score`
- `flood_score`

## 3) Metric formulas and logic by service

### Amenity score
- Per category:
  - `category_norm = min(count / threshold, 1.0)` (range `0..1`)
- Priority source:
  - Read `priorities_ranking_ques` from `user_onboarding_answers`.
  - Rank weights are fixed by order: `0.4, 0.3, 0.2, 0.1`.
  - No equal/uniform fallback is used.
  - If ranking is missing/invalid, deterministic default order is used:
    - `["safety", "proximity", "demographics", "schools"]`
- 4-priority to 5-category mapping:
  - `safety -> lifestyle`
  - `proximity -> retail + transit` (split equally)
  - `demographics -> healthcare`
  - `schools -> education`
- Category weight formulas:
  - `W_lifestyle = P_safety`
  - `W_retail = 0.5 * P_proximity`
  - `W_transit = 0.5 * P_proximity`
  - `W_healthcare = P_demographics`
  - `W_education = P_schools`
- Final formula (0-100):
  - `amenity_score = 100 * (W_education*C_education + W_retail*C_retail + W_healthcare*C_healthcare + W_lifestyle*C_lifestyle + W_transit*C_transit)`
  - where each `C_*` is the corresponding `category_norm`.
  - Clamped to `[0, 100]`, rounded to 1 decimal.

### Transit score
- Normalizations:
  - `bus_norm = min(bus_count / 20, 1)`
  - `rail_norm = min(rail_count / 8, 1)`
  - `proximity_norm = max(0, 1 - nearest_stop_meters / radius_meters)`
- Availability-aware weighting:
  - Keep proximity fixed at `20`.
  - `mode_weight_pool = 80`
  - `active_modes = (bus_count > 0 ? 1 : 0) + (rail_count > 0 ? 1 : 0)`
  - `bus_weight = bus_count > 0 ? mode_weight_pool / active_modes : 0`
  - `rail_weight = rail_count > 0 ? mode_weight_pool / active_modes : 0`
- Formula:
  - `transit_score = (bus_norm * bus_weight) + (rail_norm * rail_weight) + (proximity_norm * 20)`
- Clamped to `[5, 100]`, rounded to 1 decimal.

### Noise scoring
- Noise index (higher = noisier):
  - `noise_index = 100 * exp(-distance_to_road_m / 100)`
  - Clamped `[0, 100]`, rounded to 1 decimal.
- Estimated dB:
  - `estimated_noise_db = 35 + (noise_index / 100) * 45`
- Level labels from distance (for explainability):
  - `<20m: Very High`, `<50m: High`, `<100m: Moderate`, else `Low`.

### School score (property-level)
- Candidate schools filtered to:
  - non-null `housmart_school_score`
  - non-null `s_academic`
  - level in `Elementary`, `Middle`, `High`
- Formula:
  - `property_school_score = average(housmart_school_score of valid schools)`
- Rounded to 1 decimal.

### Safety (crime) score
- Weighted indices built from offense rates:
  - `local_crime_index = sum(local_rate_per_100k * offense_weight)`
  - `national_crime_index = sum(national_rate_per_100k * offense_weight)`
  - `relative_crime_ratio = local_crime_index / national_crime_index`
- Final formula:
  - `safety_score = 100 * exp(-0.75 * relative_crime_ratio)`
- Clamped `[0, 100]`.
- Category:
  - `>75: Green`, `>=40: Yellow`, else `Red`.

### Flood score
- Categorical mapping from FEMA flood zone to fixed score.
- Examples:
  - `VE/V -> 10`
  - `A/AE -> 20`
  - `X500/B -> 60`
  - `X/C -> 95`
  - fallback `D -> 50`

## 4) Priority weighting status

- Onboarding priorities (`priorities_ranking_ques`) are actively used for amenity scoring.
- Rank order is converted to fixed weights `0.4/0.3/0.2/0.1` and mapped to amenity categories as above.
- Other metrics currently remain raw endpoint/service-derived scores.
- System persists per-metric scores plus `scoring_version = v1`.

## 5) Other computed analysis values

- `total_schools`: count from school payload.
- `local_crime_index` / `national_crime_index`: persisted for downstream explainability.
- Transit support fields: radius, nearest stop distance, bus/rail counts.
- Noise support fields: distance to road, numeric index, estimated dB.
- Comparables: top 3 selected after active-status preference + highest normalized correlation.
