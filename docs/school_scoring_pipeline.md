# HouSmart School Scoring Pipeline

## Overview

The HouSmart School Scoring Pipeline calculates a normalized 0–100 school quality score for every U.S. public school using data from NCES (National Center for Education Statistics) and SEDA (Stanford Education Data Archive).

The system powers the HouSmart property intelligence API, allowing users to submit a property address and receive ranked nearby schools.

The pipeline integrates:

- National education datasets
- Machine-engineered features
- Custom HouSmart scoring algorithm
- Supabase PostgreSQL database
- FastAPI backend service

The final system provides fast school intelligence queries for real estate analysis.

## System Architecture

```
User Request
     │
     ▼
FastAPI API
     │
     ▼
Google Maps Geocoding
(Address → ZIP)
     │
     ▼
Supabase Query
(ZIP → Schools)
     │
     ▼
HouSmart Scoring Algorithm
     │
     ▼
Ranked Schools Response
```

## Data Sources

### 1. NCES (Common Core of Data)

The NCES dataset provides official information for U.S. public schools.

**Datasets used:**

| Dataset | Purpose |
|---------|---------|
| ccd_sch_029_directory | School directory |
| ccd_sch_052_membership | Enrollment counts |
| ccd_sch_059_staff | Teacher counts |
| ccd_sch_033_lunch | Free/Reduced lunch statistics |
| ccd_sch_129_schoolChar | School characteristics |

### 2. SEDA Dataset

The Stanford Education Data Archive (SEDA) provides school-level academic performance metrics.

**Dataset used:**

- seda_school_pool_cs_6.0.csv

**Key metric used:**

- cs_mn_avg_eb: This metric represents education-adjusted academic achievement.

## HouSmart School Score Algorithm

The final HouSmart score combines three dimensions of school quality.

```
HouSmart Score =
0.6 × Academic
+ 0.2 × Resource
+ 0.2 × Equity
```

### 1. Academic Score (60%)

**Metric:**

- cs_mn_avg_eb

**Normalized within each state:**

```
S_academic =
(value − state_min) / (state_max − state_min) × 100
```

This removes state-level testing bias.

### 2. Resource Score (20%)

**Metric:**

- student_teacher_ratio

**Formula:**

| Ratio | Score |
|-------|-------|
| < 12 | 100 |
| 12–25 | Linear decay |
| > 25 | 40 |

**Implementation:**

```
score = 100 − (ratio − 12) × 4.6
```

Lower ratios indicate more teacher attention per student.

### 3. Equity Score (20%)

**Metric:**

- FRPL rate (FRPL = Free/Reduced Price Lunch)

**Formula:**

```
S_equity = (1 − FRPL_rate / 100) × 100
```

Lower poverty → higher score.

## Data Pipeline

**Pipeline script:**

- backend/app/data/nces_seda_ingest.py

**Pipeline stages:**

1. Load NCES datasets
2. Load SEDA dataset
3. Merge datasets by NCESSCH
4. Compute student-teacher ratio
5. Compute FRPL rate
6. Normalize academic scores by state
7. Compute HouSmart school score
8. Clean missing values
9. Upload results to Supabase

## Database Schema

### school_master

Main dataset containing ~100,000 U.S. schools.

| Column | Description |
|--------|-------------|
| ncessch | NCES school ID |
| school_name | School name |
| district_id | District ID |
| district_name | District name |
| state | State |
| zip_code | School ZIP code |
| student_teacher_ratio | Enrollment / teachers |
| frpl_rate | Free/reduced lunch percentage |
| academic_score | Raw SEDA score |
| s_academic | Normalized academic score |
| s_resource | Resource score |
| s_equity | Equity score |
| housmart_school_score | Final HouSmart score |

### school_districts

District reference table.

| Column | Description |
|--------|-------------|
| district_id | District ID |
| district_name | District name |
| state | State |

### property_school_district

Links properties to school districts.

| Column | Description |
|--------|-------------|
| property_id | Property UUID |
| district_id | School district |

## SQL Queries Used

### Create Performance Indexes

```sql
CREATE INDEX idx_school_zip
ON school_master(zip_code);

CREATE INDEX idx_school_district
ON school_master(district_id);
```

These improve:

- ZIP lookups
- district joins

### District Synchronization

Ensures all districts exist in school_districts.

```sql
CREATE OR REPLACE FUNCTION sync_school_districts()
RETURNS void
LANGUAGE sql
AS $$
INSERT INTO school_districts (district_id, district_name, state)
SELECT DISTINCT district_id, district_name, state
FROM school_master
ON CONFLICT (district_id) DO NOTHING;
$$;
```

### Property → District Mapping

Links properties to districts.

```sql
INSERT INTO property_school_district (property_id, district_id)
SELECT
    p.id,
    sm.district_id
FROM properties p
JOIN school_master sm
ON p.zip_code = sm.zip_code
GROUP BY p.id, sm.district_id
ON CONFLICT DO NOTHING;
```

### Address-Based School Lookup (RPC)

Used for similarity-based property matching.

```sql
CREATE OR REPLACE FUNCTION get_property_school_scores(search_address text)
RETURNS TABLE (
    school_name text,
    level text,
    housmart_school_score numeric,
    s_academic numeric,
    s_resource numeric,
    s_equity numeric
)
LANGUAGE sql
AS $$
WITH closest_property AS (
    SELECT id
    FROM properties
    ORDER BY similarity(formatted_address, search_address) DESC
    LIMIT 1
)
SELECT
    sm.school_name,
    sm.level,
    sm.housmart_school_score,
    sm.s_academic,
    sm.s_resource,
    sm.s_equity
FROM closest_property cp
JOIN property_school_district psd
ON cp.id = psd.property_id
JOIN school_master sm
ON psd.district_id = sm.district_id
ORDER BY sm.housmart_school_score DESC;
$$;
```

## API Endpoint

**Endpoint:**

```
POST /api/property/school-scores
```

**Example request:**

```json
{
  "address": "5000 Main St, Houston, TX"
}
```

## Example Response

```json
{
  "zip_code": "77002",
  "total_schools": 4,
  "schools": [
    {
      "school_name": "LEADERSHIP ACADEMY",
      "level": "Secondary",
      "housmart_school_score": 47.48,
      "s_academic": 38.64,
      "s_resource": 40.0,
      "s_equity": 81.46
    }
  ]
}
```