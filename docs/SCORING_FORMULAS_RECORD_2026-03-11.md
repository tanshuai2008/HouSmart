# Scoring and Derived Formula Reference (11 March 2026)

Date: 11 March 2026

## 1) Derived indices in `property_facts`

### Rent-to-Price
- Formula:
  - `rent_to_price = ((monthly_rent * 12) / median_property_price) * 100`
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

Current v1 stores raw endpoint-derived scores (not a single weighted blended score yet):
- `amenity_score`
- `transit_score`
- `noise_score` (categorical text)
- `school_score`
- `safety_score`
- `flood_score`

## 3) Metric formulas and logic by service

### Amenity score
- Per category:
  - `category_score = min(count / threshold, 1.0) * weight`
- Composite:
  - Sum of all category scores.

### Transit score
- Normalizations:
  - `bus_norm = min(bus_count / 20, 1)`
  - `rail_norm = min(rail_count / 8, 1)`
  - `proximity_norm = max(0, 1 - nearest_stop_meters / radius_meters)`
- Formula:
  - `transit_score = (bus_norm * 40) + (rail_norm * 40) + (proximity_norm * 20)`
- Clamped to `[5, 100]`, rounded to 1 decimal.

### Noise scoring
- Noise index (higher = noisier):
  - `noise_index = 100 * exp(-distance_to_road_m / 100)`
  - Clamped `[0, 100]`, rounded to 1 decimal.
- Estimated dB:
  - `estimated_noise_db = 35 + (noise_index / 100) * 45`
- Level labels from distance:
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

## 4) Variable scoring (priority-weighting status)

- Onboarding priorities (`priorities_ranking_ques`) are read and mapped to temporary weights:
  - Top ranks boost metric multipliers (`1.2`, `1.15`, `1.1`, `1.05`).
- Current status in v1:
  - these variable weights are prepared in code but not yet applied to compute a final blended/overall score.
  - system currently persists raw per-metric scores plus `scoring_version = v1`.

## 5) Other computed analysis values

- `total_schools`: count from school payload.
- `local_crime_index` / `national_crime_index`: persisted for downstream explainability.
- Transit support fields: radius, nearest stop distance, bus/rail counts.
- Noise support fields: distance to road, numeric index, estimated dB.
- Comparables: top 3 selected after active-status preference + highest normalized correlation.
