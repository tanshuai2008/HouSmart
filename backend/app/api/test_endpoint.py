"""
test_endpoint.py
----------------
DEV ONLY — test endpoints for the AI pipeline.
DO NOT expose in production.

Endpoints:
    POST /dev/test-mock              → full pipeline with mocked LLM (no API key needed)
    POST /dev/test-real              → full pipeline with real Gemini, uses Houston TX by default
    POST /dev/test-real/{property_id} → full pipeline with real Gemini, pick any property from DB
    GET  /dev/properties             → list available properties to test with
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.core.db import get_db
from app.intelligence.engine import run_intelligence

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dev", tags=["DEV — AI Pipeline Tests"])

# ── Default test property (Houston TX) ────────────────────────────────────
_DEFAULT_PROP_ID = "f832e250-a431-49a0-940a-744f0d14de38"
_DEFAULT_TRACT   = "48201980700"

# ── Mock data ──────────────────────────────────────────────────────────────
_MOCK_EVALUATION_DATA = {
    "evaluation_id": "test-mock-001",
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
_MOCK_PRIORITY_RANKING = [
    {"factor": "roi", "rank": 1},
    {"factor": "safety", "rank": 2},
    {"factor": "schools", "rank": 3},
]
_MOCK_AI_RESPONSE = {
    "community_profile": "This zip code has a median income of $68,000 and a median home value of $410,000, indicating a stable middle-income neighborhood. The vacancy rate of 4.10% suggests healthy rental demand.",
    "safety_and_amenities": "The crime score of 62/100 is moderate. Flood risk is very low at 90/100. Transit access is solid at 75/100 with good amenity density at 80/100. Noise score of 70/100 indicates acceptable road noise levels.",
    "investment_suitability": "With a cap rate of 5.20% and a 5-year ROI of 18.00%, this property aligns with your top priority of ROI. Monthly cash flow of $320 is positive but narrow. School data is unavailable and requires manual verification.",
    "verdict_explanation": "This property receives a YELLOW verdict because it meets your ROI target but the crime score of 62 may not fully satisfy your safety priority. School data is unavailable — verify manually.",
    "key_strengths": ["Cap rate of 5.20% meets investor threshold", "Very low flood risk score of 90/100", "Positive monthly cash flow of $320"],
    "key_risks": ["Crime score of 62 may fall short of safety expectations", "School score data unavailable — manual verification required"],
    "missing_data_note": "School score data was unavailable. Please verify school quality manually.",
    "_meta": {"model": "gemini-2.5-flash", "input_tokens": 850, "output_tokens": 320, "policy_injected": False},
}


# ── GET /dev/properties ────────────────────────────────────────────────────
@router.get(
    "/properties",
    summary="[DEV] List all available properties to test with",
)
def list_properties(db: Client = Depends(get_db)):
    """Returns all properties in the DB with their IDs and addresses."""
    try:
        r = db.table("properties").select(
            "id, formatted_address, state, zip_code, city, latitude, longitude, tract_fips"
        ).execute()
        return {
            "count": len(r.data),
            "properties": r.data,
            "hint": "Use any 'id' value in POST /dev/test-real/{property_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── POST /dev/test-mock ────────────────────────────────────────────────────
@router.post(
    "/test-mock",
    summary="[DEV] Full pipeline with mocked LLM — no API key or DB needed",
)
def test_mock():
    """Runs the full AI pipeline with a mocked Gemini call. Safe for any environment."""
    import app.intelligence.engine as engine_module
    original = engine_module.run_recommendation

    def _mock_llm(payload, policy_summary=None):
        return dict(_MOCK_AI_RESPONSE)

    try:
        engine_module.run_recommendation = _mock_llm
        result = run_intelligence(
            evaluation_id="test-mock-001",
            evaluation_data=_MOCK_EVALUATION_DATA,
            priority_ranking=_MOCK_PRIORITY_RANKING,
            db_session=None,
        )
    finally:
        engine_module.run_recommendation = original

    return result


# ── POST /dev/test-real (default Houston TX) ──────────────────────────────
@router.post(
    "/test-real",
    summary="[DEV] Real Gemini + real Supabase data — default Houston TX property",
)
def test_real_default(db: Client = Depends(get_db)):
    """Uses the default Houston TX property. Requires GEMINI_API_KEY in .env"""
    return _run_real_test(db, _DEFAULT_PROP_ID)


# ── POST /dev/test-real/{property_id} ─────────────────────────────────────
@router.post(
    "/test-real/{property_id}",
    summary="[DEV] Real Gemini + real Supabase data — choose any property by ID",
)
def test_real_by_property(property_id: str, db: Client = Depends(get_db)):
    """
    Pick any property from GET /dev/properties and pass its ID here.
    Requires GEMINI_API_KEY in .env
    """
    return _run_real_test(db, property_id)


# ── Shared logic ───────────────────────────────────────────────────────────
def _run_real_test(db: Client, property_id: str) -> dict:
    # Load property from DB
    try:
        prop_resp = db.table("properties").select(
            "id, formatted_address, state, zip_code, city, latitude, longitude, tract_fips"
        ).eq("id", property_id).maybe_single().execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DB error: {e}")

    if not prop_resp.data:
        raise HTTPException(
            status_code=404,
            detail=f"Property '{property_id}' not found. Use GET /dev/properties to see available IDs."
        )

    prop  = prop_resp.data
    state = prop.get("state", "TX")
    city  = prop.get("city", "")
    tract = prop.get("tract_fips") or _DEFAULT_TRACT

    # Fetch all variables
    transit_score     = _fetch_transit(db)
    flood_score       = _fetch_flood(db)
    noise_score       = _fetch_noise(db)
    amenity_score     = _fetch_amenity(db)
    estimated_rent    = _fetch_rent(db)
    school_score      = _fetch_school(db, state)
    median_home_value = _fetch_median_home(db, state)
    median_income, education_pct = _fetch_census(db, tract)
    priority_ranking  = _fetch_priorities(db)

    evaluation_data = {
        "evaluation_id": property_id,
        "verdict_color": "yellow",
        "property": {
            "formatted_address": prop.get("formatted_address"),
            "state":             state,
            "zip_code":          prop.get("zip_code"),
            "bedrooms":          prop.get("bedrooms", 3),
            "bathrooms":         prop.get("bathrooms", 2.0),
            "square_feet":       prop.get("square_feet", 1400),
            "year_built":        prop.get("year_built", 2010),
            "property_type":     prop.get("property_type", "single_family"),
        },
        "financials": {
            "monthly_cash_flow": 400,
            "cap_rate":          0.055,
            "roi_5yr":           0.20,
            "estimated_value":   380000,
        },
        "variables": {
            "estimated_rent":    {"status": "ready" if estimated_rent    else "failed", "value": estimated_rent,    "source": "RentCast"},
            "crime_score":       {"status": "failed"},
            "school_score":      {"status": "ready" if school_score      else "failed", "value": school_score,      "source": "SchoolDigger"},
            "transit_score":     {"status": "ready" if transit_score     else "failed", "value": transit_score,     "source": "OSM"},
            "flood_risk_score":  {"status": "ready" if flood_score       else "failed", "value": flood_score,       "source": "FEMA"},
            "amenity_score":     {"status": "ready" if amenity_score     else "failed", "value": amenity_score,     "source": "OSM"},
            "noise_score":       {"status": "ready" if noise_score       else "failed", "value": noise_score,       "source": "OSM"},
            "median_income":     {"status": "ready" if median_income     else "failed", "value": median_income,     "source": "ACS"},
            "median_home_value": {"status": "ready" if median_home_value else "failed", "value": median_home_value, "source": "Redfin"},
            "vacancy_rate":      {"status": "failed"},
        },
    }

    return run_intelligence(
        evaluation_id=property_id,
        evaluation_data=evaluation_data,
        priority_ranking=priority_ranking,
        db_session=db,
    )


# ── Fetch helpers ──────────────────────────────────────────────────────────
def _fetch_transit(db):
    try:
        r = db.table('transit_scores').select('transit_score').order('created_at', desc=True).limit(1).execute()
        return r.data[0]['transit_score'] if r.data else None
    except: return None

def _fetch_flood(db):
    try:
        r = db.table('flood_zones').select('flood_score').order('created_at', desc=True).limit(1).execute()
        return r.data[0]['flood_score'] if r.data else None
    except: return None

def _fetch_noise(db):
    try:
        r = db.table('noise_scores').select('noise_level').order('created_at', desc=True).limit(1).execute()
        if r.data:
            label = r.data[0]['noise_level']
            return {'Very Low': 90, 'Low': 75, 'Moderate': 60, 'High': 40, 'Very High': 20}.get(label, 50)
        return None
    except: return None

def _fetch_amenity(db):
    try:
        r = db.table('osm_poi_cache').select('id').limit(100).execute()
        return min(100, len(r.data)) if r.data else None
    except: return None

def _fetch_rent(db):
    try:
        r = db.table('rent_estimate_cache').select('response_payload').order('created_at', desc=True).limit(1).execute()
        if r.data:
            p = r.data[0]['response_payload']
            return p.get('rent') or p.get('price') or p.get('rentRangeLow') or p.get('rentEstimate')
        return None
    except: return None

def _fetch_school(db, state):
    try:
        r = db.table('school_rankings').select('rating, rank, rank_of').eq('state', state).limit(1).execute()
        if r.data:
            row = r.data[0]
            if row.get('rank') and row.get('rank_of') and row['rank_of'] > 0:
                return round((1 - row['rank'] / row['rank_of']) * 100)
            elif row.get('rating'):
                return round(float(row['rating']) * 10)
        return None
    except: return None

def _fetch_median_home(db, state):
    try:
        r = db.table('redfin_median_prices').select('median_price').eq('state', state).order('period', desc=True).limit(1).execute()
        return r.data[0]['median_price'] if r.data else None
    except: return None

def _fetch_census(db, tract):
    try:
        r = db.table('geo_tract_metrics').select('median_income, education_bachelor_pct').eq('tract_geoid', tract).execute()
        if r.data:
            return r.data[0].get('median_income'), r.data[0].get('education_bachelor_pct')
        return None, None
    except: return None, None

def _fetch_priorities(db):
    try:
        r = db.table('user_onboarding_answers').select('priorities_ranking_ques').order('created_on', desc=True).limit(1).execute()
        if r.data:
            raw = r.data[0]['priorities_ranking_ques']
            if isinstance(raw, list):
                return [{'factor': p, 'rank': i+1} for i, p in enumerate(raw)]
        return [{"factor": "roi", "rank": 1}, {"factor": "safety", "rank": 2}, {"factor": "schools", "rank": 3}]
    except:
        return [{"factor": "roi", "rank": 1}, {"factor": "safety", "rank": 2}, {"factor": "schools", "rank": 3}]