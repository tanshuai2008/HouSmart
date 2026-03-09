import os, sys, json
from dotenv import load_dotenv
load_dotenv(override=True)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.supabase_client import supabase
from app.intelligence.builder import build_base_payload
from app.intelligence.recommendation import run_recommendation

# ── Houston TX property ────────────────────────────────────────────────────
PROP_ID  = 'f832e250-a431-49a0-940a-744f0d14de38'
LAT      = 29.756940918955
LNG      = -95.365007245443
TRACT    = '48201980700'
STATE    = 'TX'
CITY     = 'HOUSTON'
ADDRESS  = '1000 MAIN ST, HOUSTON, TX, 77002'

print("🔍 Fetching real data from Supabase...\n")

# 1 — Transit score
transit_score = None
try:
    r = supabase.table('transit_scores').select('transit_score').order('created_at', desc=True).limit(1).execute()
    if r.data: transit_score = r.data[0]['transit_score']
    print(f"✅ transit_score: {transit_score}")
except Exception as e: print(f"❌ transit: {e}")

# 2 — Flood score
flood_score = None
try:
    r = supabase.table('flood_zones').select('flood_score, risk_label').order('created_at', desc=True).limit(1).execute()
    if r.data: flood_score = r.data[0]['flood_score']
    print(f"✅ flood_score: {flood_score}")
except Exception as e: print(f"❌ flood: {e}")

# 3 — Noise score (convert label to 0-100, higher = quieter)
noise_score = None
try:
    r = supabase.table('noise_scores').select('noise_level, distance_to_road').order('created_at', desc=True).limit(1).execute()
    if r.data:
        label = r.data[0]['noise_level']
        noise_map = {'Very Low': 90, 'Low': 75, 'Moderate': 60, 'High': 40, 'Very High': 20}
        noise_score = noise_map.get(label, 50)
    print(f"✅ noise_score: {noise_score} (from label: '{label}')")
except Exception as e: print(f"❌ noise: {e}")

# 4 — Amenity score (POI count capped at 100)
amenity_score = None
try:
    r = supabase.table('osm_poi_cache').select('id').limit(100).execute()
    amenity_score = min(100, len(r.data))
    print(f"✅ amenity_score: {amenity_score}")
except Exception as e: print(f"❌ amenity: {e}")

# 5 — Rent estimate
estimated_rent = None
try:
    r = supabase.table('rent_estimate_cache').select('response_payload').order('created_at', desc=True).limit(1).execute()
    if r.data:
        payload = r.data[0]['response_payload']
        estimated_rent = (
            payload.get('rent') or
            payload.get('price') or
            payload.get('rentRangeLow') or
            payload.get('rentEstimate')
        )
    print(f"✅ estimated_rent: {estimated_rent}")
except Exception as e: print(f"❌ rent: {e}")

# 6 — School score from school_rankings
school_score = None
try:
    r = supabase.table('school_rankings').select('rating, rank, rank_of').eq('state', STATE).limit(1).execute()
    if r.data:
        row = r.data[0]
        if row.get('rank') and row.get('rank_of') and row['rank_of'] > 0:
            school_score = round((1 - row['rank'] / row['rank_of']) * 100)
        elif row.get('rating'):
            school_score = round(float(row['rating']) * 10)
    print(f"✅ school_score: {school_score}")
except Exception as e: print(f"❌ school: {e}")

# 7 — Median home price from redfin
median_home_value = None
try:
    r = supabase.table('redfin_median_prices').select('median_price').eq('state', STATE).order('period', desc=True).limit(1).execute()
    if r.data: median_home_value = r.data[0]['median_price']
    print(f"✅ median_home_value: {median_home_value}")
except Exception as e: print(f"❌ median home: {e}")

# 8 — Census: median income + education from geo_tract_metrics
median_income = None
education_pct = None
try:
    r = supabase.table('geo_tract_metrics').select('median_income, education_bachelor_pct').eq('tract_geoid', TRACT).execute()
    if r.data:
        median_income = r.data[0].get('median_income')
        education_pct = r.data[0].get('education_bachelor_pct')
    print(f"✅ median_income: {median_income}, education_pct: {education_pct}")
except Exception as e: print(f"❌ census: {e}")

# 9 — User priorities from onboarding
priority_ranking = []
try:
    r = supabase.table('user_onboarding_answers').select('priorities_ranking_ques').order('created_on', desc=True).limit(1).execute()
    if r.data:
        raw = r.data[0]['priorities_ranking_ques']
        if isinstance(raw, list):
            priority_ranking = [{'factor': p, 'rank': i+1} for i, p in enumerate(raw)]
        elif isinstance(raw, dict):
            priority_ranking = [{'factor': k, 'rank': v} for k, v in raw.items()]
    print(f"✅ priority_ranking: {priority_ranking}")
except Exception as e: print(f"❌ priorities: {e}")

# ── Fallback priorities if none found ─────────────────────────────────────
if not priority_ranking:
    priority_ranking = [
        {"factor": "roi",     "rank": 1},
        {"factor": "safety",  "rank": 2},
        {"factor": "schools", "rank": 3},
    ]
    print("⚠️  Using default priority ranking")

# ── Build evaluation_data ──────────────────────────────────────────────────
evaluation_data = {
    "evaluation_id": PROP_ID,
    "verdict_color": "yellow",
    "property": {
        "formatted_address": ADDRESS,
        "state": STATE,
        "zip_code": "77002",
        "bedrooms": 3,
        "bathrooms": 2.0,
        "square_feet": 1400,
        "year_built": 2010,
        "property_type": "single_family",
    },
    "financials": {
        "monthly_cash_flow": 400,
        "cap_rate": 0.055,
        "roi_5yr": 0.20,
        "estimated_value": 380000,
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

# ── Run pipeline ───────────────────────────────────────────────────────────
print("\n🔥 Making REAL Gemini API call with real Supabase data...\n")
payload = build_base_payload(evaluation_data, priority_ranking)
result  = run_recommendation(payload, policy_summary=None)

print("=== REAL OUTPUT ===")
print(json.dumps({k: v for k, v in result.items() if k != '_meta'}, indent=2))
print(f"\n✅ Tokens — input: {result['_meta']['input_tokens']} output: {result['_meta']['output_tokens']}")
print(f"✅ Model: {result['_meta']['model']}")