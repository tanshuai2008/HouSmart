import json
import sys
import os

# ── Make sure Python finds the app modules ────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Fake API key so the modules load without crashing ─────────────────────
os.environ["GEMINI_API_KEY"] = "fake-key-for-local-testing"

from app.intelligence.builder import build_base_payload
from app.intelligence.validator import validate_ai_output
from app.intelligence.engine import run_intelligence

# ─────────────────────────────────────────────────────────────────────────
# TEST DATA
# ─────────────────────────────────────────────────────────────────────────

evaluation_data = {
    "evaluation_id": "test-001",
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
        "estimated_rent":    {"status": "ready",  "value": 2400,   "source": "RentCast"},
        "crime_score":       {"status": "ready",  "value": 62,     "source": "FBI UCR"},
        "school_score":      {"status": "failed"},   # ← missing data — tests flag logic
        "transit_score":     {"status": "ready",  "value": 75,     "source": "OSM"},
        "flood_risk_score":  {"status": "ready",  "value": 90,     "source": "FEMA"},
        "amenity_score":     {"status": "ready",  "value": 80,     "source": "OSM"},
        "noise_score":       {"status": "ready",  "value": 70,     "source": "OSM"},
        "median_income":     {"status": "ready",  "value": 68000,  "source": "ACS"},
        "median_home_value": {"status": "ready",  "value": 410000, "source": "ACS"},
        "vacancy_rate":      {"status": "ready",  "value": 0.041,  "source": "ACS"},
    },
}

priority_ranking = [
    {"factor": "roi",     "rank": 1},
    {"factor": "safety",  "rank": 2},
    {"factor": "schools", "rank": 3},
]

# ─────────────────────────────────────────────────────────────────────────
# MOCK AI OUTPUT  (simulates what Gemini would return)
# ─────────────────────────────────────────────────────────────────────────

mock_ai_output = {
    "community_profile": (
        "This zip code has a median income of $68,000 and a median home value of $410,000, "
        "indicating a stable middle-income neighborhood with moderate homeownership. "
        "The vacancy rate of 4.10% suggests healthy rental demand."
    ),
    "safety_and_amenities": (
        "The crime score of 62/100 is moderate. Flood risk is low at 90/100. "
        "Transit access is solid at 75/100 with good amenity density at 80/100. "
        "Noise score of 70/100 indicates acceptable road noise levels."
    ),
    "investment_suitability": (
        "With a cap rate of 5.20% and a 5-year ROI of 18.00%, this property aligns with "
        "your top priority of ROI. Monthly cash flow of $320 is positive but narrow. "
        "School data is unavailable and requires manual verification before finalizing."
    ),
    "verdict_explanation": (
        "This property receives a YELLOW verdict because it meets your ROI target but "
        "the crime score of 62 may not fully satisfy your safety priority. "
        "School data is unavailable — verify manually."
    ),
    "key_strengths": [
        "Cap rate of 5.20% meets investor threshold",
        "Low flood risk score of 90/100",
        "Positive monthly cash flow of $320",
        "Low vacancy rate of 4.10% signals rental demand",
    ],
    "key_risks": [
        "Crime score of 62 may fall short of safety expectations",
        "School score data unavailable — manual verification required",
        "Narrow cash flow leaves limited buffer for unexpected expenses",
    ],
    "missing_data_note": (
        "School score data was unavailable for this property. "
        "Please verify school quality manually before making a decision."
    ),
}

# ─────────────────────────────────────────────────────────────────────────
# TEST 1 — Builder
# ─────────────────────────────────────────────────────────────────────────

def _header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


_header("TEST 1 — builder.build_base_payload()")

payload = build_base_payload(evaluation_data, priority_ranking)
print(json.dumps(payload, indent=2))

