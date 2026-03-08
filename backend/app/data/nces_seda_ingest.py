import os
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


print("Step 1: Loading NCES Directory")

dir_df = pd.read_csv(
    os.path.join(BASE_DIR, "ccd_sch_029_2223_w_1a_083023-directory.csv"),
    low_memory=False,
    encoding="latin-1"
)

dir_df = dir_df[
    [
        "NCESSCH",
        "SCH_NAME",
        "LEA_NAME",
        "LEAID",
        "ST",
        "MZIP",
        "LEVEL",
        "GSLO",
        "GSHI",
        "CHARTER_TEXT",
        "SCH_TYPE_TEXT",
        "SY_STATUS_TEXT",
    ]
].copy()

dir_df["NCESSCH"] = dir_df["NCESSCH"].astype(str).str.zfill(12)
dir_df["LEAID"] = dir_df["LEAID"].astype(str).str.zfill(7)

dir_df = dir_df[dir_df["SY_STATUS_TEXT"] == "Open"].copy()

print("Directory rows:", len(dir_df))


print("Step 2: Loading Membership")

try:

    mem_df = pd.read_csv(
        os.path.join(BASE_DIR, "ccd_sch_052_2223_l_1a_083023-membership.csv"),
        low_memory=False,
        encoding="latin-1"
    )

    mem_df["NCESSCH"] = mem_df["NCESSCH"].astype(str).str.zfill(12)

    if "MEMBER" in mem_df.columns:

        mem_df["MEMBER"] = pd.to_numeric(mem_df["MEMBER"], errors="coerce")

        enroll = mem_df.groupby("NCESSCH")["MEMBER"].sum().reset_index()
        enroll.columns = ["NCESSCH", "total_enrollment"]

    else:

        print("Membership dataset missing MEMBER column")
        enroll = pd.DataFrame(columns=["NCESSCH", "total_enrollment"])

    print("Enrollment rows:", len(enroll))

except FileNotFoundError:

    print("Membership file not found")
    enroll = pd.DataFrame(columns=["NCESSCH", "total_enrollment"])


print("Step 3: Loading Staff")

staff_df = pd.read_csv(
    os.path.join(BASE_DIR, "ccd_sch_059_2223_l_1a_083023--staff.csv"),
    low_memory=False,
    encoding="latin-1"
)

staff_df["NCESSCH"] = staff_df["NCESSCH"].astype(str).str.zfill(12)
staff_df["TEACHERS"] = pd.to_numeric(staff_df["TEACHERS"], errors="coerce")

staff_clean = staff_df[["NCESSCH", "TEACHERS"]].copy()


print("Step 4: Loading Lunch")

lunch_df = pd.read_csv(
    os.path.join(BASE_DIR, "ccd_sch_033_2223_l_1a_083023-lunch.csv"),
    low_memory=False,
    encoding="latin-1"
)

lunch_df["NCESSCH"] = lunch_df["NCESSCH"].astype(str).str.zfill(12)
lunch_df["STUDENT_COUNT"] = pd.to_numeric(lunch_df["STUDENT_COUNT"], errors="coerce")

free = lunch_df[
    lunch_df["LUNCH_PROGRAM"] == "Free lunch qualified"
].groupby("NCESSCH")["STUDENT_COUNT"].sum().reset_index()

free.columns = ["NCESSCH", "free_lunch_n"]

reduced = lunch_df[
    lunch_df["LUNCH_PROGRAM"] == "Reduced-price lunch qualified"
].groupby("NCESSCH")["STUDENT_COUNT"].sum().reset_index()

reduced.columns = ["NCESSCH", "reduced_lunch_n"]

frpl = free.merge(reduced, on="NCESSCH", how="outer").fillna(0)
frpl["frpl_total"] = frpl["free_lunch_n"] + frpl["reduced_lunch_n"]


print("Step 5: Loading School Characteristics")

char_df = pd.read_csv(
    os.path.join(BASE_DIR, "ccd_sch_129_2223_w_1a_083023-schoolChar.csv"),
    low_memory=False,
    encoding="latin-1"
)

