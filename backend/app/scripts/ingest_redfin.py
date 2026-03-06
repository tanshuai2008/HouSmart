import os
import sys
import tempfile
import time
import gzip

import pandas as pd
import requests

# Allow running from any directory
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from app.config.db import supabase


REDFIN_URL = (
    "https://redfin-public-data.s3.us-west-2.amazonaws.com/"
    "redfin_market_tracker/city_market_tracker.tsv000.gz"
)


# --------------------------------------------------
# STEP 1 — Download Redfin
# --------------------------------------------------
def download_redfin(url: str) -> str:
    print("⬇ Downloading Redfin dataset...")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".gz") as tmp:
        tmp_path = tmp.name

    with requests.get(url, stream=True, timeout=(15, 300)) as response:
        response.raise_for_status()

        total_size = int(response.headers.get("content-length") or 0)
        downloaded = 0

        with open(tmp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                f.write(chunk)
                downloaded += len(chunk)

                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rDownloading: {percent:.2f}%", end="")

    print("\n✅ Download Complete")
    return tmp_path


# --------------------------------------------------
# STEP 2 — Extract + Prepare Data
# --------------------------------------------------
def prepare_dataframe(gz_path: str) -> pd.DataFrame:

    print("📦 Extracting dataset...")

    with gzip.open(gz_path, "rt", encoding="utf-8") as f:
        df = pd.read_csv(f, sep="\t")

    df.columns = df.columns.str.lower()

    # The raw file contains multiple property types and other dimensions.
    # We only need a single canonical row per region.
    if "region_type" in df.columns:
        df = df[df["region_type"].astype(str).str.lower() == "place"]

    if "property_type" in df.columns:
        df = df[df["property_type"].astype(str).str.strip() == "All Residential"]

    df = df[["city", "state", "period_end", "median_sale_price"]]

    df.rename(
        columns={
            "period_end": "period",
            "median_sale_price": "median_price",
        },
        inplace=True,
    )

    df.dropna(inplace=True)

    # Normalize
    df["city"] = df["city"].astype(str).str.strip()
    df["state"] = df["state"].astype(str).str.strip()
    df["period"] = pd.to_datetime(df["period"], errors="coerce")
    df["median_price"] = pd.to_numeric(df["median_price"], errors="coerce")

    df.dropna(inplace=True)

    # --------------------------------------------------
    # Keep ONLY latest Redfin period
    # --------------------------------------------------
    latest_period = df["period"].max()

    print(f"📅 Latest period found: {latest_period.date()}")

    df = df[df["period"] == latest_period]

    df["period"] = df["period"].dt.strftime("%Y-%m-%d")
    df["median_price"] = df["median_price"].round().astype("int64")

    print(f"✅ Filtered dataset: {len(df)} cities")

    return df


# --------------------------------------------------
# STEP 3 — Upload to Supabase
# --------------------------------------------------
def upload_to_supabase(df: pd.DataFrame):

    total = len(df)

    print(f"🚀 Uploading {total} records to Supabase...")

    # Clear old data
    print("🧹 Clearing old data...")
    supabase.table("redfin_median_prices").delete().neq("id", 0).execute()

    batch_size = 500
    uploaded = 0

    for start in range(0, total, batch_size):

        batch_df = df.iloc[start:start+batch_size]

        batch = [
            {
                "city": row.city,
                "state": row.state,
                "period": row.period,
                "median_price": int(row.median_price)
            }
            for row in batch_df.itertuples(index=False)
        ]

        supabase.table("redfin_median_prices").insert(batch).execute()

        uploaded += len(batch)

        percent = (uploaded / total) * 100
        print(f"\rUploading: {percent:.2f}%", end="")

    print("\n✅ Upload Complete")


# --------------------------------------------------
# MAIN INGEST FLOW
# --------------------------------------------------
def ingest_redfin():

    gz_path = download_redfin(REDFIN_URL)

    try:
        df = prepare_dataframe(gz_path)
        upload_to_supabase(df)

    finally:
        try:
            os.remove(gz_path)
        except OSError:
            pass


if __name__ == "__main__":
    ingest_redfin()
