"""
test_db_writes.py
-----------------
Tests the full end-to-end flow:
  1. Real Gemini API call
  2. Write result to property_ai_summary
  3. Write token/cost log to ai_usage_logs
  4. Read both back and confirm

Run from backend/:
    source venv/bin/activate
    python test_db_writes.py
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv(override=True)  # must be before app imports

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from supabase import create_client
from app.intelligence.builder import build_base_payload
from app.intelligence.recommendation import run_recommendation
from app.intelligence.validator import validate_ai_output
from app.intelligence.logger import log_usage

# ── Test evaluation data ───────────────────────────────────────────────────

EVALUATION_ID = "test-db-write-001"

evaluation_data = {
    "evaluation_id": EVALUATION_ID,
    "verdict_color": "yellow",
    "property": {
        "formatted_address": "350 5th Ave, New York, NY 10118",
        "state": "TX",
        "zip_code": "10118",
        "bedrooms": 3,
        "bathrooms": 2.0,
        "square_feet": 1400,
        "year_built": 2005,
        "property_type": "single_family",
    },
    "financials": {
        "monthly_cash_flow": 320,
        "cap_rate": 0.052,
        "roi_5yr": 0.18,
        "estimated_value": 420000,
    },
    "variables": {
        "estimated_rent":    {"status": "ready", "value": 2400,   "source": "RentCast"},
        "crime_score":       {"status": "ready", "value": 62,     "source": "FBI UCR"},
        "school_score":      {"status": "failed"},
        "transit_score":     {"status": "ready", "value": 75,     "source": "OSM"},
        "flood_risk_score":  {"status": "ready", "value": 90,     "source": "FEMA"},
        "amenity_score":     {"status": "ready", "value": 80,     "source": "OSM"},
        "noise_score":       {"status": "ready", "value": 70,     "source": "OSM"},
        "median_income":     {"status": "ready", "value": 68000,  "source": "ACS"},
        "median_home_value": {"status": "ready", "value": 410000, "source": "ACS"},
        "vacancy_rate":      {"status": "ready", "value": 0.041,  "source": "ACS"},
    },
}

priority_ranking = [
    {"factor": "roi",     "rank": 1},
    {"factor": "safety",  "rank": 2},
    {"factor": "schools", "rank": 3},
]


def _header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


# ── 1. Connect to Supabase ─────────────────────────────────────────────────

_header("STEP 1 — Supabase connection")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ SUPABASE_URL or SUPABASE_KEY missing from .env")
    sys.exit(1)

db = create_client(SUPABASE_URL, SUPABASE_KEY)
print("✅ Supabase client created")


# ── 2. Real Gemini call ────────────────────────────────────────────────────

_header("STEP 2 — Real Gemini API call")

payload = build_base_payload(evaluation_data, priority_ranking)
print(f"  Payload built — completeness: {payload['data_completeness_pct']}%")

raw_output = run_recommendation(payload, policy_summary=None)
print(f"  Gemini responded ✅")
print(f"  Model  : {raw_output['_meta']['model']}")
print(f"  Tokens : input={raw_output['_meta']['input_tokens']} output={raw_output['_meta']['output_tokens']}")


# ── 3. Validate ────────────────────────────────────────────────────────────

_header("STEP 3 — Validate AI output")

validated = validate_ai_output(raw_output, payload)
print(f"  admin_review_required : {validated['admin_review_required']}")
print(f"  validation_errors     : {validated['validation_errors']}")
print(f"  validation_warnings   : {validated['validation_warnings']}")


# ── 4. Write to property_ai_summary ───────────────────────────────────────

_header("STEP 4 — Write to property_ai_summary")

try:
    db.table("property_ai_summary").upsert({
        "evaluation_id":         EVALUATION_ID,
        "property_id":           "test-property-001",
        "recommendation":        validated.get("verdict_color", payload.get("verdict_color")),
        "traffic_light":         payload.get("verdict_color"),
        "confidence_score":      payload.get("data_completeness_pct"),
        "summary":               validated.get("verdict_explanation"),
        "full_output":           validated,
        "admin_review_required": validated.get("admin_review_required", False),
    }, on_conflict="evaluation_id").execute()
    print("  ✅ property_ai_summary write succeeded")
except Exception as e:
    print(f"  ❌ property_ai_summary write FAILED: {e}")
    sys.exit(1)


# ── 5. Write to ai_usage_logs ──────────────────────────────────────────────

_header("STEP 5 — Write to ai_usage_logs")

try:
    log_usage(
        evaluation_id=EVALUATION_ID,
        model_used=validated["_meta"]["model"],
        policy_summary=None,
        result=validated,
        db_session=db,
    )
    print("  ✅ ai_usage_logs write succeeded")
except Exception as e:
    print(f"  ❌ ai_usage_logs write FAILED: {e}")
    sys.exit(1)


# ── 6. Read back and confirm ───────────────────────────────────────────────

_header("STEP 6 — Read back from DB and confirm")

# Read property_ai_summary
summary_resp = db.table("property_ai_summary") \
    .select("evaluation_id, traffic_light, confidence_score, admin_review_required, created_at") \
    .eq("evaluation_id", EVALUATION_ID) \
    .single() \
    .execute()

if summary_resp.data:
    print("  property_ai_summary row:")
    print(f"    evaluation_id         : {summary_resp.data['evaluation_id']}")
    print(f"    traffic_light         : {summary_resp.data['traffic_light']}")
    print(f"    confidence_score      : {summary_resp.data['confidence_score']}")
    print(f"    admin_review_required : {summary_resp.data['admin_review_required']}")
    print(f"    created_at            : {summary_resp.data['created_at']}")
    print("  ✅ property_ai_summary confirmed in DB")
else:
    print("  ❌ Could not read back from property_ai_summary")

# Read ai_usage_logs
logs_resp = db.table("ai_usage_logs") \
    .select("evaluation_id, model_used, total_tokens, estimated_cost_usd, logged_at") \
    .eq("evaluation_id", EVALUATION_ID) \
    .order("logged_at", desc=True) \
    .limit(1) \
    .execute()

if logs_resp.data:
    row = logs_resp.data[0]
    print("\n  ai_usage_logs row:")
    print(f"    evaluation_id     : {row['evaluation_id']}")
    print(f"    model_used        : {row['model_used']}")
    print(f"    total_tokens      : {row['total_tokens']}")
    print(f"    estimated_cost_usd: ${row['estimated_cost_usd']}")
    print(f"    logged_at         : {row['logged_at']}")
    print("  ✅ ai_usage_logs confirmed in DB")
else:
    print("  ❌ Could not read back from ai_usage_logs")


# ── Summary ────────────────────────────────────────────────────────────────

_header("ALL STEPS COMPLETE ✅")
print("""
  Step 1 — Supabase connected
  Step 2 — Real Gemini call succeeded
  Step 3 — Validation passed
  Step 4 — property_ai_summary written
  Step 5 — ai_usage_logs written
  Step 6 — Both rows confirmed in DB
""")