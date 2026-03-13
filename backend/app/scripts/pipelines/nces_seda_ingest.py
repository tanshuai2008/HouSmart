
"""
HouSmart — NCES CCD + SEDA School Master Pipeline
---------------------------------------------------
Produces: school_master table in Supabase

Join sequence (all LEFT JOINs on NCESSCH):
  1. NCES Directory          → school name, district, state, level, charter flag
  2. NCES Membership         → total enrollment
  3. NCES Staff              → teacher count → student_teacher_ratio
  4. NCES Lunch              → FRPL count → frpl_rate
  5. NCES School Characteristics → NSLP status, virtual flag
  6. SEDA 6.0                → academic_score, growth_score

SEDA: subgroup='all', subcat='all', gap=0 — confirmed, no filter needed.
Primary Key: NCESSCH (12-digit string, zero-padded throughout)

Files needed in same folder as this script:
  - ccd_sch_029_2223_w_1a_083023-directory.csv
  - ccd_sch_052_2223_l_1a_083023-membership.csv
  - ccd_sch_059_2223_l_1a_083023--staff.csv
  - ccd_sch_033_2223_l_1a_083023-lunch.csv
  - ccd_sch_129_2223_w_1a_083023-schoolChar.csv
  - seda_school_pool_cs_6.0.csv

Run:
    python3 nces_seda_ingest.py
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parents[3]
load_dotenv(BACKEND_DIR / ".env")

SUPABASE_URL         = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client          = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

OUTPUT_DIR = SCRIPT_DIR / "output"
OUTPUT_FILE = OUTPUT_DIR / "school_master.csv"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ================================================================
# STEP 1: Load NCES Directory
# Gives: school name, district, address, level, charter flag
# ================================================================
print("── Step 1: Loading NCES Directory ──")
dir_df = pd.read_csv(
    SCRIPT_DIR / "ccd_sch_029_2223_w_1a_083023-directory.csv",
    low_memory=False, encoding="latin-1"
)
print(f"   Rows: {len(dir_df):,}")

dir_df = dir_df[[
    "NCESSCH", "SCH_NAME", "LEA_NAME", "LEAID",
    "ST", "STATENAME", "MZIP", "LEVEL",
    "CHARTER_TEXT", "SCH_TYPE_TEXT", "SY_STATUS_TEXT",
    "GSLO", "GSHI"
]].copy()

# 12-digit zero-padded string
dir_df["NCESSCH"] = dir_df["NCESSCH"].astype(str).str.zfill(12)
dir_df["LEAID"]   = dir_df["LEAID"].astype(str).str.zfill(7)

# Only keep open schools
dir_df = dir_df[dir_df["SY_STATUS_TEXT"] == "Open"].copy()
print(f"   Active schools: {len(dir_df):,}")

# ================================================================
# STEP 2: Load NCES Membership (enrollment)
# Filter: TOTAL_INDICATOR == 'Education Unit Total'
# ================================================================
print("\n── Step 2: Loading NCES Membership ──")
try:
    mem_df = pd.read_csv(
        SCRIPT_DIR / "ccd_sch_052_2223_l_1a_083023-membership.csv",
        low_memory=False, encoding="latin-1"
    )
    print(f"   Rows: {len(mem_df):,}")

    mem_df["NCESSCH"]       = mem_df["NCESSCH"].astype(str).str.zfill(12)
    mem_df["STUDENT_COUNT"] = pd.to_numeric(mem_df["STUDENT_COUNT"], errors="coerce")

    enroll = mem_df[mem_df["TOTAL_INDICATOR"] == "Education Unit Total"].copy()
    enroll = enroll.groupby("NCESSCH")["STUDENT_COUNT"].sum().reset_index()
    enroll.columns = ["NCESSCH", "total_enrollment"]
    print(f"   Schools with enrollment: {enroll['NCESSCH'].nunique():,}")

except FileNotFoundError:
    print("   ⚠️  Membership file not found — enrollment will be NULL")
    enroll = pd.DataFrame(columns=["NCESSCH", "total_enrollment"])

# ================================================================
# STEP 3: Load NCES Staff (teacher counts)
# TOTAL_INDICATOR has only 'Education Unit Total' — no filter needed
# ================================================================
print("\n── Step 3: Loading NCES Staff ──")
try:
    staff_df = pd.read_csv(
        SCRIPT_DIR / "ccd_sch_059_2223_l_1a_083023--staff.csv",
        low_memory=False, encoding="latin-1"
    )
    print(f"   Rows: {len(staff_df):,}")

    staff_df["NCESSCH"]  = staff_df["NCESSCH"].astype(str).str.zfill(12)
    staff_df["TEACHERS"] = pd.to_numeric(staff_df["TEACHERS"], errors="coerce")
    staff_clean          = staff_df[["NCESSCH", "TEACHERS"]].copy()
    print(f"   Schools with teacher data: {staff_clean['NCESSCH'].nunique():,}")

except FileNotFoundError:
    print("   ⚠️  Staff file not found — student_teacher_ratio will be NULL")
    staff_clean = pd.DataFrame(columns=["NCESSCH", "TEACHERS"])

# ================================================================
# STEP 4: Load NCES Lunch Program (FRPL)
# free_lunch_n + reduced_lunch_n → frpl_rate
# ================================================================
print("\n── Step 4: Loading NCES Lunch ──")
try:
    lunch_df = pd.read_csv(
        SCRIPT_DIR / "ccd_sch_033_2223_l_1a_083023-lunch.csv",
        low_memory=False, encoding="latin-1"
    )
    print(f"   Rows: {len(lunch_df):,}")
    print(f"   LUNCH_PROGRAM values: {lunch_df['LUNCH_PROGRAM'].unique()}")

    lunch_df["NCESSCH"]       = lunch_df["NCESSCH"].astype(str).str.zfill(12)
    lunch_df["STUDENT_COUNT"] = pd.to_numeric(lunch_df["STUDENT_COUNT"], errors="coerce").fillna(0)

    free = lunch_df[
        lunch_df["LUNCH_PROGRAM"] == "Free lunch qualified"
    ].groupby("NCESSCH")["STUDENT_COUNT"].sum().reset_index()
    free.columns = ["NCESSCH", "free_lunch_n"]

    reduced = lunch_df[
        lunch_df["LUNCH_PROGRAM"] == "Reduced-price lunch qualified"
    ].groupby("NCESSCH")["STUDENT_COUNT"].sum().reset_index()
    reduced.columns = ["NCESSCH", "reduced_lunch_n"]

    frpl = free.merge(reduced, on="NCESSCH", how="outer").fillna(0)
    frpl["frpl_total"] = frpl["free_lunch_n"] + frpl["reduced_lunch_n"]
    print(f"   Schools with FRPL data: {len(frpl):,}")

except FileNotFoundError:
    print("   ⚠️  Lunch file not found — frpl_rate will be NULL")
    frpl = pd.DataFrame(columns=["NCESSCH", "free_lunch_n", "reduced_lunch_n", "frpl_total"])

# ================================================================
# STEP 5: Load NCES School Characteristics
# Gives: NSLP participation status, virtual school flag
# ================================================================
print("\n── Step 5: Loading NCES School Characteristics ──")
try:
    char_df = pd.read_csv(
        SCRIPT_DIR / "ccd_sch_129_2223_w_1a_083023-schoolChar.csv",
        low_memory=False, encoding="latin-1"
    )
    print(f"   Rows: {len(char_df):,}")
    print(f"   NSLP_STATUS values  : {char_df['NSLP_STATUS_TEXT'].unique()}")
    print(f"   VIRTUAL values      : {char_df['VIRTUAL_TEXT'].unique()}")

    char_df["NCESSCH"] = char_df["NCESSCH"].astype(str).str.zfill(12)
    char_clean = char_df[["NCESSCH", "NSLP_STATUS_TEXT", "VIRTUAL_TEXT"]].copy()
    char_clean.columns = ["NCESSCH", "nslp_status", "is_virtual"]
    print(f"   Schools in char file: {char_clean['NCESSCH'].nunique():,}")

except FileNotFoundError:
    print("   ⚠️  School characteristics file not found")
    char_clean = pd.DataFrame(columns=["NCESSCH", "nslp_status", "is_virtual"])

# ================================================================
# STEP 6: Load SEDA 6.0
# academic_score = cs_mn_avg_eb (Empirical Bayes — stable for small schools)
# growth_score   = cs_mn_lrn_eb
# No filter needed — file is already subgroup='all', gap=0 only
# ================================================================
print("\n── Step 6: Loading SEDA 6.0 ──")
seda = pd.read_csv(SCRIPT_DIR / "seda_school_pool_cs_6.0.csv", low_memory=False)
print(f"   Rows: {len(seda):,}, Unique schools: {seda['sedasch'].nunique():,}")

# Zero-pad to 12 digits
seda["sedasch"] = seda["sedasch"].astype(str).str.split(".").str[0].str.zfill(12)

seda_clean = seda[[
    "sedasch",
    "cs_mn_avg_eb",   # academic score — Empirical Bayes overall
    "cs_mn_lrn_eb",   # growth score  — Empirical Bayes
    "cs_mn_mth_eb",   # math score    — Empirical Bayes
]].copy()
seda_clean.columns = ["NCESSCH", "academic_score", "growth_score", "math_score"]
print(f"   Schools with academic score : {seda_clean['academic_score'].notna().sum():,}")
print(f"   Schools with growth score   : {seda_clean['growth_score'].notna().sum():,}")

# ================================================================
# STEP 7: Use full directory (no filtering)
# ================================================================
print("\n── Step 7: Using full directory ──")
before = len(dir_df)

# ================================================================
# STEP 8: LEFT JOIN sequence — no school ever dropped
# Directory → Membership → Staff → Lunch → Characteristics → SEDA
# ================================================================
print("\n── Step 8: Joining all sources ──")
master = dir_df.copy()
before = len(master)

master = master.merge(enroll,     on="NCESSCH", how="left")
print(f"   After membership join      : {len(master):,} rows")

master = master.merge(staff_clean, on="NCESSCH", how="left")
print(f"   After staff join           : {len(master):,} rows")

master = master.merge(
    frpl[["NCESSCH", "free_lunch_n", "reduced_lunch_n", "frpl_total"]],
    on="NCESSCH", how="left"
)
print(f"   After lunch join           : {len(master):,} rows")

master = master.merge(char_clean,  on="NCESSCH", how="left")
print(f"   After characteristics join : {len(master):,} rows")

master = master.merge(seda_clean,  on="NCESSCH", how="left")
print(f"   After SEDA join            : {len(master):,} rows")

assert len(master) == before, f" Row count changed! {before} → {len(master)}"
print(f"   Row count stable — 100% school retention confirmed")

# ================================================================
# STEP 9: Compute derived fields
# ================================================================
print("\n── Step 9: Computing derived fields ──")

# FRPL rate = (free + reduced) / total_enrollment * 100
if "total_enrollment" in master.columns and "frpl_total" in master.columns:
    master["frpl_rate"] = np.where(
        (master["total_enrollment"] > 0) & master["frpl_total"].notna(),
        (master["frpl_total"] / master["total_enrollment"] * 100).round(1),
        np.nan
    )
else:
    master["frpl_rate"] = np.nan

# Student/teacher ratio = total_enrollment / TEACHERS
if "TEACHERS" in master.columns and "total_enrollment" in master.columns:
    master["student_teacher_ratio"] = np.where(
        (master["TEACHERS"] > 0) & master["total_enrollment"].notna(),
        (master["total_enrollment"] / master["TEACHERS"]).round(1),
        np.nan
    )
else:
    master["student_teacher_ratio"] = np.nan

# National academic percentile (vs all US schools in SEDA)
national_scores = seda_clean["academic_score"].dropna()
def to_pct(score):
    if pd.isna(score): return None
    return round(float(np.mean(national_scores <= score) * 100), 1)

master["academic_percentile"] = master["academic_score"].apply(to_pct)
national_growth = seda_clean["growth_score"].dropna()
national_math   = seda_clean["math_score"].dropna()

master["growth_percentile"] = master["growth_score"].apply(
    lambda x: round(float(np.mean(national_growth <= x) * 100), 1) if pd.notna(x) else None
)
master["math_percentile"] = master["math_score"].apply(
    lambda x: round(float(np.mean(national_math <= x) * 100), 1) if pd.notna(x) else None
)

print(f"   FRPL rate computed for      : {master['frpl_rate'].notna().sum()} schools")
print(f"   STR computed for            : {master['student_teacher_ratio'].notna().sum()} schools")
print(f"   Academic percentile for     : {master['academic_percentile'].notna().sum()} schools")

# ================================================================
# STEP 10: State-Relative Normalization & Weighting
# ================================================================
print("\n── Step 10: State-Relative Normalization & Weighting ──")

# 1. State-wide stats for academic normalization (ST is the state code)
state_stats = master.groupby("ST")["academic_score"].agg(["min", "max"]).reset_index()
state_stats.columns = ["ST", "state_min", "state_max"]
master = master.merge(state_stats, on="ST", how="left")

# Normalized Academic Score (0-100)
master["s_academic"] = np.where(
    (master["academic_score"].notna()) & (master["state_max"] != master["state_min"]),
    ((master["academic_score"] - master["state_min"]) / (master["state_max"] - master["state_min"])) * 100,
    None
)
master["s_academic"] = master["s_academic"].apply(lambda x: max(0, min(100, x)) if pd.notna(x) else None)

# 2. Resource Score (Student-Teacher Ratio logic)
def calculate_resource_score(r):
    if pd.isna(r) or (isinstance(r, float) and np.isnan(r)): return None
    if r < 12: return 100
    elif r <= 25: return 100 - (r - 12) * 4.6
    else: return 40
master["s_resource"] = master["student_teacher_ratio"].apply(calculate_resource_score)

# 3. Equity Score (Inverse of FRPL)
master["s_equity"] = np.where(master["frpl_rate"].notna(), (1 - master["frpl_rate"] / 100) * 100, None)

# 4. Final Weighted Score with Strict Academic-First Logic
def calculate_housmart_score(row):
    # Mandatory Academic Score
    if pd.isna(row["s_academic"]):
        return None, "none"

    has_res = pd.notna(row["s_resource"])
    has_equ = pd.notna(row["s_equity"])

    # Case 1: All 3 components present (60/20/20)
    if has_res and has_equ:
        score = (row["s_academic"] * 0.6) + (row["s_resource"] * 0.2) + (row["s_equity"] * 0.2)
        confidence = "high"
    
    # Case 2: Academic + One other (75/25 redistribution)
    elif has_res or has_equ:
        other_val = row["s_resource"] if has_res else row["s_equity"]
        # (0.6 / 0.8) = 0.75 | (0.2 / 0.8) = 0.25
        score = (row["s_academic"] * 0.75) + (other_val * 0.25)
        confidence = "medium"
    
    # Case 3: ONLY Academic (100%)
    else:
        score = row["s_academic"]
        confidence = "low"
    
    return round(score, 1), confidence

# Apply the scoring function
scored_data = master.apply(calculate_housmart_score, axis=1)
master["housmart_school_score"] = scored_data.apply(lambda x: x[0])
master["score_confidence"] = scored_data.apply(lambda x: x[1])

# Confidence Level cleanup
master["score_confidence"] = master["score_confidence"].fillna("none")

# Tracks which fields were used/missing for weight redistribution
def get_fields_str(row, target_val):
    comp_cols = ["s_academic", "s_resource", "s_equity"]
    fields = [col.replace("s_", "") for col in comp_cols if (pd.notna(row[col])) == target_val]
    return ", ".join(fields)

master["score_fields_used"] = master.apply(lambda r: get_fields_str(r, True), axis=1)
master["score_fields_missing"] = master.apply(lambda r: get_fields_str(r, False), axis=1)

print(f"   Schools scored (Academic-First) : {master['housmart_school_score'].notna().sum():,}")

# ================================================================
# STEP 11: Build final schema
# ================================================================
print("\n── Step 11: Build final schema ──")
school_master = pd.DataFrame({
    "ncessch":               master["NCESSCH"],
    "school_name":           master["SCH_NAME"],
    "district_name":         master["LEA_NAME"],
    "district_id":           master["LEAID"],
    "state":                 master["ST"],
    "level":                 master["LEVEL"],
    "zip_code":              master["MZIP"].astype(str),
    "grade_low":             master["GSLO"],
    "grade_high":            master["GSHI"],
    "charter_flag":          master["CHARTER_TEXT"],
    "school_type":           master["SCH_TYPE_TEXT"],
    "nslp_status":           master.get("nslp_status"),
    "is_virtual":            master.get("is_virtual"),
    "total_enrollment":      master.get("total_enrollment"),
    "student_teacher_ratio": master["student_teacher_ratio"],
    "free_lunch_n":          master.get("free_lunch_n"),
    "reduced_lunch_n":       master.get("reduced_lunch_n"),
    "frpl_rate":             master["frpl_rate"],
    "academic_score":        master["academic_score"],
    "growth_score":          master["growth_score"],
    "math_score":            master["math_score"],
    "academic_percentile":   master["academic_percentile"],
    "growth_percentile":     master["growth_percentile"],
    "math_percentile":       master["math_percentile"],
    "s_academic":            master["s_academic"],
    "s_resource":            master["s_resource"],
    "s_equity":              master["s_equity"],
    "housmart_school_score": master["housmart_school_score"],
    "score_confidence":      master["score_confidence"],
    "score_fields_used":     master["score_fields_used"],
    "score_fields_missing":  master["score_fields_missing"],
})

# ================================================================
# STEP 12: Coverage report + sample
# ================================================================
print(f"\n── Coverage Report ──")
print(f"   Total schools: {len(school_master)}")
for col in [
    "school_name", "total_enrollment", "student_teacher_ratio",
    "frpl_rate", "nslp_status", "academic_score", "housmart_school_score"
]:
    filled = school_master[col].notna().sum()
    print(f"   {col:25s}: {filled}/{len(school_master)}")

print(f"\n── Sample Output ──")
print(school_master[[
    "ncessch", "school_name", "level", "housmart_school_score",
    "score_fields_used", "score_fields_missing"
]].head(10).to_string())

# ================================================================
# STEP 13: Save CSV
# ================================================================
print("\n── Step 13: Saving output ──")
school_master.to_csv(OUTPUT_FILE, index=False)
print(f"\n CSV saved → {OUTPUT_FILE}")

# ================================================================
# STEP 14: Upsert to Supabase in chunks of 500
# ================================================================
print("\n── Step 14: Upserting to Supabase school_master ──")
records = school_master.where(pd.notnull(school_master), None).to_dict("records")

for r in records:
    for k, v in r.items():
        if v is None:
            continue
        elif isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            r[k] = None
        elif isinstance(v, np.integer):    r[k] = int(v)
        elif isinstance(v, np.floating):   r[k] = None if (np.isnan(v) or np.isinf(v)) else float(v)
        elif isinstance(v, np.bool_):      r[k] = bool(v)

try:
    for i in range(0, len(records), 500):
        chunk = records[i:i + 500]
        supabase.table("school_master") \
            .upsert(chunk, on_conflict="ncessch") \
            .execute()
        print(f"   Upserted rows {i + 1}–{min(i + 500, len(records))}")
    print(f"\n {len(records)} schools upserted to school_master")
except Exception as e:
    print(f"  Upsert failed: {e}")
    print("   Make sure you ran the CREATE TABLE SQL in Supabase first")
