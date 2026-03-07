# HouSmart School Data Integration & Scoring Pipeline

## Description
This service ingests, processes, and normalizes national school data to generate a proprietary 0–100 HouSmart School Rating for real estate properties. It maps individual properties to their respective school districts and calculates composite scores based on academic achievement, resource allocation, and socio-economic equity. It exposes a FastAPI endpoint to fetch these scores via a fuzzy-matching address search.

## Input and Output Format
**API Endpoint:** `POST /property/school-scores`

**Input:** A JSON payload containing a property address string.
```json
{
  "address": "100 N CANON DR, BEVERLY HILLS, CA"
}
```
**Output:** A JSON response containing the closest matched property and its associated schools, ordered by the highest HouSmart score.
```json
{
  "address": "100 N CANON DR, BEVERLY HILLS, CA",
  "total_schools_found": 1,
  "schools": [
    {
      "school_name": "Beverly Hills High",
      "level": "High",
      "housmart_school_score": 85.2,
      "s_academic": 88.0,
      "s_resource": 75.0,
      "s_equity": 90.5
    }
  ]
}

```
## APIs, Data Sources, and Column Mapping
National Center for Education Statistics (NCES) Common Core of Data (CCD): Provides school directory information, student enrollment, teacher counts, and Free/Reduced Price Lunch (FRPL) statistics.

Stanford Educational Opportunity Project (SEDA) Version 6.0: Pooled national cohort data. Provides empirical-bayes academic and growth scores.

Supabase (PostgreSQL): Utilizes pg_trgm for fuzzy text matching and PostGIS for spatial geometry mapping.

(Note: Initial exploration utilized the SchoolDigger API, but the architecture was pivoted to direct NCES/SEDA ingestion.

The `school_master` table is synthesized from multiple raw government CSVs and proprietary calculations. Below is the exact mapping of where each column originates:

### 1. NCES Common Core of Data (CCD) 2022-2023
* **Directory File (`ccd_sch_029...-directory.csv`)**
  * `ncessch` (Primary Key)
  * `school_name`
  * `district_name` & `district_id`
  * `state` & `zip_code`
  * `level` (Elementary/Middle/High)
  * `grade_low` & `grade_high`
  * `charter_flag` & `school_type`
* **Membership/Enrollment File (`ccd_sch_052...-membership.csv`)**
  * `total_enrollment`
* **Staff File (`ccd_sch_059...--staff.csv`)**
  * Provides raw teacher counts used to calculate `student_teacher_ratio`.
* **Lunch Program File (`ccd_sch_033...-lunch.csv`)**
  * `free_lunch_n`
  * `reduced_lunch_n`
  * Provides raw counts used to calculate `frpl_rate`.
* **School Characteristics File (`ccd_sch_129...-schoolChar.csv`)**
  * `nslp_status`
  * `is_virtual`

### 2. Stanford Educational Opportunity Project (SEDA) v6.0
* **School Pool CS File (`seda_school_pool_cs_6.0.csv`)**
  * `academic_score` *(Derived from `cs_mn_avg_eb`)*
  * `growth_score` *(Derived from `cs_mn_lrn_eb`)*
  * `math_score` *(Derived from `cs_mn_mth_eb`)*


### 3. HouSmart Derived & Computed Columns
These columns do not exist in the raw files and are calculated dynamically during the Python ingestion and scoring pipelines:
* **Ingestion Pipeline (`nces_seda_ingest.py`)**:
  * `student_teacher_ratio`: Total Enrollment / Total Teachers
  * `frpl_rate`: (Free + Reduced Lunch) / Total Enrollment * 100
  * `academic_percentile`: National percentile ranking (0-100) based on `academic_score`
  * `growth_percentile`: National percentile ranking based on `growth_score`
  * `math_percentile`: National percentile ranking based on `math_score`
* **Scoring Algorithm (`school_score_v1.py`)**:
  * `housmart_school_score`: Final 0-100 composite rating
  * `s_academic`: 0-100 normalized state-level academic dimension
  * `s_resource`: 0-100 resource dimension
  * `s_equity`: 0-100 equity dimension
  * `score_confidence`: High/Medium/Low based on data availability
  * `score_fields_used` & `score_fields_missing`: Tracks which fields were null for weight redistribution

  ### 4. SchoolDigger API
* **School Rankings & Metadata:** Utilized to fetch state-level school rankings, district-level rankings, and supplementary school performance metrics to enrich the dataset.

**Assumptions and Limitations**
Fuzzy Matching Threshold: The API uses a trigram similarity threshold (> 0.2) to match user input to the database. If an address is drastically misspelled, it may return empty results to prevent false positives.

Missing Academic Data: High schools frequently lack standard SEDA testing scores (which heavily target grades 3–8). The scoring algorithm assumes this is normal and dynamically redistributes the 60% academic weight to the Resource and Equity dimensions.

Pre-Mapped Districts: The API assumes that properties have already been spatially mapped to district IDs in the property_school_district table.

**Scoring Algorithm Details:**
The HouSmart rating is a composite score calculated via three weighted dimensions:

Academic Achievement Score (60% Weight): Min-Max normalization applied within the state using SEDA pooled average scores.

Resource & Attention Score (20% Weight): Based on the Student-to-Teacher Ratio (ideal is < 12).

Socio-Economic Stability Score (20% Weight): The inverse of the Free/Reduced Lunch Ratio, acting as a proxy for community economic health and funding stability.