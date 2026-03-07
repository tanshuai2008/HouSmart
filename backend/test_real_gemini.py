import os
import sys
from dotenv import load_dotenv
load_dotenv(override=True)  # ← MUST be before any app imports

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.intelligence.builder import build_base_payload
from app.intelligence.recommendation import run_recommendation
# rest of file...

evaluation_data = {
    "evaluation_id": "test-real-001",
    "verdict_color": "yellow",
    "property": {
        "formatted_address": "350 5th Ave, New York, NY 10118",
        "state": "TX", "zip_code": "10118",
        "bedrooms": 3, "bathrooms": 2.0,
        "square_feet": 1400, "year_built": 2005,
        "property_type": "single_family",
    },
    "financials": {
        "monthly_cash_flow": 320, "cap_rate": 0.052,
        "roi_5yr": 0.18, "estimated_value": 420000,
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
    {"factor": "roi", "rank": 1},
    {"factor": "safety", "rank": 2},
    {"factor": "schools", "rank": 3},
]

import json
print("Making REAL Gemini API call...\n")
payload = build_base_payload(evaluation_data, priority_ranking)
result = run_recommendation(payload, policy_summary=None)

print("=== REAL GEMINI OUTPUT ===")
print(json.dumps(result, indent=2))
print(f"\n Tokens used — input: {result['_meta']['input_tokens']} output: {result['_meta']['output_tokens']}")
