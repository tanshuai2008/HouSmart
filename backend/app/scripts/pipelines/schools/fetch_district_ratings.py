
import requests
from supabase import create_client, Client
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# ===============================
# CONFIG & CREDENTIALS
# ===============================

SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parents[2]
load_dotenv(BACKEND_DIR / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

SCHOOLDIGGER_APP_ID = os.getenv("SCHOOLDIGGER_APP_ID")
SCHOOLDIGGER_APP_KEY = os.getenv("SCHOOLDIGGER_APP_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Complete FIPS to State Abbreviation Map
FIPS_TO_STATE = { 
    1: 'AL', 2: 'AK', 4: 'AZ', 5: 'AR', 6: 'CA',
    8: 'CO', 9: 'CT', 10: 'DE', 11: 'DC', 12: 'FL',
    13: 'GA', 15: 'HI', 16: 'ID', 17: 'IL', 18: 'IN',
    19: 'IA', 20: 'KS', 21: 'KY', 22: 'LA', 23: 'ME',
    24: 'MD', 25: 'MA', 26: 'MI', 27: 'MN', 28: 'MS',
    29: 'MO', 30: 'MT', 31: 'NE', 32: 'NV', 33: 'NH',
    34: 'NJ', 35: 'NM', 36: 'NY', 37: 'NC', 38: 'ND',
    39: 'OH', 40: 'OK', 41: 'OR', 42: 'PA', 44: 'RI',
    45: 'SC', 46: 'SD', 47: 'TN', 48: 'TX', 49: 'UT',
    50: 'VT', 51: 'VA', 53: 'WA', 54: 'WV', 55: 'WI',
    56: 'WY'
}


# ===============================
# 1. GET TARGET DISTRICTS (UNIQUE ONLY)
# ===============================
print("Fetching target districts from Supabase...")
response = supabase.table("property_school_district").select("district_id, state").execute()

# Group the distinct district IDs by state
states_to_query = {}

for row in response.data:
    fips = int(row['state'])
    
    # FIX: Keep it as an exact string so we don't lose leading zeros!
    dist_id = str(row['district_id']) 
    
    if fips in FIPS_TO_STATE:
        state_abbr = FIPS_TO_STATE[fips]
        
        if state_abbr not in states_to_query:
            states_to_query[state_abbr] = set()
            
        states_to_query[state_abbr].add(dist_id)
    else:
        print(f"⚠️ Missing FIPS mapping for state code: {fips}")

print(f"Unique districts to fetch by state: {states_to_query}")

# ===============================
# 2. FETCH & UPSERT RATINGS
# ===============================
for state, needed_ids in states_to_query.items():
    print(f"\nSearching for {len(needed_ids)} unique district(s) in {state}...")
    
    page = 1
    total_pages = 1 
    districts_found = 0
    
    while page <= total_pages:
        url = f"https://api.schooldigger.com/v2.3/rankings/districts/{state}"
        params = {
            "appID": SCHOOLDIGGER_APP_ID,
            "appKey": SCHOOLDIGGER_APP_KEY,
            "page": page,
            "perPage": 50
        }
        
        api_response = requests.get(url, params=params)
        
        if api_response.status_code == 200:
            data = api_response.json()
            total_pages = data.get("numberOfPages", 1)
            
            for dist in data.get("districtList", []):
                
                #  FIX: Keep the API ID as an exact string too!
                api_dist_id = str(dist["districtID"])
                
                if api_dist_id in needed_ids:
                    rank_history = dist.get("rankHistory", [])
                    
                    if rank_history:
                        latest_rank = max(rank_history, key=lambda x: x.get("year", 0))
                        
                        insert_data = {
                            "district_id": api_dist_id, # Preserves leading zeros perfectly
                            "schooldigger_district_id": api_dist_id, 
                            "state": state,
                            "year": latest_rank.get("year"),
                            "rank": latest_rank.get("rank"),
                            "rank_of": latest_rank.get("rankOf"),
                            "rating": latest_rank.get("rankStars"),
                            "average_standard_score": latest_rank.get("rankScore"),
                            "source": "SchoolDigger"
                        }
                        
                        supabase.table("school_district_ratings") \
                            .upsert(insert_data, on_conflict="district_id") \
                            .execute()
                        
                        print(f" Upserted {dist.get('districtName')} → {latest_rank.get('rankStars')} stars")
                    else:
                        print(f" ⚠️ No ranking history found for {dist.get('districtName')}")
                        
                    districts_found += 1
            
            if districts_found >= len(needed_ids):
                print(f"Found all needed districts in {state}. Moving on.")
                break
                
        else:
            print(f"API Error for {state}: {api_response.status_code} - {api_response.text}")
            break
            
        page += 1
        time.sleep(0.5)

    if districts_found < len(needed_ids):
        missing = len(needed_ids) - districts_found
        print(f"⚠️ Could not find {missing} needed district(s) in {state} on SchoolDigger.")

print("\n All target school district ratings processed!")
