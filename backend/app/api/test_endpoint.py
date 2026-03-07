from fastapi import APIRouter
from app.intelligence.engine import run_intelligence

router = APIRouter(prefix="/dev", tags=["AI Evaluation — DEV TEST"])

MOCK_EVALUATION_DATA = {
    "evaluation_id": "test-mock-001",
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
        "school_score":      {"status": "failed"},
        "transit_score":     {"status": "ready",  "value": 75,     "source": "OSM"},
        "flood_risk_score":  {"status": "ready",  "value": 90,     "source": "FEMA"},
        "amenity_score":     {"status": "ready",  "value": 80,     "source": "OSM"},
        "noise_score":       {"status": "ready",  "value": 70,     "source": "OSM"},
        "median_income":     {"status": "ready",  "value": 68000,  "source": "ACS"},
        "median_home_value": {"status": "ready",  "value": 410000, "source": "ACS"},
        "vacancy_rate":      {"status": "ready",  "value": 0.041,  "source": "ACS"},
    },
}

MOCK_PRIORITY_RANKING = [
    {"factor": "roi",     "rank": 1},
    {"factor": "safety",  "rank": 2},
    {"factor": "schools", "rank": 3},
]

MOCK_AI_RESPONSE = {
    "community_profile": "This zip code has a median income of $68,000 and a median home value of $410,000, indicating a stable middle-income neighborhood. The vacancy rate of 4.10% suggests healthy rental demand.",
    "safety_and_amenities": "The crime score of 62/100 is moderate. Flood risk is low at 90/100. Transit access is solid at 75/100 with good amenity density at 80/100. Noise score of 70/100 indicates acceptable road noise levels.",
    "investment_suitability": "With a cap rate of 5.20% and a 5-year ROI of 18.00%, this property aligns with your top priority of ROI. Monthly cash flow of $320 is positive but narrow. School data is unavailable and requires manual verification.",
    "verdict_explanation": "This property receives a YELLOW verdict because it meets your ROI target but the crime score of 62 may not fully satisfy your safety priority. School data is unavailable — verify manually.",
    "key_strengths": ["Cap rate of 5.20% meets investor threshold", "Low flood risk score of 90/100", "Positive monthly cash flow of $320"],
    "key_risks": ["Crime score of 62 may fall short of safety expectations", "School score data unavailable — manual verification required"],
    "missing_data_note": "School score data was unavailable. Please verify manually.",
    "_meta": {"model": "gemini-2.0-flash", "input_tokens": 850, "output_tokens": 320, "policy_injected": False},
}


@router.post("/test-mock", summary="[DEV ONLY] Test AI pipeline — no DB or API key needed")
def test_mock_endpoint():
    import app.intelligence.engine as engine_module
    original = engine_module.run_recommendation

    def _mock_llm(payload, policy_summary=None):
        return dict(MOCK_AI_RESPONSE)

    try:
        engine_module.run_recommendation = _mock_llm
        result = run_intelligence(
            evaluation_id="test-mock-001",
            evaluation_data=MOCK_EVALUATION_DATA,
            priority_ranking=MOCK_PRIORITY_RANKING,
            db_session=None,
        )
    finally:
        engine_module.run_recommendation = original

    return result
