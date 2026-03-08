import requests
import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

APP_ID = os.getenv("SCHOOLDIGGER_APP_ID")
APP_KEY = os.getenv("SCHOOLDIGGER_APP_KEY")


def fetch_district_ratings():

    districts = supabase.table("property_school_district") \
        .select("district_id,state") \
        .execute().data

    for d in districts:

        url = f"https://api.schooldigger.com/v2.3/rankings/districts/{d['state']}"

        params = {
            "appID": APP_ID,
            "appKey": APP_KEY
        }

        r = requests.get(url, params=params)

        if r.status_code != 200:
            print("API error:", r.status_code)
            continue

        data = r.json()

        for dist in data.get("districtList", []):

            if str(dist["districtID"]) != str(d["district_id"]):
                continue

            history = dist.get("rankHistory")

            if not history:
                continue

            latest = history[-1]

            supabase.table("school_district_ratings") \
                .upsert({
                    "district_id": dist["districtID"],
                    "rank": latest["rank"],
                    "rating": latest["rankStars"]
                }, on_conflict="district_id") \
                .execute()

            print("Inserted district:", dist["districtName"])


if __name__ == "__main__":
    fetch_district_ratings()