assert payload["verdict_color"] == "YELLOW"
assert payload["data_completeness_pct"] == 90.0
assert "school_score" in payload["failed_variables"]
assert payload["location_metrics"]["school_score"] is None
assert len(payload["missing_data_flags"]) == 1
print("\n✅ Builder test passed")

# ─────────────────────────────────────────────────────────────────────────
# TEST 2 — Validator (clean output — should PASS)
# ─────────────────────────────────────────────────────────────────────────

_header("TEST 2 — validator.validate_ai_output() — CLEAN (should pass)")

result_clean = validate_ai_output(dict(mock_ai_output), payload)
print(f"  admin_review_required : {result_clean['admin_review_required']}")
print(f"  validation_errors     : {result_clean['validation_errors']}")
print(f"  validation_warnings   : {result_clean['validation_warnings']}")
assert result_clean["admin_review_required"] == False, f"Expected pass, got errors: {result_clean['validation_errors']}"
print("\n✅ Validator clean-output test passed")

# ─────────────────────────────────────────────────────────────────────────
# TEST 3 — Validator (dirty output — should FAIL)
# ─────────────────────────────────────────────────────────────────────────

_header("TEST 3 — validator.validate_ai_output() — DIRTY (should flag errors)")

dirty_output = dict(mock_ai_output)
dirty_output["verdict_explanation"] = (
    "This is a great deal and a strong investment. I recommend buying immediately. "
    "Guaranteed returns of 45% are expected."   # hallucinated %, forbidden word
)
dirty_output["safety_and_amenities"] = (
    "The school score is excellent."   # school_score is null — no disclaimer!
)

result_dirty = validate_ai_output(dirty_output, payload)
print(f"  admin_review_required : {result_dirty['admin_review_required']}")
print(f"  validation_errors     : {json.dumps(result_dirty['validation_errors'], indent=4)}")
print(f"  validation_warnings   : {json.dumps(result_dirty['validation_warnings'], indent=4)}")
assert result_dirty["admin_review_required"] == True, "Expected dirty output to be flagged"
assert len(result_dirty["validation_errors"]) > 0
print("\n✅ Validator dirty-output test passed")

# ─────────────────────────────────────────────────────────────────────────
# TEST 4 — Full engine with mocked LLM call
# ─────────────────────────────────────────────────────────────────────────

_header("TEST 4 — engine.run_intelligence() — mocked LLM")

# Patch at the ENGINE level — that's where the name is actually called from
import app.intelligence.engine as engine_module
original_run = engine_module.run_recommendation

def mock_run_recommendation(payload, policy_summary=None):
    print("  [MOCK] Gemini call intercepted — returning mock output")
    output = dict(mock_ai_output)
    output["_meta"] = {
        "model": "gemini-2.0-flash",
        "input_tokens": 850,
        "output_tokens": 320,
        "policy_injected": policy_summary is not None,
    }
    return output

engine_module.run_recommendation = mock_run_recommendation

engine_result = run_intelligence(
    evaluation_id="test-001",
    evaluation_data=evaluation_data,
    priority_ranking=priority_ranking,
    db_session=None,   # no DB needed
)

# Restore original
engine_module.run_recommendation = original_run

print("\n=== ENGINE OUTPUT ===")
print(json.dumps(engine_result, indent=2))

assert engine_result["status"] == "complete"
assert engine_result["verdict_color"] == "YELLOW"
assert engine_result["admin_review_required"] == False
assert engine_result["community_profile"] is not None
assert engine_result["policy_highlights"] is None   # TX but no RAG chunks in dev
print("\n✅ Full engine test passed")

# ─────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────

_header("ALL TESTS PASSED ✅")
print("""
  Test 1 — Builder:          payload built correctly, failed vars flagged
  Test 2 — Validator clean:  valid AI output passes all 4 rulesets
  Test 3 — Validator dirty:  hallucinated % + forbidden words + missing disclaimer caught
  Test 4 — Full engine:      orchestrator runs builder→policy→rec→validator→logger
""")