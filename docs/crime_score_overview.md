# Crime Safety Score Service

The crime endpoint now calculates a safety score for any address by resolving its agency ORI, fetching FBI summarized crime data for every offense in `CRIME_OFFENSE_CODES`, and comparing weighted local crime rates against a national benchmark.

## High-Level Flow

1. **Geocode Address**  
  `app/services/geocode_client.py` calls Geocodio (`fields=census`, `census_year = current_year - 1`) to retrieve the normalized address, census population, and FIPS identifiers while emitting debug logs that include the full request URL and JSON payload.

2. **Resolve Agency ORI**  
   `app/data/croswalk_leasc_data.py` queries Supabase via `resolve_crosswalk_for_fips()` to find the responsible agency (city preferred, county fallback).

3. **Fetch FBI Summarized Data**  
   `app/services/fbi_crime_data.py` calls `summarized/agency/{ori}/{offense_code}` for every offense between the requested date range (default: previous calendar year) and returns the parsed JSON payloads.

4. **Compute Safety Score**  
  `app/core/crime_scoring.py` ingests the agency + national rate series directly from the FBI response, filters out null/`-1` values, averages each offense’s local and national rates (per 100k), applies `CRIME_WEIGHTS`, builds weighted indices, and derives the exponential-decay safety score and color band (Green/Yellow/Red).

5. **Serve API Response**  
   `app/api/routes/crime_score.py` exposes `POST /api/crime-score`. The route accepts an address, runs the pipeline, and returns local/national metrics with a per-offense breakdown.

## Module Responsibilities

| Module | Purpose |
| --- | --- |
| `app/services/geocode_client.py` | Geocodio wrapper returning normalized address + census data. |
| `app/data/croswalk_leasc_data.py` | Supabase helper that resolves ORI metadata for place/county FIPS. |
| `app/services/fbi_crime_data.py` | Authenticated client for the FBI CDE summarized API. |
| `app/core/crime_scoring.py` | Owns `fetch_ori_metadata()`, `compute_crime_safety_score()`, offense weights, and CLI entrypoint. |
| `app/models/crime.py` | TypedDicts/dataclasses for API inputs, safety-score outputs, and per-offense breakdowns. |
| `app/api/routes/crime_score.py` | FastAPI router that wires the pipeline into HTTP. |

## Required Environment Variables

| Variable | Description |
| --- | --- |
| `GEOCODIO_API_KEY` | Required for address geocoding. |
| `GEOCODIO_BASE_URL` | Optional; defaults to Geocodio v1.7. |
| `SUPABASE_URL` | Supabase project URL. |
| `SUPABASE_SERVICE_ROLE_KEY` / `SUPABASE_KEY` | Supabase credentials for crosswalk lookups. |
| `FBI_API_BASE_URL` | Optional override for the FBI CDE API (defaults to `https://api.usa.gov/crime/fbi/cde`). |
| `FBI_API_KEY` | Required key for the FBI summarized endpoint. |

## Supabase Schema Checklist

The `leaic_crosswalk` table must contain:

- `ori`
- `agency_name`
- `agency_type` (e.g., `city`, `county`)
- `place_fips`
- `county_fips`

Refer to [docs/sql_query.md](docs/sql_query.md) for schema details.

## Built-in Crime Constants

`CRIME_OFFENSE_CODES` and `CRIME_WEIGHTS` live in `app/core/crime_scoring.py`. Every offense in these dictionaries is fetched from the FBI summarized API and contributes to the weighted local/national indices. Update both mappings together when adding/removing offenses.

## Running the Score Calculator Manually

```bash
python -m app.core.crime_scoring "123 Main St, Example City, CA" --from-month 01-2025 --to-month 12-2025
```

The script prints the JSON payload returned by `compute_crime_safety_score()`.

## HTTP API Endpoint

- **Path:** `POST /api/crime-score`
- **Body:**

```json
{
  "address": "123 Main St, Example City, CA"
}
```

- **Response:**

```json
{
  "normalized_address": "123 Main St, Example City, CA 90210",
  "agency": {
    "ori": "CA01903",
    "name": "Los Angeles Police Department",
    "type": "city"
  },
  "date_range": {
    "from": "01-2025",
    "to": "12-2025"
  },
  "months_analyzed": 12,
  "local_crime_index": 143.2,
  "national_crime_index": 162.5,
  "relative_crime_ratio": 0.88,
  "safety_score": 51.3,
  "safety_category": "Yellow",
  "offense_breakdown": [
    {
      "alias": "homicide",
      "offense_code": "HOM",
      "weight": 10.0,
      "local_rate_per_100k": 3.1,
      "national_rate_per_100k": 4.5,
      "rate_ratio": 0.69,
      "months_with_data": 12,
      "weighted_local_rate": 31.0,
      "weighted_national_rate": 45.0
    }
  ],
  "data_available": true,
  "message": null
}
```

When no FBI rate data exists for the agency/date range, the API now returns the same metadata with zeros for the indices, `safety_category: "No Data"`, `data_available: false`, and `message: "Crime data is not available for the supplied address"`.

## Troubleshooting

- **Missing ORI:** Confirm the address geocodes to valid FIPS codes and the Supabase crosswalk contains the matching agency.
- **Zero or missing populations:** Ensure Geocodio returned census population; the scorer falls back to this value when the FBI payload shows zeros.
- **Geocode debugging:** Enable `LOG_LEVEL=DEBUG` to see the complete Geocodio URL, parameters (sans API key), response timing, and payload for each address lookup.
- **FBI request failures:** Check `FBI_API_KEY` and that the date range is supported by the summarized endpoint. Logs include the ORI, offense code, and date window for each fetch.
- **Unexpected score gaps:** If all offenses are skipped (e.g., every category lacks population or national rates), the API returns `400` with an explanatory message; inspect logs for the offending offenses.
