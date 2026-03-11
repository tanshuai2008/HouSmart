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


print("Step 2: Loading Membership")

mem_df = pd.read_csv(
    os.path.join(BASE_DIR, "ccd_sch_052_2223_l_1a_083023-membership.csv"),
    low_memory=False,
    encoding="latin-1"
)

mem_df["NCESSCH"] = mem_df["NCESSCH"].astype(str).str.zfill(12)
mem_df["STUDENT_COUNT"] = pd.to_numeric(mem_df["STUDENT_COUNT"], errors="coerce")

enroll = mem_df.groupby("NCESSCH")["STUDENT_COUNT"].sum().reset_index()
enroll.columns = ["NCESSCH", "total_enrollment"]


print("Step 3: Loading Staff")

staff_df = pd.read_csv(
    os.path.join(BASE_DIR, "ccd_sch_059_2223_l_1a_083023--staff.csv"),
    low_memory=False,
    encoding="latin-1"
)

staff_df["NCESSCH"] = staff_df["NCESSCH"].astype(str).str.zfill(12)
staff_df["TEACHERS"] = pd.to_numeric(staff_df["TEACHERS"], errors="coerce")

staff_clean = staff_df[["NCESSCH", "TEACHERS"]]


print("Step 4: Loading Lunch")

lunch_df = pd.read_csv(
    os.path.join(BASE_DIR, "ccd_sch_033_2223_l_1a_083023-lunch.csv"),
    low_memory=False,
    encoding="latin-1"
)

lunch_df["NCESSCH"] = lunch_df["NCESSCH"].astype(str).str.zfill(12)
lunch_df["STUDENT_COUNT"] = pd.to_numeric(lunch_df["STUDENT_COUNT"], errors="coerce")

free = lunch_df[lunch_df["LUNCH_PROGRAM"] == "Free lunch qualified"].groupby(
    "NCESSCH"
)["STUDENT_COUNT"].sum().reset_index()

free.columns = ["NCESSCH", "free_lunch_n"]

reduced = lunch_df[
    lunch_df["LUNCH_PROGRAM"] == "Reduced-price lunch qualified"
].groupby("NCESSCH")["STUDENT_COUNT"].sum().reset_index()

reduced.columns = ["NCESSCH", "reduced_lunch_n"]

frpl = free.merge(reduced, on="NCESSCH", how="outer").fillna(0)
frpl["frpl_total"] = frpl["free_lunch_n"] + frpl["reduced_lunch_n"]


print("Step 5: Loading SEDA")

seda = pd.read_csv(
    os.path.join(BASE_DIR, "seda_school_pool_cs_6.0.csv"),
    low_memory=False
)

seda["sedasch"] = seda["sedasch"].astype(str).str.split(".").str[0].str.zfill(12)

seda_clean = seda[["sedasch", "cs_mn_avg_eb"]]
seda_clean.columns = ["NCESSCH", "academic_score"]


print("Step 6: Joining datasets")

master = dir_df.merge(enroll, on="NCESSCH", how="left")
master = master.merge(staff_clean, on="NCESSCH", how="left")
master = master.merge(frpl, on="NCESSCH", how="left")
master = master.merge(seda_clean, on="NCESSCH", how="left")


print("Step 7: Computing ratios")

master["student_teacher_ratio"] = np.where(
    (master["TEACHERS"] > 0) & (master["total_enrollment"] > 0),
    master["total_enrollment"] / master["TEACHERS"],
    None
)

master["frpl_rate"] = np.where(
    master["total_enrollment"] > 0,
    (master["frpl_total"] / master["total_enrollment"]) * 100,
    None
)


print("Step 8: Academic normalization")

state_stats = master.groupby("ST")["academic_score"].agg(["min", "max"]).reset_index()
state_stats.columns = ["ST", "state_min", "state_max"]

master = master.merge(state_stats, on="ST", how="left")

master["s_academic"] = np.where(
    (master["academic_score"].notna())
    & (master["state_max"] != master["state_min"]),
    ((master["academic_score"] - master["state_min"])
     / (master["state_max"] - master["state_min"])) * 100,
    None,
)


print("Step 9: Resource score")


def score_resource(r):

    if pd.isna(r):
        return None

    if r < 12:
        return 100

    elif r <= 25:
        return 100 - (r - 12) * 4.6

    else:
        return 40


master["s_resource"] = master["student_teacher_ratio"].apply(score_resource)


print("Step 10: Equity score")

master["s_equity"] = np.where(
    master["frpl_rate"].notna(),
    (1 - master["frpl_rate"] / 100) * 100,
    None,
)


print("Step 11: Final HouSmart score")

master["housmart_school_score"] = (
    master["s_academic"].fillna(0) * 0.6
    + master["s_resource"].fillna(0) * 0.2
    + master["s_equity"].fillna(0) * 0.2
)


print("Step 12: Preparing final table")

school_master = pd.DataFrame(
    {
        "ncessch": master["NCESSCH"],
        "school_name": master["SCH_NAME"],
        "district_name": master["LEA_NAME"],
        "district_id": master["LEAID"],
        "state": master["ST"],
        "level": master["LEVEL"],
        "zip_code": master["MZIP"].astype(str),
        "student_teacher_ratio": master["student_teacher_ratio"],
        "frpl_rate": master["frpl_rate"],
        "academic_score": master["academic_score"],
        "s_academic": master["s_academic"],
        "s_resource": master["s_resource"],
        "s_equity": master["s_equity"],
        "housmart_school_score": master["housmart_school_score"],
    }
)


print("Step 13: Cleaning NaN values")

records = school_master.to_dict("records")

clean_records = []

for row in records:

    clean_row = {}

    for k, v in row.items():

        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            clean_row[k] = None

        elif pd.isna(v):
            clean_row[k] = None

        else:
            clean_row[k] = v

    clean_records.append(clean_row)


print("Step 14: Fast Upload")

BATCH = 5000

for i in range(0, len(clean_records), BATCH):

    chunk = clean_records[i : i + BATCH]

    supabase.table("school_master").upsert(
        chunk,
        on_conflict="ncessch"
    ).execute()

    print("Uploaded rows", i, "to", i + len(chunk))


print("Step 15: Sync school_districts")

supabase.rpc("sync_school_districts").execute()


print("Step 16: Map properties to districts")

supabase.rpc("map_properties_to_districts").execute()


print("Pipeline completed successfully")