r"""
Standalone test for the AI recommendation pipeline.

Run from the backend/ folder:
    .\venv\Scripts\python app\ai\test_ai.py

Or using module syntax:
    .\venv\Scripts\python -m app.ai.test_ai
"""
import os, sys, json, logging
from pathlib import Path
from dotenv import load_dotenv

# ── Make the package importable when running this file directly ──────────────
# Adds  …/backend  to sys.path so  "from app.ai.builder import …"  works.
_BACKEND_ROOT = str(Path(__file__).resolve().parents[2])   # …/backend
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

load_dotenv(os.path.join(_BACKEND_ROOT, ".env"))
load_dotenv(os.path.join(_BACKEND_ROOT, "app", "ai", ".env"), override=True)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# Now import using the *package* path — exactly as production does.
from app.ai.builder import build_base_payload
from app.ai.recommendation import run_recommendation
from app.ai.validator import validate_ai_output
from app.ai.engine import _build_final_response

MOCK_EVALUATION_ID = "dc901e03-6507-4898-8ecb-b7d618766e0e"
MOCK_PROPERTY_ID   = "c8d1ee1d-6e96-4b12-8c6a-b0ea204b942a"
MOCK_USER_ID       = "71984a45-c0ba-49b7-87e3-4c0eac9b724d"

MOCK_EVALUATION_DATA = {
    "property": {
        "property_id":       MOCK_PROPERTY_ID,
        "user_id":           MOCK_USER_ID,
        "formatted_address": "6611 Natasha Ct, Countryside, IL 60525",
        "state":             "IL",
        "zip_code":          "60525",
        "bedrooms":          3,
        "bathrooms":         2.5,
        "square_feet":       2088,
        "year_built":        1998,
        "property_type":     "Townhouse",
    },
    "financials": {
        "monthly_cash_flow": 327,
        "cap_rate":          0.0552,
        "roi_5yr":           0.312,
        "estimated_value":   410000,
    },
    "variables": {
        "estimated_rent":    {"status": "ready", "value": 3370,   "source": "RentCast"},
        "crime_score":       {"status": "ready", "value": 49.86,  "source": "NeighborhoodScout"},
        "school_score":      {"status": "ready", "value": 79.4,   "source": "GreatSchools"},
        "transit_score":     {"status": "ready", "value": 58,     "source": "Walkscore"},
        "flood_risk_score":  {"status": "ready", "value": 95,     "source": "FEMA"},
        "amenity_score":     {"status": "ready", "value": 78.5,   "source": "Foursquare"},
        "noise_score":       {"status": "ready", "value": 72.8,   "source": "HowLoud"},
        "median_income":     {"status": "ready", "value": 101838, "source": "Census"},
        "median_home_value": {"status": "ready", "value": 135000, "source": "Census"},
        "vacancy_rate":      {"status": "failed"},
    },
    "verdict_color": "green",
}

MOCK_USER_PROFILE = {
    "primary_role_ques":                "Individual Investor",
    "investment_experience_level_ques": "Newbie (1st Deal)",
    "investment_goal_ques":             "Balanced Mix",
    "priorities_ranking_ques":          "[\"safety\", \"proximity\", \"demographics\", \"schools\"]",
}

MOCK_PRIORITY_RANKING = [
    {"factor": "roi",    "rank": 1},
    {"factor": "safety", "rank": 2},
    {"factor": "school", "rank": 3},
]


def run_test():
    print("\n--- Step 1: Build payload ---")
    payload = build_base_payload(
        evaluation_id=MOCK_EVALUATION_ID,
        evaluation_data=MOCK_EVALUATION_DATA,
        priority_ranking=MOCK_PRIORITY_RANKING,
        user_profile=MOCK_USER_PROFILE,
    )
    print(json.dumps(payload, indent=2))

    print("\n--- Step 2: Run recommendation LLM ---")
    raw_output = run_recommendation(payload=payload, policy_summary=None)
    print(json.dumps({k: v for k, v in raw_output.items() if not k.startswith("_")}, indent=2))

    print("\n--- Step 3: Validate output ---")
    validated = validate_ai_output(
        ai_output=raw_output,
        deterministic_payload=payload,
    )
    print("admin_review_required:", validated.get("admin_review_required"))
    print("validation_errors:    ", validated.get("validation_errors"))
    print("validation_warnings:  ", validated.get("validation_warnings"))

    print("\n--- Step 4: Final response (dashboard shape) ---")
    final = _build_final_response(
        validated_output=validated,
        payload=payload,
        policy_summary=None,
    )
    print(json.dumps(final, indent=2))


if __name__ == "__main__":
    run_test()