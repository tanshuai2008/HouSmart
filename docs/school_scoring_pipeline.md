# HouSmart School Scoring Pipeline

## Objective

calculates a normalized **0–100 rating for every U.S. public school** using NCES and SEDA datasets.
The system powers the **/property/school-scores API**, allowing users to send an address and receive a ranked list of nearby schools.

The pipeline performs:

1. **Data ingestion** from NCES and SEDA datasets
2. **Feature engineering** (student–teacher ratio, FRPL rate)
3. **Score computation** (academic, resource, equity)
4. **Upload to Supabase** (`school_master` table)
5. **District synchronization**
6. **Property → district mapping**
7. **FastAPI endpoint for school ranking**

---

# System Architecture

User Request

↓

FastAPI API

↓

Google Maps Geocoding (Address → ZIP)

↓

Supabase Query (ZIP → District → Schools)

↓

HouSmart Ranking Algorithm

↓

Ranked School Results

---

# Data Sources

## 1. NCES Common Core of Data

Provides core school information.

Datasets used:

| Dataset                  | Purpose                 |
| ------------------------ | ----------------------- |
| `ccd_sch_029_directory`  | School directory        |
| `ccd_sch_052_membership` | Enrollment counts       |
| `ccd_sch_059_staff`      | Teacher counts          |
| `ccd_sch_033_lunch`      | Free/Reduced lunch data |

---

## 2. SEDA Dataset

Provides academic performance metrics.

Dataset:

| Dataset                       | Metric               |
| ----------------------------- | -------------------- |
| `seda_school_pool_cs_6.0.csv` | Academic achievement |

We use:

```
cs_mn_avg_eb
```

Which represents **education-adjusted academic achievement**.

---

# HouSmart School Score Algorithm

Final Score:

```
Score = (0.6 × Academic) + (0.2 × Resource) + (0.2 × Equity)
```

## 1. Academic Score (60%)

Metric:

```
cs_mn_avg_eb
```

Normalized per state:

```
S_academic = (value − state_min) / (state_max − state_min) × 100
```

---

## 2. Resource Score (20%)

Metric:

```
student_teacher_ratio
```

Formula:

| Ratio | Score        |
| ----- | ------------ |
| < 12  | 100          |
| 12–25 | Linear decay |
| > 25  | 40           |

Implementation:

```
score = 100 − (ratio − 12) × 4.6
```

---

## 3. Equity Score (20%)

Metric:

```
FRPL rate
```

Formula:

```
S_equity = (1 − FRPL_rate/100) × 100
```

Lower poverty → higher score.

---

# Data Pipeline

Script:

```
backend/app/data/nces_seda_ingest.py
```

Pipeline steps:

1. Load NCES datasets
2. Load SEDA dataset
3. Merge datasets
4. Compute ratios
5. Normalize academic score
6. Compute HouSmart score
7. Clean NaN values
8. Upload to Supabase

---

# Database Tables

## school_master

Main dataset (~100k schools)

| Column                | Description               |
| --------------------- | ------------------------- |
| ncessch               | School ID                 |
| school_name           | School name               |
| district_id           | District ID               |
| zip_code              | School ZIP                |
| academic_score        | Raw academic metric       |
| s_academic            | Normalized academic score |
| s_resource            | Resource score            |
| s_equity              | Equity score              |
| housmart_school_score | Final score               |

---

## school_districts

District reference table.

| Column        | Description   |
| ------------- | ------------- |
| district_id   | District ID   |
| district_name | District name |
| state         | State         |

---

## property_school_district

Links properties to districts.

| Column      | Description   |
| ----------- | ------------- |
| property_id | Property UUID |
| district_id | District ID   |

---

# Automatic District Sync

SQL Function:

```
sync_school_districts()
```

```
INSERT INTO school_districts
SELECT DISTINCT district_id, district_name, state
FROM school_master
ON CONFLICT DO NOTHING
```

Ensures districts stay updated.

---

# Property Mapping

Function:

```
map_properties_to_districts()
```

Maps properties using ZIP codes:

```
properties.zip_code = school_master.zip_code
```

This populates `property_school_district`.

---

# API Endpoint

Route:

```
POST /property/school-scores
```

Example request:

```
{
 "address": "5000 Main St, Houston, TX"
}
```

---

# Google Maps Integration

Used to convert address → ZIP code.

Service:

```
geocode_service.py
```

API:

```
Google Maps Geocoding API
```

---

# School Query Logic

Process:

1. Address → ZIP
2. ZIP → District
3. District → Schools
4. Sort by HouSmart score

Query:

```
ORDER BY housmart_school_score DESC
```

Top schools returned.

---

# Example Response

```
{
 "zip_code": "30308",
 "total_schools": 10,
 "schools": [
   {
     "school_name": "Springdale Park Elementary",
     "housmart_school_score": 72.4
   },
   {
     "school_name": "Midtown High School",
     "housmart_school_score": 65.1
   }
 ]
}
```

---

# Performance Optimizations

Indexes added:

```
CREATE INDEX idx_school_zip
ON school_master(zip_code);

CREATE INDEX idx_school_district
ON school_master(district_id);
```

Benefits:

• Fast school lookup
• Low latency API responses (~5–20ms)

---

# Final Result

The system now supports:

✔ 99k+ U.S. schools
✔ Academic + resource + equity scoring
✔ Automatic district mapping
✔ Fast API queries
✔ Ranked school recommendations

The HouSmart pipeline is now **fully operational and production ready**.

---

# Next Improvements

Potential upgrades:

• Distance-based school search
• GIS district boundary matching
• School trend prediction models
• Property investment scoring

---

**Project:** HouSmart AI
**Module:** School Scoring Engine
**Author:** Ahmed Sherif
**Year:** 2026
