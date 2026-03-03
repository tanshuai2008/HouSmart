## Task: POI Radius Query

Query POIs within defined radius around each property.

### Objective

Implement deterministic spatial radius queries using PostGIS to retrieve cached POIs within a defined distance from a stored property location.

This task ensures that:
* Each category uses its own predefined radius
* Queries are executed using PostGIS `ST_DWithin`
* Coordinates are retrieved from the `properties` table
* No external API calls occur when cache exists
* Results are computed deterministically

---

## Category-Specific Radius Enforcement

Each scoring category applies its own radius value during the spatial query:

| Category | Radius (meters) |
|----------|-----------------|
| Education | 2400 |
| Retail | 1600 |
| Healthcare | 3200 |
| Lifestyle | 1600 |
| Transit | 1200 |

The radius is dynamically passed into the `count_pois` PostGIS function.

---

## Spatial Query Logic

All radius filtering is executed using PostGIS geography-based distance filtering:

```
ST_DWithin(
    location,
    ST_SetSRID(ST_MakePoint(lng, lat), 4326)::geography,
    radius_meters
)
```

This ensures:
* Accurate meter-based calculations
* High-performance spatial filtering using GiST index
* Deterministic query behavior

---

## Property-Based Query Flow

Unlike the standalone latitude/longitude testing endpoint, this task uses stored property coordinates.

Pipeline Flow:

```
property_id
    |
    v
Fetch from `properties` table
    |
    v
Retrieve latitude & longitude
    |
    v
Execute PostGIS radius queries per category
    |
    v
Compute normalized scores
    |
    v
Return composite location intelligence score
```

---

## Endpoint Implementation

### Endpoint

```
GET /evaluation/{property_id}/location-intelligence
```

### Example Request

```
http://127.0.0.1:8000/evaluation/f832e250-a431-49a0-940a-744f0d14de38/location-intelligence
```

### Example Response

```
{
    "status": "success",
    "property_id": "f832e250-a431-49a0-940a-744f0d14de38",
    "data": {
        "education": {
            "count": 1,
            "score": 0.04
        },
        "retail": {
            "count": 1,
            "score": 0.025
        },
        "healthcare": {
            "count": 1,
            "score": 0.05
        },
        "lifestyle": {
            "count": 1,
            "score": 0.02
        },
        "transit": {
            "count": 1,
            "score": 0.0333
        },
        "composite_score": 0.1683
    }
}
```