char_df["NCESSCH"] = char_df["NCESSCH"].astype(str).str.zfill(12)

char_clean = char_df[["NCESSCH", "NSLP_STATUS_TEXT", "VIRTUAL_TEXT"]].copy()
char_clean.columns = ["NCESSCH", "nslp_status", "is_virtual"]


print("Step 6: Loading SEDA")

seda = pd.read_csv(
    os.path.join(BASE_DIR, "seda_school_pool_cs_6.0.csv"),
    low_memory=False
)

seda["sedasch"] = seda["sedasch"].astype(str).str.split(".").str[0].str.zfill(12)

seda_clean = seda[
    ["sedasch", "cs_mn_avg_eb", "cs_mn_lrn_eb", "cs_mn_mth_eb"]
].copy()

seda_clean.columns = [
    "NCESSCH",
    "academic_score",
    "growth_score",
    "math_score",
]


print("Step 7: Fetching target districts")

resp = supabase.table("property_school_district").select("district_id").execute()

our_ids = {str(r["district_id"]).zfill(7) for r in resp.data if r.get("district_id")}

if len(our_ids) == 0:

    print("No districts found in database, loading all schools")

    dir_filtered = dir_df.copy()

else:

    dir_filtered = dir_df[dir_df["LEAID"].isin(our_ids)].copy()

print("Filtered schools:", len(dir_filtered))


print("Step 8: Joining datasets")

master = dir_filtered.merge(enroll, on="NCESSCH", how="left")
master = master.merge(staff_clean, on="NCESSCH", how="left")
master = master.merge(frpl, on="NCESSCH", how="left")
master = master.merge(char_clean, on="NCESSCH", how="left")
master = master.merge(seda_clean, on="NCESSCH", how="left")


print("Step 9: Computing metrics")

master["TEACHERS"] = pd.to_numeric(master["TEACHERS"], errors="coerce")
master["total_enrollment"] = pd.to_numeric(master["total_enrollment"], errors="coerce")

master["student_teacher_ratio"] = np.where(
    (master["TEACHERS"] > 0) & (master["total_enrollment"] > 0),
    master["total_enrollment"] / master["TEACHERS"],
    np.nan,
)

master["frpl_rate"] = np.where(
    (master["total_enrollment"] > 0) & (master["frpl_total"] > 0),
    (master["frpl_total"] / master["total_enrollment"]) * 100,
    np.nan,
)


print("Step 10: Final table")

school_master = pd.DataFrame(
    {
        "ncessch": master["NCESSCH"],
        "school_name": master["SCH_NAME"],
        "district_name": master["LEA_NAME"],
        "district_id": master["LEAID"],
        "state": master["ST"],
        "level": master["LEVEL"],
        "zip_code": master["MZIP"].astype(str),
        "grade_low": master["GSLO"],
        "grade_high": master["GSHI"],
        "charter_flag": master["CHARTER_TEXT"],
        "school_type": master["SCH_TYPE_TEXT"],
        "nslp_status": master.get("nslp_status"),
        "is_virtual": master.get("is_virtual"),
        "total_enrollment": master.get("total_enrollment"),
        "student_teacher_ratio": master["student_teacher_ratio"],
        "free_lunch_n": master.get("free_lunch_n"),
        "reduced_lunch_n": master.get("reduced_lunch_n"),
        "frpl_rate": master["frpl_rate"],
        "academic_score": master["academic_score"],
        "growth_score": master["growth_score"],
        "math_score": master["math_score"],
    }
)


print("Upserting to Supabase")

records = school_master.replace([np.inf, -np.inf], np.nan)
records = records.where(pd.notnull(records), None).to_dict("records")

clean_records = []

for r in records:

    clean_row = {}

    for k, v in r.items():

        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            clean_row[k] = None
        else:
            clean_row[k] = v

    clean_records.append(clean_row)


for i in range(0, len(clean_records), 500):

    chunk = clean_records[i : i + 500]

    supabase.table("school_master").upsert(
        chunk,
        on_conflict="ncessch"
    ).execute()

    print("Uploaded rows", i, "to", i + len(chunk))

print("Pipeline completed")