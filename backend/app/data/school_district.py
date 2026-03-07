import requests
from supabase import create_client, Client
import time
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL         = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SCHOOLDIGGER_APP_ID  = os.getenv("SCHOOLDIGGER_APP_ID")
SCHOOLDIGGER_APP_KEY = os.getenv("SCHOOLDIGGER_APP_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ===============================
# SAFETY CONFIG
# ===============================
MAX_API_CALLS = 18      # hard stop — leaves 2 buffer from 20/day limit
FETCH_TOP_N   = 5       # only top 5 ranked schools per district (1 page, 1 call)
SLEEP_SECONDS = 61      # 1 call/minute rate limit on Developer plan

FIPS_TO_STATE = {
    1:'AL',2:'AK',4:'AZ',5:'AR',6:'CA',8:'CO',9:'CT',10:'DE',11:'DC',
    12:'FL',13:'GA',15:'HI',16:'ID',17:'IL',18:'IN',19:'IA',20:'KS',
    21:'KY',22:'LA',23:'ME',24:'MD',25:'MA',26:'MI',27:'MN',28:'MS',
    29:'MO',30:'MT',31:'NE',32:'NV',33:'NH',34:'NJ',35:'NM',36:'NY',
    37:'NC',38:'ND',39:'OH',40:'OK',41:'OR',42:'PA',44:'RI',45:'SC',
    46:'SD',47:'TN',48:'TX',49:'UT',50:'VT',51:'VA',53:'WA',54:'WV',
    55:'WI',56:'WY'
}


# ===============================
# STEP 1: Get distinct districts
# ===============================
print("Fetching target districts from Supabase...")
resp = supabase.table("property_school_district") \
    .select("district_id, state") \
    .execute()

districts = []
for row in resp.data:
    if not row.get("district_id") or not row.get("state"):
        continue
    try:
        fips = int(row["state"])
    except ValueError:
        continue
    state_abbr = FIPS_TO_STATE.get(fips)
    if not state_abbr:
        print(f"  ⚠️  No FIPS mapping for: {fips}")
        continue
    districts.append({
        "district_id": str(row["district_id"]),
        "state": state_abbr
    })

# Deduplicate
seen = set()
unique_districts = []
for d in districts:
    key = (d["district_id"], d["state"])
    if key not in seen:
        seen.add(key)
        unique_districts.append(d)

print(f"Unique districts : {len(unique_districts)}")
print(f"API calls needed : {len(unique_districts)} / {MAX_API_CALLS} limit")
print(f"Est. run time    : ~{len(unique_districts)} minutes (1 call/min)\n")

if len(unique_districts) > MAX_API_CALLS:
    print(f"⚠️  {len(unique_districts)} districts exceeds {MAX_API_CALLS} call limit.")
    print(f"   Will process first {MAX_API_CALLS} districts today.")
    print(f"   Re-run tomorrow for remaining {len(unique_districts) - MAX_API_CALLS}.\n")
    unique_districts = unique_districts[:MAX_API_CALLS]

# ===============================
# STEP 2: Fetch top 5 schools per district
# 1 call per district — stays within 20/day limit
# ===============================
total_inserted = 0
total_no_rank  = 0
api_calls_used = 0

for d in unique_districts:
    dist_id = d["district_id"]
    state   = d["state"]

    # Hard stop before limit
    if api_calls_used >= MAX_API_CALLS:
        print(f"\n Hit {MAX_API_CALLS} call limit. Stopping safely.")
        print(f"   Re-run tomorrow for remaining districts.")
        break

    print(f"\n── District {dist_id} ({state}) ── [call {api_calls_used + 1}/{MAX_API_CALLS}]")

    params = {
        "appID":      SCHOOLDIGGER_APP_ID,
        "appKey":     SCHOOLDIGGER_APP_KEY,
        "districtID": dist_id,
        "sortBy":     "rank",       # ranked schools come first
        "page":       1,            # only page 1
        "perPage":    FETCH_TOP_N,  # top 5 only = 1 call max per district
    }

    resp = requests.get(
        f"https://api.schooldigger.com/v2.3/rankings/schools/{state}",
        params=params
    )
    api_calls_used += 1

    if resp.status_code != 200:
        print(f"   API error {resp.status_code}: {resp.text}")
        # Stop immediately if 429 (rate limit) — don't waste remaining calls
        if resp.status_code == 429:
            print("   Rate limit hit. Stop and try again tomorrow.")
            break
        continue

    data = resp.json()

    # Detect obfuscated data — school names as pure numbers = fake data
    school_list  = data.get("schoolList", [])
    if school_list:
        sample_name = school_list[0].get("schoolName", "")
        if sample_name and sample_name.replace(" ", "").startswith("School #"):
            print(f"    Obfuscated data detected — daily limit likely hit.")
            print(f"   Stopping to protect data quality.")
            api_calls_used -= 1  # don't count this bad call
            break

    school_batch = []
    for school in school_list:
        rank_history = school.get("rankHistory", [])
        has_ranking  = bool(rank_history)

        if has_ranking:
            latest = max(rank_history, key=lambda x: x.get("year", 0))
            rank   = latest.get("rank")
            rank_of = latest.get("rankOf")
            score  = latest.get("rankScore")
            rating = latest.get("rankStars")
            year   = latest.get("year")
        else:
            rank = rank_of = score = rating = year = None

        school_batch.append({
            "district_id":            dist_id,
            "schooldigger_school_id": school.get("schoolid"),
            "school_name":            school.get("schoolName"),
            "state":                  state,
            "school_type":            school.get("schoolLevelLabel"),
            "rank":                   rank,
            "rank_of":                rank_of,
            "average_standard_score": score,
            "rating":                 rating,
            "year":                   year,
            "has_ranking":            has_ranking,
        })

    if not school_batch:
        print(f"  ⚠️  No schools returned")
        # Still sleep to respect rate limit
        if api_calls_used < len(unique_districts):
            print(f"  ⏳ Waiting {SLEEP_SECONDS}s before next call...")
            time.sleep(SLEEP_SECONDS)
        continue

    # Upsert to Supabase
    try:
        supabase.table("school_rankings") \
            .upsert(school_batch, on_conflict="schooldigger_school_id") \
            .execute()

        ranked   = sum(1 for s in school_batch if s["has_ranking"])
        unranked = len(school_batch) - ranked
        total_inserted += len(school_batch)
        total_no_rank  += unranked

        print(f"   {len(school_batch)} schools upserted ({ranked} ranked, {unranked} unranked)")
        for s in school_batch:
            if s["has_ranking"]:
                print(f"     #{s['rank']}/{s['rank_of']} {s['school_name']} ({s['school_type']}) {s['rating']}★")

    except Exception as e:
        print(f"   Upsert failed: {e}")

    # Respect 1 call/minute rate limit — sleep between every call
    if api_calls_used < min(len(unique_districts), MAX_API_CALLS):
        print(f"  ⏳ Waiting {SLEEP_SECONDS}s before next call...")
        time.sleep(SLEEP_SECONDS)

# ===============================
# STEP 3: Summary
# ===============================
print(f"\n🎉 Done.")
print(f"   Schools inserted : {total_inserted}")
print(f"   Without ranking  : {total_no_rank}")
print(f"   API calls used   : {api_calls_used} / {MAX_API_CALLS}")

remaining = len(unique_districts) - api_calls_used
if remaining > 0:
    print(f"   Districts remaining for tomorrow: {remaining}")

# ===============================
# STEP 4: Coverage check
# ===============================
print("\n── Coverage check ──")
check = supabase.table("school_rankings") \
    .select("district_id, school_name, rank, rating, school_type") \
    .order("district_id") \
    .order("rank") \
    .execute()

from collections import defaultdict
by_district = defaultdict(list)
for row in check.data:
    by_district[row["district_id"]].append(row)

for dist_id, schools in by_district.items():
    ranked = [s for s in schools if s["rank"] is not None]
    print(f"\n  {dist_id}: {len(schools)} schools, {len(ranked)} ranked")
    for s in ranked:
        print(f"    #{s['rank']} {s['school_name']} ({s['school_type']}) {s['rating']}★")