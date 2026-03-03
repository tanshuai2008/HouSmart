# Task: POI Category List 

Finalize list of amenity categories for scoring.

---

Provide deterministic lifestyle and accessibility scoring using OpenStreetMap POIs. The engine:

- Fetches POIs dynamically via Overpass API
- Caches them in PostGIS
- Uses radius-based queries
- Computes weighted category scores
- Returns normalized composite score

---

## Categories Used For Scoring

| Category | OSM Key | Values | Radius | Threshold |
|----------|---------|--------|--------|-----------|
| **Education** | `amenity` | `school`, `college`, `university`, `library` | 2400m | 5 |
| **Retail** | `shop` | `supermarket`, `mall` | 1600m | 8 |
| **Healthcare** | `amenity` | `hospital`, `clinic`, `dentist` | 3200m | 4 |
| **Lifestyle** | `leisure` | `park` | 1600m | 10 |
| **Transit** | `railway` | `station` | 1200m | 6 |

---

## Pipeline Flow

```
1. Check DB cache (PostGIS radius query)
   ↓
2. If no POIs exist in radius:
   ├─ Fetch via Overpass API
   └─ Bulk insert into `osm_poi_cache`
   ↓
3. Compute category counts using PostGIS
   ↓
4. Normalize counts using thresholds
   ↓
5. Apply weights
   ↓
6. Return composite score
```

---

## Scoring Formula

### Per-Category Score

```
score = min(count / threshold, 1.0) * weight
```

**Where:**
- `count` = number of POIs in the specified radius
- `threshold` = minimum POI count for full score
- `weight` = category importance multiplier (default: 1.0)
- `min()` = caps normalized value at 1.0

### Composite Score

```
total_score = Σ(category_scores) / number_of_categories
```

**Result:** Normalized value between 0 and 10 (or raw sum depending on implementation choice).

---

## Caching Strategy

| Event | Behavior |
|-------|----------|
| **First call** | Overpass fetch → DB insert → PostGIS query |
| **Subsequent calls** | PostGIS only (no external API calls) |
| **Cache invalidation** | Manual purge or TTL-based (recommend 30 days) |

**Key Principle:** No repeated external API calls for identical or overlapping geographic queries.

---

## Overpass API Limitations

The public Overpass API may return `504` errors under heavy load.

**Production Recommendations:**
- Use paid OSM data provider (example: Nominatim Enterprise, Mapbox)
- Import regional OSM extracts directly into PostGIS
- Self-host Overpass instance with SSD backend

---

## Database Requirements

### Table: `osm_poi_cache`

Run this SQL in Supabase to create the cache table:

```sql
create table if not exists osm_poi_cache (
    id uuid primary key default gen_random_uuid(),
    osm_key text,
    osm_value text,
    latitude double precision,
    longitude double precision,
    location geography(Point, 4326),
    created_at timestamp default now()
);

create index if not exists idx_osm_location
on osm_poi_cache
using gist(location);
```

**Fields:**
- `id` – Unique POI identifier
- `osm_key` – OSM tag key (example: `amenity`, `shop`, `leisure`)
- `osm_value` – OSM tag value (example: `school`, `supermarket`, `park`)
- `latitude`, `longitude` – Decimal coordinates
- `location` – PostGIS geography type (indexed for efficient spatial queries)
- `created_at` – Insertion timestamp

---

## PostGIS Function: Count POIs

This function counts POIs within a specified radius matching a key and set of values.

```sql
create or replace function count_pois(
    lat double precision,
    lng double precision,
    radius_meters integer,
    p_osm_key text,
    p_osm_values text[]
)
returns integer
language plpgsql
as $$
declare
    result_count integer;
begin
    select count(*)
    into result_count
    from osm_poi_cache
    where osm_key = p_osm_key
    and osm_value = any(p_osm_values)
    and ST_DWithin(
        location,
        ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography,
        radius_meters
    );

    return result_count;
end;
$$;
```

**Usage Example:**

```sql
-- Count schools, colleges, universities within 2400m of (37.7749, -122.4194)
select count_pois(37.7749, -122.4194, 2400, 'amenity', ARRAY['school', 'college', 'university']);
```

---

## Integration with Pipeline

This phase completes the **Amenity POI Pipeline (OSM)** workflow:

```
User Location Input
        ↓
Cache Check (PostGIS)
        ├─→ Cache Hit → Score Computation
        └─→ Cache Miss → Overpass Fetch → DB Insert → Score Computation
        ↓
Normalized Composite Score (0–10)
        ↓
API Response
```

## Test at postman

URL: http://127.0.0.1:8000/evaluation/amenity-score

Type: POST

- Go To Body Tab

    1- Click Body

    2- Select raw

    3- Choose JSON 

Example 1 : 

```
{
  "latitude": 40.7128,
  "longitude": -74.0060
}
```

```
{
  "latitude": 34.0522,
  "longitude": -118.2437
}
```

