
"""
HouSmart School Score v1
------------------------
Calculates a 0-100 HouSmart School Rating per school using three
weighted dimensions as specified in the HouSmart scoring algorithm.

SCORING ALGORITHM
=================

Final Score = (S_academic × 0.6) + (S_resource × 0.2) + (S_equity × 0.2)

1. ACADEMIC ACHIEVEMENT SCORE (S_academic) — 60% Weight
   Metric : SEDA cs_mn_avg_eb
   Method : Min-Max Normalization within state
            S_academic = (value - state_min) / (state_max - state_min) * 100
   Why    : Represents actual academic outcomes. Normalized within state
            to account for state-level testing differences.
            

2. RESOURCE & ATTENTION SCORE (S_resource) — 20% Weight
   Metric : Student-to-Teacher Ratio R = total_enrollment / teachers
   Logic  :
     R < 12        → 100 points  (excellent personalized attention)
     12 <= R <= 25 → linear decay: 100 - (R - 12) * 4.6
     R > 25        → 40 points   (overcrowded / understaffed)
   Why    : Lower ratio = more teacher attention per student = better outcomes.

3. SOCIO-ECONOMIC STABILITY SCORE (S_equity) — 20% Weight
   Metric : Inverse of Free/Reduced Lunch ratio
            S_equity = (1 - FRPL_rate/100) * 100
   Why    : In US real estate context, lower FRPL = higher economic health
            of local community = stronger property demand and school funding.

NULL HANDLING
=============
   - If a field is NULL, its weight is redistributed to available fields
   - score_confidence: high (3 fields) / medium (2 fields) / low (1 field)
   - housmart_school_score = NULL only when all 3 fields missing

Run:
    python3 school_score_v1.py
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parents[2]
load_dotenv(BACKEND_DIR / ".env")

SUPABASE_URL         = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client          = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# ================================================================
# WEIGHTS
# ================================================================
W_ACADEMIC  = 0.60
W_RESOURCE  = 0.20
W_EQUITY    = 0.20

# ================================================================
# COMPONENT SCORING FUNCTIONS
# ================================================================

def score_resource(ratio):
    """
    Student-to-Teacher Ratio scoring.
    R < 12        → 100
    12 <= R <= 25 → 100 - (R - 12) * 4.6
    R > 25        → 40
    """
    if ratio is None or np.isnan(ratio):
        return None
    if ratio < 12:
        return 100.0
    elif ratio <= 25:
        return round(100 - (ratio - 12) * 4.6, 1)
    else:
        return 40.0

def score_equity(frpl_rate):
    """
    Socio-economic stability = inverse of FRPL rate.
    S_equity = (1 - frpl_rate/100) * 100
    """
    if frpl_rate is None or np.isnan(frpl_rate):
        return None
    return round((1 - frpl_rate / 100) * 100, 1)

def compute_final_score(s_academic, s_resource, s_equity):
    """
    Weighted composite score with weight redistribution for NULLs.
    Returns (score, confidence, fields_used, fields_missing)
    """
    components = {
        "academic": (s_academic, W_ACADEMIC),
        "resource": (s_resource, W_RESOURCE),
        "equity":   (s_equity,   W_EQUITY),
    }

    available = {k: v for k, v in components.items() if v[0] is not None}
    missing   = [k for k, v in components.items() if v[0] is None]

    if not available:
        return None, "no_data", [], list(components.keys())

    # Redistribute weight from missing fields proportionally
    total_weight = sum(w for _, w in available.values())
    score = sum(val * (weight / total_weight)
                for val, weight in available.values())

    confidence = (
        "high"   if len(available) == 3 else
        "medium" if len(available) == 2 else
        "low"
    )

    return round(score, 1), confidence, list(available.keys()), missing

# ================================================================
# STEP 1: Load all schools from Supabase
# ================================================================
print("── Step 1: Loading schools from Supabase ──")
resp = supabase.table("school_master") \
    .select("ncessch, school_name, district_id, state, level, "
            "academic_score, frpl_rate, student_teacher_ratio") \
    .execute()
    

schools = resp.data
print(f"   Loaded {len(schools):,} schools")

# ================================================================
# STEP 2: Compute state-level min/max for academic normalization
# Min-Max within state as specified in algorithm
# ================================================================
print("\n── Step 2: Computing state-level academic min/max ──")
df = pd.DataFrame(schools)

# academic_score = cs_mn_avg_ol (raw SEDA value)
df["academic_score"] = pd.to_numeric(df["academic_score"], errors="coerce")

state_stats = df.groupby("state")["academic_score"].agg(["min", "max"]).reset_index()
state_stats.columns = ["state", "state_min", "state_max"]
df = df.merge(state_stats, on="state", how="left")

print(f"   States with academic data: {state_stats['state'].nunique()}")
print(f"   Sample state ranges:")
for _, row in state_stats.head(3).iterrows():
    print(f"     {row['state']}: {row['state_min']:.3f} → {row['state_max']:.3f}")

# ================================================================
# STEP 3: Compute scores for each school
# ================================================================
print("\n── Step 3: Computing scores ──")
results = []

for _, row in df.iterrows():
    # S_academic: Min-Max within state
    raw     = row.get("academic_score")
    s_min   = row.get("state_min")
    s_max   = row.get("state_max")

    if pd.notna(raw) and pd.notna(s_min) and pd.notna(s_max) and s_max != s_min:
        s_academic = round((raw - s_min) / (s_max - s_min) * 100, 1)
        s_academic = max(0, min(100, s_academic))  # clip to 0-100
    else:
        s_academic = None

    # S_resource: Student-to-Teacher Ratio scoring
    str_val    = row.get("student_teacher_ratio")
    str_val    = float(str_val) if str_val is not None and not (isinstance(str_val, float) and np.isnan(str_val)) else None
    s_resource = score_resource(str_val)

    # S_equity: Inverse FRPL rate
    frpl       = row.get("frpl_rate")
    frpl       = float(frpl) if frpl is not None and not (isinstance(frpl, float) and np.isnan(frpl)) else None
    s_equity   = score_equity(frpl)

    # Final composite score
    score, confidence, used, missing = compute_final_score(
        s_academic, s_resource, s_equity
    )

    results.append({
        "ncessch":               row["ncessch"],
        "housmart_school_score": score,
        "s_academic":            s_academic,
        "s_resource":            s_resource,
        "s_equity":              s_equity,
        "score_confidence":      confidence,
        "score_fields_used":     ", ".join(used) if used else "none",
        "score_fields_missing":  ", ".join(missing) if missing else "none",
    })

# ================================================================
# STEP 4: Summary report
# ================================================================
scored   = [r for r in results if r["housmart_school_score"] is not None]
unscored = [r for r in results if r["housmart_school_score"] is None]
high     = [r for r in results if r["score_confidence"] == "high"]
medium   = [r for r in results if r["score_confidence"] == "medium"]
low      = [r for r in results if r["score_confidence"] == "low"]

print(f"\n── Score Summary ──")
print(f"   Total schools    : {len(results)}")
print(f"   Scored           : {len(scored)}")
print(f"   Unscored (NULL)  : {len(unscored)}")
print(f"   High confidence  : {len(high)}   (all 3 fields)")
print(f"   Medium confidence: {len(medium)}  (2 fields)")
print(f"   Low confidence   : {len(low)}   (1 field only)")

if scored:
    scores = [r["housmart_school_score"] for r in scored]
    print(f"\n   Score range  : {min(scores):.1f} – {max(scores):.1f}")
    print(f"   Average score: {sum(scores)/len(scores):.1f}")

# ================================================================
# STEP 5: Preview top and bottom schools
# ================================================================
school_lookup = {s["ncessch"]: s for s in schools}
sorted_scored = sorted(scored, key=lambda x: x["housmart_school_score"], reverse=True)

print("\n── Top 10 Schools ──")
for r in sorted_scored[:10]:
    s = school_lookup.get(r["ncessch"], {})
    print(f"   {r['housmart_school_score']:5.1f} | "
          f"{str(s.get('school_name',''))[:35]:35s} | "
          f"{str(s.get('level','')):10s} | "
          f"acad={r['s_academic']} res={r['s_resource']} eq={r['s_equity']}")

print("\n── Bottom 10 Schools ──")
for r in sorted_scored[-10:]:
    s = school_lookup.get(r["ncessch"], {})
    print(f"   {r['housmart_school_score']:5.1f} | "
          f"{str(s.get('school_name',''))[:35]:35s} | "
          f"{str(s.get('level',''))[:10]:10s} | "
          f"acad={r['s_academic']} res={r['s_resource']} eq={r['s_equity']}")

# ================================================================
# STEP 6: Upsert to Supabase


print("\n── Upserting scores to school_master ──")
try:
    for i in range(0, len(results), 500):
        chunk = results[i:i+500]
        supabase.table("school_master") \
            .upsert(chunk, on_conflict="ncessch") \
            .execute()
        print(f"   Upserted {i+1}–{min(i+500, len(results))}")
    print(f"\n {len(results)} school scores upserted to school_master")
except Exception as e:
    print(f"  Upsert failed: {e}")
    print("   Run the ALTER TABLE SQL in Supabase SQL Editor first")
